"""
Measurement service — reads intensity from power supply.

Supports two modes:
  • Modbus RTU/TCP  → real equipment via pymodbus
  • Simulation      → mock readings for development
"""

import asyncio
import logging
import random

from config import settings

logger = logging.getLogger(__name__)


class MeasurementService:
    """Manages the connection to the power supply and reads intensity."""

    def __init__(self):
        self._client = None
        self._connected = False

        if settings.modbus_enabled:
            self._init_modbus()
        else:
            logger.info("Modbus disabled — running in SIMULATION mode")

    # ── Modbus setup ──────────────────────────────────────────────

    def _init_modbus(self):
        """Initialise the Modbus client (RTU or TCP)."""
        try:
            if settings.modbus_method == "rtu":
                from pymodbus.client import ModbusSerialClient
                self._client = ModbusSerialClient(
                    port=settings.modbus_port,
                    baudrate=settings.modbus_baudrate,
                    timeout=3,
                )
            else:
                from pymodbus.client import ModbusTcpClient
                self._client = ModbusTcpClient(
                    host=settings.modbus_host,
                    port=settings.modbus_tcp_port,
                    timeout=3,
                )

            self._connected = self._client.connect()
            if self._connected:
                logger.info(f"Modbus connected via {settings.modbus_method}")
            else:
                logger.warning("Modbus connection failed — falling back to simulation")
        except Exception as e:
            logger.error(f"Modbus init error: {e} — falling back to simulation")
            self._connected = False

    # ── Tension ───────────────────────────────────────────────────

    def apply_tension(self, voltage: float) -> bool:
        """Write voltage to the power supply holding register."""
        if self._connected and self._client:
            try:
                # Write voltage * 10 as integer (common Modbus convention)
                value = int(voltage * 10)
                result = self._client.write_register(
                    settings.modbus_tension_register,
                    value,
                    slave=settings.modbus_slave_id,
                )
                if result.isError():
                    logger.error(f"Modbus write error: {result}")
                    return False
                logger.info(f"Tension set to {voltage}V via Modbus")
                return True
            except Exception as e:
                logger.error(f"Modbus write exception: {e}")
                return False
        else:
            logger.info(f"[SIM] Tension set to {voltage}V")
            return True

    # ── Intensity reading ─────────────────────────────────────────

    def read_intensity(self) -> float:
        """Read current intensity from the power supply."""
        if self._connected and self._client:
            try:
                result = self._client.read_input_registers(
                    settings.modbus_intensity_register,
                    count=1,
                    slave=settings.modbus_slave_id,
                )
                if result.isError():
                    logger.error(f"Modbus read error: {result}")
                    return 0.0
                # Convert register value back (value / 100 for 2 decimal precision)
                raw = result.registers[0]
                intensity = raw / 100.0
                return round(intensity, 3)
            except Exception as e:
                logger.error(f"Modbus read exception: {e}")
                return 0.0
        else:
            return self._simulate_reading()

    # ── Simulation ────────────────────────────────────────────────

    def _simulate_reading(self) -> float:
        """Generate a realistic mock intensity reading."""
        base = (settings.default_min_intensity + settings.default_max_intensity) / 2
        jitter = (random.random() - 0.5) * 0.6
        return round(base + jitter, 3)

    # ── Cleanup ───────────────────────────────────────────────────

    def close(self):
        """Disconnect from Modbus."""
        if self._client and self._connected:
            self._client.close()
            logger.info("Modbus connection closed")


# Singleton instance
measurement_service = MeasurementService()
