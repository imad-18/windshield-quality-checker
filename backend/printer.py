"""
Zebra printer service — generates ZPL II labels and sends them via TCP.

Label content (per user spec): DATE and TIME only.
"""

import logging
import socket
from datetime import datetime

from config import settings

logger = logging.getLogger(__name__)


class ZebraPrinter:
    """Sends ZPL II commands to a Zebra printer over raw TCP (port 9100)."""

    def __init__(
        self,
        host: str = settings.printer_host,
        port: int = settings.printer_port,
        enabled: bool = settings.printer_enabled,
    ):
        self.host = host
        self.port = port
        self.enabled = enabled

    def generate_zpl(self, test_date: str, test_time: str) -> str:
        """
        Build the ZPL II label string.
        Prints only the date and time of the test.
        """
        zpl = (
            "^XA\n"                        # Start format
            "^CF0,40\n"                    # Default font, 40pt
            "^FO50,50^FD"                  # Field origin
            f"DATE: {test_date}"           # Date
            "^FS\n"                        # Field separator
            "^FO50,120^FD"                 # Field origin
            f"TIME: {test_time}"           # Time
            "^FS\n"                        # Field separator
            "^XZ\n"                        # End format
        )
        return zpl

    def print_label(self, test_date: str | None = None, test_time: str | None = None) -> bool:
        """
        Generate and send ZPL label to printer.
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
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((self.host, self.port))
                sock.sendall(zpl.encode("utf-8"))
                logger.info(f"Label printed to {self.host}:{self.port}")
                return True
        except socket.timeout:
            logger.error(f"Printer timeout: {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            logger.error(f"Printer connection refused: {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"Printer error: {e}")
            return False


# Singleton instance
zebra_printer = ZebraPrinter()
