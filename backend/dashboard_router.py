"""
Dashboard Router - Read-only API for production managers
Endpoints for viewing windshield test results without modification
"""

from datetime import datetime
from io import StringIO, BytesIO
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
import csv
import logging

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import WindshieldTest

# ── Logger ────────────────────────────────────────────
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

# ── Pydantic Schemas ──────────────────────────────────


class TestItem(BaseModel):
    """Single test record response model"""

    id: int
    tension: float
    final_intensity: float
    final_resistance: float
    result: str
    created_at: str

    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination metadata"""

    limit: int
    offset: int
    total: int
    pages: int


class TestListResponse(BaseModel):
    """Response for list of tests"""

    success: bool
    data: list[TestItem]
    pagination: PaginationInfo


class SingleTestResponse(BaseModel):
    """Response for single test"""

    success: bool
    data: TestItem


class StatsResponse(BaseModel):
    """Response for dashboard statistics"""

    success: bool
    data: dict


# ── Endpoints ─────────────────────────────────────────


@router.get("/tests", response_model=TestListResponse)
def get_tests(
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    result: str = Query(None, description="Filter by result: 'OK' or 'ERROR'"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Get all windshield tests with optional filtering and pagination

    **Query Parameters:**
    - limit: Number of records per page (1-100, default 10)
    - offset: Number of records to skip (default 0)
    - result: Filter by 'OK' or 'ERROR' (optional)
    - start_date: Filter tests from this date YYYY-MM-DD (optional)
    - end_date: Filter tests until this date YYYY-MM-DD (optional)

    **Example:**
    `/api/dashboard/tests?limit=20&offset=0&result=OK&start_date=2026-05-01&end_date=2026-05-18`
    """
    try:
        # Build base query
        query = db.query(WindshieldTest)

        # Filter by result (OK or ERROR)
        if result and result.upper() in ["OK", "ERROR"]:
            query = query.filter(WindshieldTest.result == result.upper())

        # Filter by date range
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(WindshieldTest.created_at >= start)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
                )

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                # Add 1 day to include the entire end_date
                query = query.filter(
                    WindshieldTest.created_at
                    < end.replace(hour=23, minute=59, second=59)
                )
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
                )

        # Get total count before pagination
        total = query.count()

        # Apply pagination
        tests = (
            query.order_by(WindshieldTest.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        # Calculate pages
        pages = (total + limit - 1) // limit if limit > 0 else 1

        # Convert to response model
        test_items = [
            TestItem(
                id=t.id,
                tension=t.tension,
                final_intensity=t.final_intensity,
                final_resistance=t.final_resistance,
                result=t.result,
                created_at=t.created_at.isoformat() if t.created_at else None,
            )
            for t in tests
        ]

        return TestListResponse(
            success=True,
            data=test_items,
            pagination=PaginationInfo(
                limit=limit,
                offset=offset,
                total=total,
                pages=pages,
            ),
        )

    except Exception as e:
        logger.error(f"Error fetching tests: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/tests/{test_id}", response_model=SingleTestResponse)
def get_test(test_id: int, db: Session = Depends(get_db)):
    """
    Get a single test by ID

    **Parameters:**
    - test_id: The ID of the test to retrieve

    **Example:**
    `/api/dashboard/tests/1`
    """
    try:
        test = db.query(WindshieldTest).filter(WindshieldTest.id == test_id).first()

        if not test:
            raise HTTPException(status_code=404, detail=f"Test {test_id} not found")

        return SingleTestResponse(
            success=True,
            data=TestItem(
                id=test.id,
                tension=test.tension,
                final_intensity=test.final_intensity,
                final_resistance=test.final_resistance,
                result=test.result,
                created_at=test.created_at.isoformat() if test.created_at else None,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching test {test_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/export")
def export_tests(
    result: str = Query(None, description="Filter by result: 'OK' or 'ERROR'"),
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """
    Export filtered tests as CSV

    **Query Parameters:**
    - result: Filter by 'OK' or 'ERROR' (optional)
    - start_date: Filter from date YYYY-MM-DD (optional)
    - end_date: Filter until date YYYY-MM-DD (optional)

    **Example:**
    `/api/dashboard/export?result=OK&start_date=2026-05-01&end_date=2026-05-18`

    **Returns:**
    CSV file with columns: id,tension,final_intensity,final_resistance,result,created_at
    """
    try:
        # Build query same as list endpoint
        query = db.query(WindshieldTest)

        if result and result.upper() in ["OK", "ERROR"]:
            query = query.filter(WindshieldTest.result == result.upper())

        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                query = query.filter(WindshieldTest.created_at >= start)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD"
                )

        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                query = query.filter(
                    WindshieldTest.created_at
                    < end.replace(hour=23, minute=59, second=59)
                )
            except ValueError:
                raise HTTPException(
                    status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD"
                )

        # Get all tests (no pagination for export)
        tests = query.order_by(WindshieldTest.created_at.desc()).all()

        # # Generate CSV
        # output = StringIO()
        # writer = csv.writer(output)

        # # Write header
        # writer.writerow(
        #     [
        #         "id",
        #         "tension",
        #         "final_intensity",
        #         "final_resistance",
        #         "result",
        #         "created_at",
        #     ]
        # )

        # # Write data rows
        # for test in tests:
        #     writer.writerow(
        #         [
        #             test.id,
        #             test.tension,
        #             test.final_intensity,
        #             test.final_resistance,
        #             test.result,
        #             test.created_at.isoformat() if test.created_at else "",
        #         ]
        #     )

        # # Return as downloadable file
        # csv_content = output.getvalue()
        # return {
        #     "content": csv_content,
        #     "filename": f"windshield_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        # }

    # Create an Excel workbook
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Windshield Tests"

        # Write header
        headers = [
            "ID",
            "Tension",
            "Final Intensity",
            "Final Resistance",
            "Result",
            "Created At",
        ]
        sheet.append(headers)

        # Write data rows
        for test in tests:
            sheet.append([
                test.id,
                test.tension,
                test.final_intensity,
                test.final_resistance,
                test.result,
                test.created_at.isoformat() if test.created_at else "",
            ])

        # Save workbook to a BytesIO stream
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        # Return as downloadable file
        filename = f"windshield_tests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        logger.error(f"Error exporting tests: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """
    Get dashboard statistics (summary counts and averages)

    **Returns:**
    - total_tests: Total number of tests
    - ok_count: Number of tests with OK result
    - error_count: Number of tests with ERROR result
    - ok_percentage: Percentage of OK tests
    - avg_intensity: Average final_intensity across all tests
    - last_test: Timestamp of most recent test

    **Example:**
    `/api/dashboard/stats`
    """
    try:
        # Total tests
        total_tests = db.query(WindshieldTest).count()

        if total_tests == 0:
            return StatsResponse(
                success=True,
                data={
                    "total_tests": 0,
                    "ok_count": 0,
                    "error_count": 0,
                    "ok_percentage": 0.0,
                    "avg_intensity": 0.0,
                    "last_test": None,
                },
            )

        # OK and ERROR counts
        ok_count = (
            db.query(WindshieldTest).filter(WindshieldTest.result == "OK").count()
        )
        error_count = total_tests - ok_count

        # OK percentage
        ok_percentage = (ok_count / total_tests * 100) if total_tests > 0 else 0.0

        # Average intensity
        avg_intensity = (
            db.query(WindshieldTest)
            .filter(WindshieldTest.final_intensity != None)
            .all()
        )
        avg_intensity_value = (
            sum(t.final_intensity for t in avg_intensity) / len(avg_intensity)
            if avg_intensity
            else 0.0
        )

        # Last test timestamp
        last_test = (
            db.query(WindshieldTest).order_by(WindshieldTest.created_at.desc()).first()
        )
        last_test_timestamp = (
            last_test.created_at.isoformat()
            if last_test and last_test.created_at
            else None
        )

        return StatsResponse(
            success=True,
            data={
                "total_tests": total_tests,
                "ok_count": ok_count,
                "error_count": error_count,
                "ok_percentage": round(ok_percentage, 2),
                "avg_intensity": round(avg_intensity_value, 3),
                "last_test": last_test_timestamp,
            },
        )

    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics")
