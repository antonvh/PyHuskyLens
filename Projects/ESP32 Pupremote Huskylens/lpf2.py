# LPF2 class allows communication between LEGO SPIKE Prime and third party devices.

import machine
import struct
import utime
import binascii

MAX_PKT = 32

BYTE_NACK = 0x02
BYTE_ACK = 0x04
CMD_Type = 0x40  # @, set sensor type command
CMD_Select = 0x43  #  C, sets modes on the fly
CMD_Mode = 0x49  # I, set mode type command
CMD_Baud = 0x52  # R, set the transmission baud rate
CMD_Vers = 0x5F  # _,  set the version number
CMD_ModeInfo = 0x80  # name command
CMD_Data = 0xC0  # data command
CMD_EXT_MODE = 0x6
EXT_MODE_0 = 0x00
EXT_MODE_8 = 0x08  # only used for extended mode > 7
CMD_LLL_SHIFT = 3

LENGTH_1 = 0x00

NAME, RAW, Pct, SI, SYM, FCT, FMT = 0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x80
DATA8, DATA16, DATA32, DATAF = 0, 1, 2, 3  # Data type codes
ABSOLUTE, RELATIVE, DISCRETE = 16, 8, 4
WeDo_Ultrasonic, SPIKE_Color, SPIKE_Ultrasonic = 35, 61, 62
Ev3_Utrasonic = 34

length = [1, 2, 4]
format = ["B", "H", "I", "f"]

HEARTBEAT_PERIOD = 200  # time of inactivity after which we reset sensor

def __num_bits(x):
    # Return the number of bits required to represent x
    n = 0
    while x > 0:
        x >>= 1
        n += 1
    return n


def default_cmd_callback(size, buf):
    print("received command")
    print("size=", size)
    print("len=", len(buf))
    print("data=", binascii.hexlify(buf))


class LPF2(object):
    def __init__(self, modes, sensor_id=WeDo_Ultrasonic, timer=4, freq=5, debug=False):
        self.txTimer = timer
        self.modes = modes
        self.current_mode = 0
        self.sensor_id = sensor_id
        self.connected = False
        # self.payload = bytearray([])
        self.payloads = {}
        self.freq = freq
        self.oldbuffer = bytes([])
        self.textBuffer = bytearray(b"\x00" * 32)
        self.cmd_call_back = default_cmd_callback
        self.last_nack = 0
        self.debug = debug

    @staticmethod
    def mode(
        name,
        size=1,
        data_type=DATA8,
        writable=0,
        format="3.0",
        raw=[0, 100],
        percent=[0, 100],
        SI=[0, 100],
        symbol="",
        functionmap=[ABSOLUTE, ABSOLUTE],
        view=True,
    ):
        fig, dec = format.split(".")
        functionmap = [ABSOLUTE, writable]
        total_data_size = size * 2**data_type # Byte size of data set.
        # Find the power of 2 that is greater than the length of the data
        # -1 because of the header byte. # Really?
        bit_size = __num_bits( total_data_size-1 )
        fred = [
            name,           # 0
            [size, data_type, int(fig), int(dec)], # 1
            raw,            # 2
            percent,        # 3
            SI,             # 4
            symbol,         # 5
            functionmap,    # 6
            view,           # 7
            total_data_size,# 8
            bit_size        # 9
        ]
        return fred

    def write_tx_pin(self, value, sleep=500):
        tx = machine.Pin(self.tx_pin_nr, machine.Pin.OUT)
        tx.value(value)
        utime.sleep_ms(sleep)

    def fast_uart(self):
        self.uart = machine.UART(
            self.uartchannel, baudrate=115200, rx=self.rx_pin_nr, tx=self.tx_pin_nr
        )

    def slow_uart(self):
        self.uart = machine.UART(
            self.uartChannel, baudrate=2400, rx=self.rxPin, tx=self.txPin, timeout=5
        )

    # define own call back
    def set_call_back(self, cb):
        self.cmd_call_back = cb

    # -------- Payload definition

    def load_payload(self, data, data_type = DATA8, mode = None):
        if mode is None:
            mode = self.current_mode
        if isinstance(data, list):
            # We have a list of integers. Pack them as bytes.
            bin_data = struct.pack("%d" % len(data) + format[data_type], *data)
        elif isinstance(data, float) or isinstance(data, int):
            bin_data = struct.pack(format[data_type], data)
        elif isinstance(data, str):
            # String. Convert to bytes of max size.
            bin_data = bytes(data, "UTF-8")[:MAX_PKT]
        elif isinstance(data, bytes):
            bin_data = data
        elif isinstance(data, bytearray):
            bin_data = data
        else:
            raise ValueError("Wrong data type: %s" % type(data))

        bytesize = self.modes[mode][8]
        bit = self.modes[mode][9]

        assert len(bin_data) > 0, "Payload is empty"
        assert len(bin_data) <= bytesize, "Wrong payload size"

        payload = bytearray(2**bit + 2)
        cksm = 0xFF
        payload[0] = CMD_Data | (bit << CMD_LLL_SHIFT) | mode
        cksm ^= payload[0]
        for i in range(len(bin_data)):
            payload[i+1] = bin_data[i]
            cksm ^= bin_data[i]
        payload[-1] = cksm # No need to checksum zero bytes.

        self.payloads[mode] = payload

    def send_payload(self, array, data_type = DATA8):
        self.load_payload(array, data_type)
        self.writeIt(self.payloads[self.current_mode])

    # ----- comm stuff

    def readchar(self):
        c = self.uart.read(1)
        cbyte = ord(c) if c else -1
        if self.debug:
            print("c= 0x%02X" % cbyte)
        return cbyte

    def heartbeat(self):
        if (utime.ticks_ms() - self.last_nack) > HEARTBEAT_PERIOD:
            # Reinitalize the port, have not heard from the hub in a while.
            self.last_nack = utime.ticks_ms()
            self.initialize()

        b = self.readchar()  # Read in any heartbeat or command bytes
        if b > 0:  # There is data, let's see what it is.
            if b == BYTE_NACK:
                # Regular heartbeat pulse from the hub. We have to reply with data.
                self.last_nack = utime.ticks_ms() # reset heartbeat timer

                # Now send the payload
                self.writeIt(self.payloads[self.current_mode])
                # print("payload", self.payloads[self.current_mode])

            elif b == CMD_Select:
                self.last_nack = utime.ticks_ms() # reset heartbeat timer
                # The hub is asking us to change mode.
                mode = self.readchar()
                cksm = self.readchar()
                # Calculate the checksum for two bytes.
                if cksm == 0xFF ^ CMD_Select ^ mode:
                    self.current_mode = mode

            elif b == 0x46:
                self.last_nack = utime.ticks_ms() # reset heartbeat timer
                # Data from hub to sensor should read 0x46, 0x00, 0xb9
                # print("cmd recv")
                ext_mode = self.readchar()  # 0x00 or 0x08
                cksm = self.readchar()      # 0xb9

                if cksm == 0xFF ^ 0x46 ^ ext_mode:
                    b = self.readchar()  # CMD_Data | LENGTH | MODE

                    # Bitmask and then shift to get the size exponent of the data
                    size = 2 ** ((b & 0b111000) >> 3)

                    # Bitmask to get the mode number
                    self.current_mode = (b & 0b111) + ext_mode

                    # Keep track of the checksum while reading data
                    ck = 0xFF ^ b

                    buf = bytearray(size)
                    for i in range(size):
                        buf[i] = self.readchar()
                        # Keep track of the checksum
                        ck ^= buf[i]

                    if ck == self.readchar():
                        return buf
                    else:
                        print("Checksum error")


    def writeIt(self, array):
        if self.debug:
            print(binascii.hexlify(array))
        return self.uart.write(array)

    def waitFor(self, char, timeout=2):
        starttime = utime.time()
        currenttime = starttime
        status = False
        while (currenttime - starttime) < timeout:
            utime.sleep_ms(5)
            currenttime = utime.time()
            if self.uart.any() > 0:
                data = self.uart.read(1)
                # print("received",data)
                if data == char:
                    status = True
                    break
        return status

    @staticmethod
    def calc_cksm(array):
        chksm = 0xFF
        for b in array:
            chksm ^= b
        return chksm

    def addChksm(self, array):
        return array + self.calc_cksm(array).to_bytes(1,'little')

    # -----  Init and close

    def init(self):
        self.write_tx_pin(0, 500)
        self.write_tx_pin(1, 0)
        self.slow_uart()
        self.writeIt(b"\x00")

    def close(self):
        # self.uart.deinit()
        self.send_timer.deinit()

    # ---- settup definitions

    def setType(self, sensorType):
        return self.addChksm(bytearray([CMD_Type, sensorType]))

    def defineBaud(self, baud):
        rate = baud.to_bytes(4, "little")
        return self.addChksm(bytearray([CMD_Baud]) + rate)

    def defineVers(self, hardware, software):
        hard = hardware.to_bytes(4, "big")
        soft = software.to_bytes(4, "big")
        return self.addChksm(bytearray([CMD_Vers]) + hard + soft)

    def padString(self, string, num, startNum):
        reply = bytearray(string, "UTF-8")
        reply = reply[:MAX_PKT]
        exp = __num_bits(len(reply) - 1)
        reply = reply + b"\x00" * (2**exp - len(string))
        exp = exp << 3
        return self.addChksm(bytearray([CMD_ModeInfo | exp | num, startNum]) + reply)

    def buildFunctMap(self, mode, num, Type):
        exp = 1 << CMD_LLL_SHIFT
        mapType = mode[0]
        mapOut = mode[1]
        return self.addChksm(
            bytearray([CMD_ModeInfo | exp | num, Type, mapType, mapOut])
        )

    def buildFormat(self, mode, num, Type):
        exp = 2 << CMD_LLL_SHIFT
        sampleSize = mode[0] & 0xFF
        dataType = mode[1] & 0xFF
        figures = mode[2] & 0xFF
        decimals = mode[3] & 0xFF
        return self.addChksm(
            bytearray(
                [
                    CMD_ModeInfo | exp | num,
                    Type,
                    sampleSize,
                    dataType,
                    figures,
                    decimals,
                ]
            )
        )

    def buildRange(self, settings, num, rangeType):
        exp = 3 << CMD_LLL_SHIFT
        minVal = struct.pack("<f", settings[0])
        maxVal = struct.pack("<f", settings[1])
        return self.addChksm(
            bytearray([CMD_ModeInfo | exp | num, rangeType]) + minVal + maxVal
        )

    def defineModes(self):
        length = (len(self.modes) - 1) & 0xFF
        views = 0
        for i in range(len(self.modes)):
            mode = self.modes[i]
            if mode[7]:
                views = views + 1

            # Initialize the payload for this mode

            self.load_payload(b"\x00" * mode[8], mode=i)

        views = (views - 1) & 0xFF
        return self.addChksm(bytearray([CMD_Mode, length, views]))

    def setupMode(self, mode, num):
        self.writeIt(self.padString(mode[0], num, NAME))  # write name
        self.writeIt(self.buildRange(mode[2], num, RAW))  # write RAW range
        self.writeIt(self.buildRange(mode[3], num, Pct))  # write Percent range
        self.writeIt(self.buildRange(mode[4], num, SI))  # write SI range
        self.writeIt(self.padString(mode[5], num, SYM))  # write symbol
        self.writeIt(self.buildFunctMap(mode[6], num, FCT))  # write Function Map
        self.writeIt(self.buildFormat(mode[1], num, FMT))  # write format

    # -----   Start everything up

    def initialize(self):
        self.connected = False
        # self.send_timer = machine.Timer(-1)  # default is 200 ms
        # self.period=int(1000/self.freq)
        self.init()
        self.writeIt(
            self.setType(self.sensor_id)
        )  # set sensor_id to 35 (WeDo Ultrasonic) 61 (Spike color), 62 (Spike ultrasonic)
        self.writeIt(self.defineModes())  # tell how many modes
        self.writeIt(self.defineBaud(115200))
        self.writeIt(self.defineVers(2, 2))
        num = len(self.modes) - 1
        for mode in reversed(self.modes):
            self.setupMode(mode, num)
            num -= 1
            utime.sleep_ms(5)

        self.writeIt(b"\x04")  # ACK
        # Check for ACK reply
        self.connected = self.waitFor(b"\x04")
        print("Successfully connected to hub" if self.connected else "Failed to connect to hub")
        self.last_nack = utime.ticks_ms()

        # Reset Serial to High Speed
        if self.connected:
            self.write_tx_pin(0, 10)

            # Change baudrate
            self.fast_uart()
            self.load_payload(b'\x00')

            # start callback  - MAKE SURE YOU RESTART THE CHIP EVERY TIME (CMD D) to kill previous callbacks running
            # self.send_timer.init(period=self.period, mode=machine.Timer.PERIODIC, callback= self.hubCallback)
        return


class ESP_LPF2(LPF2):
    tx_pin_nr = 19
    rx_pin_nr = 18
    uartchannel = 2

    def write_tx_pin(self, value, sleep=500):
        tx = machine.Pin(self.tx_pin_nr, machine.Pin.OUT)
        tx.value(value)
        utime.sleep_ms(sleep)

    def slow_uart(self):
        self.uart = machine.UART(
            self.uartchannel, baudrate=2400, rx=self.rx_pin_nr, tx=self.tx_pin_nr
        )

    def fast_uart(self):
        self.uart = machine.UART(
            self.uartchannel, baudrate=115200, rx=self.rx_pin_nr, tx=self.tx_pin_nr
        )


class Prime_LPF2(LPF2):
    def init(self):
        self.tx = machine.Pin(self.txPin, machine.Pin.OUT)
        self.rx = machine.Pin(self.rxPin, machine.Pin.IN)
        self.tx.value(0)
        utime.sleep_ms(500)
        self.tx.value(1)
        self.uart = machine.UART(baudrate=2400, bits=8, parity=None, stop=1)
        self.writeIt(b"\x00")


class EV3_LPF2(LPF2):
    def init(self):
        self.uart.init(baudrate=2400, bits=8, parity=None, stop=1)
        self.writeIt(b"\x00")

    def defineVers(self, hardware, software):
        return bytearray([])


class OpenMV_LPF2(LPF2):
    uartchannel = 3

    def __init__(self, modes, sensor_id=WeDo_Ultrasonic, timer=4, freq=5):
        from uos import dupterm

        dupterm(None, 2)
        super().__init__(modes, sensor_id, timer, freq)

    def write_tx_pin(self, value, sleep=500):
        from pyb import Pin

        txpin = Pin("P4", Pin.OUT_PP)
        txpin.value(value)
        utime.sleep_ms(sleep)

    def slow_uart(self):
        self.uart = machine.UART(self.uartchannel, 2400)

    def fast_uart(self):
        self.uart = machine.UART(self.uartchannel, 115200)
