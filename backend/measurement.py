"""
Measurement service — reads intensity from power supply.

Supports two modes:
  • USB/Serial  → real equipment via pyserial
  • Simulation  → mock readings for development
"""

import logging
import random
import serial
import time

from config import settings

logger = logging.getLogger(__name__)


class MeasurementService:
    """Manages the connection to the power supply and reads intensity via USB/Serial."""

    def __init__(self):
        self._serial = None
        self._connected = False

        if settings.power_supply_enabled:
            self._init_usb()
        else:
            logger.info("Power supply disabled — running in SIMULATION mode")

    # ── USB/Serial setup ──────────────────────────────────────────

    def _init_usb(self):
        """Initialize the USB/Serial connection to the power supply."""
        try:
            self._serial = serial.Serial(
                port=settings.power_supply_port,
                baudrate=settings.power_supply_baudrate,
                timeout=settings.power_supply_timeout,
            )
            self._connected = True
            logger.info(
                f"Power supply connected via USB on {settings.power_supply_port}"
            )
        except serial.SerialException as e:
            logger.error(f"USB connection error: {e} — falling back to simulation")
            self._connected = False
        except Exception as e:
            logger.error(f"USB init error: {e} — falling back to simulation")
            self._connected = False

    # ── Tension ───────────────────────────────────────────────────

    def apply_tension(self, voltage: float) -> bool:
        """Send voltage command to the power supply via USB/Serial."""
        if self._connected and self._serial:
            try:
                # Format the command with the voltage value
                cmd = settings.power_supply_tension_cmd.format(value=voltage)
                self._serial.write(cmd.encode("utf-8"))
                logger.info(f"Tension set to {voltage}V via USB")
                return True
            except serial.SerialException as e:
                logger.error(f"USB write error: {e}")
                return False
            except Exception as e:
                logger.error(f"USB write exception: {e}")
                return False
        else:
            logger.info(f"[SIM] Tension set to {voltage}V")
            return True

    # ── Intensity reading ─────────────────────────────────────────

    def read_intensity(self) -> float:
        """Read current intensity from the power supply via USB/Serial."""
        if self._connected and self._serial:
            try:
                # Send the intensity read command
                self._serial.write(settings.power_supply_intensity_cmd.encode("utf-8"))

                # Wait for and read the response
                time.sleep(settings.power_supply_response_timeout)
                response = self._serial.readline().decode("utf-8").strip()

                if response:
                    # Try to parse the response as a float
                    intensity = float(response)
                    return round(intensity, 3)
                else:
                    logger.warning("No response from power supply")
                    return 0.0
            except ValueError:
                logger.error(f"Could not parse intensity response: {response}")
                return 0.0
            except serial.SerialException as e:
                logger.error(f"USB read error: {e}")
                return 0.0
            except Exception as e:
                logger.error(f"USB read exception: {e}")
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
        """Disconnect from the power supply USB/Serial."""
        if self._serial and self._connected:
            self._serial.close()
            logger.info("Power supply USB connection closed")


# Singleton instance
measurement_service = MeasurementService()
