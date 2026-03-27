#!/usr/bin/env python3
"""
Raw Serial Monitor — Diagnostic tool to see exactly what your power supply sends.

This tool displays raw data from the serial port so you can understand
the actual protocol and data format your power supply uses.
"""

import sys
import serial
import time
from datetime import datetime

from config import settings


def list_serial_ports():
    """List available COM ports."""
    import serial.tools.list_ports

    print("\nAvailable COM ports:")
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("  No ports found")
        return []

    for port in ports:
        print(f"  {port.device} - {port.description}")
    return [p.device for p in ports]


def monitor_raw_serial(port=None, baudrate=9600, timeout=1):
    """Monitor raw serial data from power supply."""

    if port is None:
        port = settings.power_supply_port
    if baudrate is None:
        baudrate = settings.power_supply_baudrate

    print("\n" + "=" * 80)
    print("  RAW SERIAL MONITOR - Power Supply Data Inspection")
    print("=" * 80)
    print(f"Port: {port} | Baudrate: {baudrate}")
    print("-" * 80)
    print("Listening for data from power supply...")
    print("Press Ctrl+C to stop")
    print("-" * 80 + "\n")

    try:
        ser = serial.Serial(port, baudrate, timeout=timeout)
        print(f"✓ Connected to {port}\n")

        time.sleep(1)

        last_activity = time.time()
        buffer = b""

        voltage = None
        current = None

        while True:
            # ✅ Request voltage
            ser.write(b"VOUT1?\n")
            time.sleep(0.2)

            # ✅ Request current
            ser.write(b"IOUT1?\n")
            time.sleep(0.2)

            # Read available data
            while ser.in_waiting > 0:
                data = ser.read(ser.in_waiting)
                buffer += data

                # Process full lines
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)

                    decoded = line.decode("utf-8", errors="replace").strip()

                    # 🎯 Detect if it's voltage or current
                    if decoded.replace('.', '', 1).replace('-', '', 1).isdigit():
                        value = float(decoded)

                        # Heuristic: voltage usually > 1, current small
                        if value > 1:
                            voltage = value
                        else:
                            current = value

            # ✅ Display only when we have both values
            if voltage is not None and current is not None:
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] Voltage: {voltage:.2f} V | Current: {current:.2f} A")

                # reset for next cycle
                voltage = None
                current = None

            # Safety: no data warning
            if time.time() - last_activity > 5:
                print("⚠ Waiting for data...")
                last_activity = time.time()

                time.sleep(0.5)
            else:
                # Show a message if no data for 5 seconds
                if time.time() - last_activity > 5 and byte_count == 0:
                    print("\n⚠ No data received. Possible issues:")
                    print("  1. Power supply is not connected to this COM port")
                    print("  2. Power supply is turned off")
                    print("  3. USB cable is not properly connected")
                    print("  4. Baudrate is incorrect")
                    print("\nTry these alternatives:")
                    print("  • python raw_serial_monitor.py COM4")
                    print("  • python raw_serial_monitor.py COM3 19200")
                    print(
                        "  • List available ports: python raw_serial_monitor.py --list"
                    )
                    last_activity = time.time()

                time.sleep(0.01)

    except serial.SerialException as e:
        print(f"\n✗ Connection Error: {e}")
        print(f"\nThe port '{port}' could not be opened. Available ports:")
        list_serial_ports()
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n\n{'=' * 80}")
        print(f"Monitor stopped. Total bytes received: {byte_count}")
        print("=" * 80 + "\n")
        ser.close()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Handle command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_serial_ports()
            sys.exit(0)

        port = sys.argv[1]
        baudrate = settings.power_supply_baudrate

        if len(sys.argv) > 2:
            try:
                baudrate = int(sys.argv[2])
            except ValueError:
                print(f"Invalid baudrate: {sys.argv[2]}")
                sys.exit(1)

        monitor_raw_serial(port=port, baudrate=baudrate)
    else:
        monitor_raw_serial()
