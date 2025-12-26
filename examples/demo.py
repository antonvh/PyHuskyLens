"""
PyHuskyLens Demo Examples
Demonstrates usage for different platforms: ESP32 (I2C), EV3 Pybricks, SPIKE/Inventor
"""

from pyhuskylens import (
    HuskyLensI2C,
    HuskyLensSerial,
    ALGORITHM_OBJECT_RECOGNITION,
    ALGORITHM_LINE_TRACKING,
    COLOR_GREEN,
)

# Demo constants - change these to test different interfaces
_EV3_PYBRICKS_SERIAL = 0
_INVENTOR_SERIAL = 1
_ESP32_I2C = 3
_MAIN_DEMO_TYPE = _ESP32_I2C  # Change this to test different interfaces


def demo_esp32_i2c():
    """Demo for ESP32 with I2C interface."""
    from machine import Pin, SoftI2C
    from time import sleep_ms

    print("=" * 60)
    print("HuskyLens Demo - I2C and Serial")
    print("=" * 60)

    # I2C Example
    print("\n--- I2C Example ---")
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
    hl_i2c = HuskyLensI2C(i2c, debug=True)

    if not hl_i2c.version:
        print("X No HuskyLens found on I2C, scl=Pin(22), sda=Pin(21)")
        devices = i2c.scan()
        print("I2C devices: " + str([hex(d) for d in devices]))
    else:
        print("V Found HuskyLens V" + str(hl_i2c.version) + " on I2C\n")

        # Test connection
        print("Testing connection...")
        if hl_i2c.knock():
            print("V I2C Connected!")

            # Get version (V1 only)
            if hl_i2c.version == 1:
                version = hl_i2c.get_version()
                if version:
                    print("V Firmware: " + str(version))

            # Draw text
            print("\nDrawing text...")
            hl_i2c.set_alg(0)
            hl_i2c.show_text("Hello!", position=(50, 50), color=COLOR_GREEN)
            print("V Text demo complete")

            # Set algorithm and get blocks
            print("\nSetting algorithm to Object Recognition...")
            hl_i2c.set_alg(ALGORITHM_OBJECT_RECOGNITION)
            sleep_ms(2000)
            print("Getting blocks...")
            for i in range(20):
                blocks = hl_i2c.get_blocks()
                print("V Found " + str(len(blocks)) + " blocks")
                for block in blocks:
                    print("  " + str(block))
        else:
            print("X Connection failed!")


def demo_ev3_pybricks_serial():
    """Demo for EV3 with Pybricks Serial interface."""
    from time import sleep_ms
    from pybricks.iodevices import UARTDevice
    from pybricks.parameters import Port

    print("\n--- Serial Example EV3dev Pybricks ---")
    uart = UARTDevice(Port.A, 9600)

    hl_serial = HuskyLensSerial(uart, debug=True)

    if hl_serial.version:
        print("V Found HuskyLens V" + str(hl_serial.version) + " on Serial\n")

        if hl_serial.knock():
            print("V Serial Connected!")

            # Get arrows
            hl_serial.set_alg(ALGORITHM_LINE_TRACKING)
            arrows = hl_serial.get_arrows()
            print("V Found " + str(len(arrows)) + " arrows")
            for arrow in arrows:
                print("  " + str(arrow))
    else:
        print("X No HuskyLens on Serial")


def demo_inventor_serial():
    """Demo for LEGO Inventor and SPIKE with Serial interface."""
    from time import sleep_ms
    from hub import port

    print("\n--- Serial Example LEGO Inventor and SPIKE LEGACY ---")
    uart = port.A
    uart.mode(1)
    sleep_ms(300)
    uart.baud(9600)
    # Put voltage on M+ or M- leads
    uart.pwm(100)
    sleep_ms(2200)  # Give the huskylens some time to boot
    sleep_ms(300)
    uart.read(32)

    hl_serial = HuskyLensSerial(uart, debug=True)

    if hl_serial.version:
        print("V Found HuskyLens V" + str(hl_serial.version) + " on Serial\n")

        if hl_serial.knock():
            print("V Serial Connected!")

            # Get arrows
            hl_serial.set_alg(ALGORITHM_LINE_TRACKING)
            arrows = hl_serial.get_arrows()
            print("V Found " + str(len(arrows)) + " arrows")
            for arrow in arrows:
                print("  " + str(arrow))
    else:
        print("X No HuskyLens on Serial")


if __name__ == "__main__":
    if _MAIN_DEMO_TYPE == _ESP32_I2C:
        demo_esp32_i2c()
    elif _MAIN_DEMO_TYPE == _EV3_PYBRICKS_SERIAL:
        demo_ev3_pybricks_serial()
    elif _MAIN_DEMO_TYPE == _INVENTOR_SERIAL:
        demo_inventor_serial()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
