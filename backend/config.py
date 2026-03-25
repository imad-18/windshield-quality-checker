from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # ── Database ──
    db_url: str = "mysql+pymysql://root:password@localhost:3306/windshield_db"

    # ── Modbus (Power Supply) ──
    modbus_enabled: bool = False
    modbus_method: str = "rtu"  # "rtu" or "tcp"
    modbus_port: str = "COM3"  # Serial port for RTU
    modbus_host: str = "192.168.1.100"  # IP for Modbus TCP
    modbus_tcp_port: int = 502
    modbus_baudrate: int = 9600
    modbus_slave_id: int = 1
    modbus_tension_register: int = 0  # Holding register address for tension
    modbus_intensity_register: int = 1  # Input register address for intensity

    # ── Zebra Printer ──
    printer_enabled: bool = True
    printer_port: str = "COM4"  # Serial port (e.g., "COM4") or IP address
    printer_tcp_port: int = 9100  # TCP port for network printers

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
