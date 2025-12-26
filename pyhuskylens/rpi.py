"""
HuskyLens Raspberry Pi Drivers
Raspberry Pi-specific drivers using smbus2 (I2C) and pyserial (Serial/UART)
"""

from .pyhuskylens import (
    HuskyLensBase,
    _I2C_ADDR_V1,
    _I2C_ADDR_V2,
    _DELAY_SERIAL_READ,
    sleep_ms,
)


class HuskyLensI2C_RPi(HuskyLensBase):
    """HuskyLens I2C driver for Raspberry Pi using smbus2."""

    def __init__(self, bus=1, address=None, debug=False):
        """Initialize Raspberry Pi I2C.

        Args:
            bus: I2C bus number (default 1 for /dev/i2c-1)
            address: I2C address (auto-detected if None)
            debug: Enable debug output
        """
        super().__init__(debug)
        try:
            import smbus2

            self.bus = smbus2.SMBus(bus)
        except ImportError:
            raise ImportError(
                "smbus2 required for Raspberry Pi I2C. Install: pip install smbus2"
            )

        self.address = address
        self.use_register = False
        self._detect_version()

    def _detect_version(self):
        """Detect HuskyLens version by scanning I2C addresses."""
        # Try to read from known addresses
        for addr in [_I2C_ADDR_V1, _I2C_ADDR_V2]:
            try:
                # Attempt a test read
                if addr == _I2C_ADDR_V1:
                    self.bus.read_byte_data(addr, 0x0C)
                    self.version = 1
                    self.address = addr
                    if self.debug:
                        print("HuskyLens V1 @ 0x%02x" % addr)
                    return
                else:
                    self.bus.read_byte(addr)
                    self.version = 2
                    self.address = addr
                    if self.debug:
                        print("HuskyLens V2 @ 0x%02x" % addr)
                    return
            except:
                continue

        self.version = None
        if self.debug:
            print("No HuskyLens found on I2C")

    def _transport_write(self, data):
        """Write data to I2C bus."""
        if self.version == 1:
            # V1: Write to register 0x0C
            self.bus.write_i2c_block_data(self.address, 0x0C, list(data))
        else:
            # V2: Direct write
            self.bus.write_i2c_block_data(self.address, data[0], list(data[1:]))

    def _transport_read(self, size):
        """Read data from I2C bus."""
        if self.version == 1:
            # V1: Read from register 0x0C
            return bytes(self.bus.read_i2c_block_data(self.address, 0x0C, size))
        else:
            # V2: Direct read
            return bytes(self.bus.read_i2c_block_data(self.address, 0, size))

    def _transport_flush(self):
        """Flush I2C buffer (V2 only)."""
        if self.version == 2:
            for _ in range(5):
                try:
                    self.bus.read_i2c_block_data(self.address, 0, 16)
                except:
                    break


class HuskyLensSerial_RPi(HuskyLensBase):
    """HuskyLens Serial/UART driver for Raspberry Pi using pyserial."""

    def __init__(self, port="/dev/ttyUSB0", baud=9600, debug=False):
        """Initialize Raspberry Pi Serial.

        Args:
            port: Serial port path (e.g., '/dev/ttyUSB0', '/dev/ttyAMA0')
            baud: Baud rate (default 9600)
            debug: Enable debug output
        """
        super().__init__(debug)
        try:
            import serial

            self.uart = serial.Serial(port, baud, timeout=0.1)
        except ImportError:
            raise ImportError(
                "pyserial required for Raspberry Pi Serial. Install: pip install pyserial"
            )
        except Exception as e:
            raise Exception("Failed to open serial port %s: %s" % (port, str(e)))

        self._detect_version()

    def _detect_version(self):
        """Detect HuskyLens version by trying knock commands."""
        # Try V2 first
        self.version = 2
        if self.knock():
            if self.debug:
                print("HuskyLens V2 (Serial)")
            return
        # Try V1
        self.version = 1
        if self.knock():
            if self.debug:
                print("HuskyLens V1 (Serial)")
            return
        self.version = None
        if self.debug:
            print("No HuskyLens on Serial")

    def _transport_write(self, data):
        """Write data to serial port."""
        self.uart.write(data)

    def _transport_read(self, size):
        """Read data from serial port."""
        data = bytearray()
        for _ in range(150):
            if self.uart.in_waiting:
                chunk = self.uart.read(1)
                if chunk:
                    data.extend(chunk)
            if len(data) >= size:
                return bytes(data[:size])
            sleep_ms(_DELAY_SERIAL_READ)
        return bytes(data)

    def _transport_flush(self):
        """Flush serial buffer."""
        try:
            self.uart.reset_input_buffer()
        except Exception as e:
            if self.debug:
                print("Flush error: " + str(e))
