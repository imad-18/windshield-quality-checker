"""
Zebra printer service — generates ZPL II labels and sends them via USB/Serial.

Label content (per user spec): DATE and TIME only.
"""

import logging
import serial
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class ZebraPrinter:
    """Sends ZPL II commands to a Zebra printer over USB/Serial."""

    def __init__(
        self,
        port: str = settings.printer_port,   # COMx on Windows, /dev/ttyUSBx on Linux
        baudrate: int = getattr(settings, "printer_baudrate", 9600),
        enabled: bool = settings.printer_enabled,
    ):
        self.port = port
        self.baudrate = baudrate
        self.enabled = enabled

    def generate_zpl(self, test_date: str, test_time: str) -> str:
        """
        Build the ZPL II label string.
        Prints only the date and time of the test.
        """
        zpl = (
            "^XA\n"
            "^CF0,40\n"
            "^FO50,50^FD"
            f"DATE: {test_date}"
            "^FS\n"
            "^FO50,120^FD"
            f"TIME: {test_time}"
            "^FS\n"
            "^XZ\n"
        )
        return zpl

    def print_label(self, test_date: str | None = None, test_time: str | None = None) -> bool:
        """
        Generate and send ZPL label to printer via USB/Serial.
        If no date/time provided, uses current datetime.
        Returns True on success.
        """
        now = datetime.now()
        date_str = test_date or now.strftime("%d/%m/%Y")
        time_str = test_time or now.strftime("%H:%M:%S")

        zpl = self.generate_zpl(date_str, time_str)

        if not self.enabled:
            logger.info(f"[PRINTER SIM] Would print label:\n{zpl}")
            return True

        try:
            with serial.Serial(self.port, self.baudrate, timeout=2) as ser:
                ser.write(zpl.encode("utf-8"))
                logger.info(f"Label printed to USB port {self.port}")
                return True
        except serial.SerialException as e:
            logger.error(f"Printer serial error: {e}")
            return False
        except Exception as e:
            logger.error(f"Printer error: {e}")
            return False


# Singleton instance
zebra_printer = ZebraPrinter()
