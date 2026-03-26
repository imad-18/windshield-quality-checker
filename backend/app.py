"""
FastAPI application — REST API + WebSocket for windshield quality testing.

REST endpoints for test management.
WebSocket for real-time intensity streaming during measurement.
"""

import asyncio
import logging
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import init_db, get_db
from models import WindshieldTest
from measurement import measurement_service
from evaluation import evaluation_service
from printer import zebra_printer

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Windshield Tester API",
    description="Power supply traceability — windshield quality control",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Startup / Shutdown ────────────────────────────────────────────
@app.on_event("startup")
def on_startup():
    logger.info("Initialising database …")
    init_db()
    logger.info("Database ready")
    logger.info(f"Power Supply: {'ENABLED' if settings.power_supply_enabled else 'SIMULATION'}")
    logger.info(f"Printer: {'ENABLED' if settings.printer_enabled else 'SIMULATION'}")


@app.on_event("shutdown")
def on_shutdown():
    measurement_service.close()
    logger.info("Shutdown complete")


# ── Request / Response Models ─────────────────────────────────────
class TestStartRequest(BaseModel):
    model: str = "VS20"
    tension: float = settings.default_tension
    min_intensity: float = settings.default_min_intensity
    max_intensity: float = settings.default_max_intensity
    cycle_time: int = settings.default_cycle_time


class TestResponse(BaseModel):
    id: int
    tension: float
    final_intensity: float
    final_resistance: float
    result: str
    created_at: str


# ── REST Endpoints ────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "modbus": "connected" if settings.modbus_enabled else "simulation",
        "printer": "connected" if settings.printer_enabled else "simulation",
    }


@app.get("/api/tests", response_model=list[TestResponse])
def list_tests(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """List all test records, most recent first."""
    tests = (
        db.query(WindshieldTest)
        .order_by(WindshieldTest.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        TestResponse(
            id=t.id,
            tension=t.tension,
            final_intensity=t.final_intensity,
            final_resistance=t.final_resistance,
            result=t.result,
            created_at=t.created_at.isoformat() if t.created_at else "",
        )
        for t in tests
    ]


@app.get("/api/test/{test_id}", response_model=TestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """Get a single test result by ID."""
    t = db.query(WindshieldTest).filter(WindshieldTest.id == test_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Test not found")
    return TestResponse(
        id=t.id,
        tension=t.tension,
        final_intensity=t.final_intensity,
        final_resistance=t.final_resistance,
        result=t.result,
        created_at=t.created_at.isoformat() if t.created_at else "",
    )


@app.get("/api/config")
def get_config():
    """Return current measurement configuration."""
    return {
        "default_tension": settings.default_tension,
        "default_min_intensity": settings.default_min_intensity,
        "default_max_intensity": settings.default_max_intensity,
        "default_cycle_time": settings.default_cycle_time,
        "reading_interval_ms": settings.reading_interval_ms,
        "modbus_enabled": settings.modbus_enabled,
        "printer_enabled": settings.printer_enabled,
    }


# ── WebSocket — Real-time Test ────────────────────────────────────
@app.websocket("/ws/test")
async def ws_test(websocket: WebSocket):
    """
    WebSocket endpoint for running a full test cycle.

    Client sends a JSON start message:
        { "action": "start", "model": "VS20", "tension": 20.0,
          "min_intensity": 0.87, "max_intensity": 1.26, "cycle_time": 30 }

    Server streams readings, then sends evaluation result.
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        # Wait for start command from Angular
        data = await websocket.receive_json()

        if data.get("action") != "start":
            await websocket.send_json({"error": "Send {action: 'start'} to begin"})
            await websocket.close()
            return

        tension = data.get("tension", settings.default_tension)
        min_i = data.get("min_intensity", settings.default_min_intensity)
        max_i = data.get("max_intensity", settings.default_max_intensity)
        cycle_time = data.get("cycle_time", settings.default_cycle_time)
        model = data.get("model", "VS20")

        interval_s = settings.reading_interval_ms / 1000.0
        expected_readings = int(cycle_time / interval_s)

        # ── Phase: Detecting ──
        await websocket.send_json({"phase": "detecting"})
        await asyncio.sleep(1.0)

        # ── Phase: Apply Tension ──
        measurement_service.apply_tension(tension)
        await websocket.send_json({"phase": "measuring"})

        # ── Phase: Measurement Loop ──
        readings: list[float] = []
        for i in range(expected_readings):
            intensity = measurement_service.read_intensity()
            resistance = round(tension / intensity, 2) if intensity > 0 else 0.0
            readings.append(intensity)

            await websocket.send_json({
                "phase": "measuring",
                "reading": {
                    "index": i + 1,
                    "total": expected_readings,
                    "intensity": intensity,
                    "resistance": resistance,
                    "progress": round(((i + 1) / expected_readings) * 100, 1),
                },
            })

            await asyncio.sleep(interval_s)

        # ── Phase: Evaluating ──
        await websocket.send_json({"phase": "evaluating"})

        result = evaluation_service.evaluate(readings, tension, min_i, max_i)

        # ── Store in MySQL ──
        db = next(get_db())
        try:
            record = WindshieldTest(
                tension=tension,
                final_intensity=result.final_intensity,
                final_resistance=result.final_resistance,
                result="OK" if result.passed else "ERROR",
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            test_id = record.id
            created_at = record.created_at
        finally:
            db.close()

        # ── Print label if OK ──
        printed = False
        if result.passed:
            now = created_at or datetime.now()
            printed = zebra_printer.print_label(
                test_date=now.strftime("%d/%m/%Y"),
                test_time=now.strftime("%H:%M:%S"),
            )

        # ── Phase: Complete ──
        await websocket.send_json({
            "phase": "complete",
            "result": {
                "test_id": test_id,
                "passed": result.passed,
                "status": "OK" if result.passed else "ERROR",
                "final_intensity": result.final_intensity,
                "final_resistance": result.final_resistance,
                "readings_count": result.readings_count,
                "is_stable": result.is_stable,
                "printed": printed,
                "created_at": created_at.isoformat() if created_at else None,
            },
        })

        logger.info(f"Test #{test_id} complete: {'OK' if result.passed else 'ERROR'}")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass


# ── Entry point ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
