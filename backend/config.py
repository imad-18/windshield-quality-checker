from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # ── Database ──
    db_url: str = "mysql+pymysql://root:password@localhost:3306/windshield_db"

    # ── Power Supply (USB/Serial) ──
    power_supply_enabled: bool = True
    power_supply_type: str = "usb"  # "usb" | "serial"
    power_supply_port: str = "COM3"  # Serial port (e.g., "COM3") or USB port
    power_supply_baudrate: int = 9600
    power_supply_timeout: float = 2.0  # seconds
    power_supply_tension_cmd: str = "VOLT:{value}\n"  # Command template for setting tension
    power_supply_intensity_cmd: str = "INTENSITY\n"  # Command to read intensity
    power_supply_response_timeout: float = 0.5  # seconds to wait for response

    # ── Zebra Printer ──
    printer_enabled: bool = True
    printer_type: str = "usb"  # "usb" | "serial"
    printer_name: str = "ZDesigner ZD621-203dpi ZPL"

    printer_port: str = "COM5"  # Serial port (e.g., "COM4")
    printer_baudrate: int = 9600
    printer_timeout: float = 2.0  # seconds

    # ── Measurement ──
    default_tension: float = 20.0
    default_min_intensity: float = 0.87
    default_max_intensity: float = 1.26
    default_cycle_time: int = 30  # seconds
    reading_interval_ms: int = 200  # ms between readings
    stabilization_window: int = 10  # last N readings to check
    stabilization_threshold: float = 0.05  # max std deviation for "stable"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
