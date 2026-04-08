import win32print
import serial
from config import Settings

settings = Settings()


def send_zpl_usb(zpl: str) -> bool:
    try:
        printer_name = settings.printer_name

        hPrinter = win32print.OpenPrinter(printer_name)
        try:
            win32print.StartDocPrinter(hPrinter, 1, ("ZPL Label", None, "RAW"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, zpl.encode())
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)

        return True
    except Exception as e:
        print(f"[PRINTER][USB ERROR] {e}")
        return False


def send_zpl_serial(zpl: str) -> bool:
    try:
        ser = serial.Serial(
            port=settings.printer_port,
            baudrate=settings.printer_baudrate,
            timeout=settings.printer_timeout,
        )
        ser.write(zpl.encode())
        ser.close()
        return True
    except Exception as e:
        print(f"[PRINTER][SERIAL ERROR] {e}")
        return False


def print_label(test_date: str, test_time: str) -> bool:
    if not settings.printer_enabled:
        return False

    # 👉 Clean ZPL (with fixes we discussed)
    zpl = f"""
^XA
^PW800
^FO250,100^A0N,50,50^FD {test_date}^FS
^FO250,180^A0N,50,50^FD {test_time}^FS
^XZ
"""

    if settings.printer_type == "usb":
        return send_zpl_usb(zpl)

    elif settings.printer_type == "serial":
        return send_zpl_serial(zpl)

    else:
        print("[PRINTER] Unsupported printer type")
        return False