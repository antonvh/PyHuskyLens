import struct
import time
from micropython import const
from math import atan2, degrees


def byte(num):
    # Convert an in int to a byte. Supposing it is < 255
    return bytes([num])


HEADER = b"\x55\xaa\x11"
FAILED = b""

EV3PYBRICKS = const(0)
INVENTOR = const(1)
ESP32I2C = const(3)
OPENMV = const(4)

(
    REQUEST,  # 0x20 = 32 etc....
    REQUEST_BLOCKS,
    REQUEST_ARROWS,
    REQUEST_LEARNED,
    REQUEST_BLOCKS_LEARNED,
    REQUEST_ARROWS_LEARNED,
    REQUEST_BY_ID,
    REQUEST_BLOCKS_BY_ID,
    REQUEST_ARROWS_BY_ID,
    RETURN_INFO,
    RETURN_BLOCK,
    RETURN_ARROW,
    REQUEST_KNOCK,
    REQUEST_ALGORITHM,
    RETURN_OK,
    REQUEST_CUSTOMNAMES,
    REQUEST_PHOTO,
    REQUEST_SEND_PHOTO,
    REQUEST_SEND_KNOWLEDGES,
    REQUEST_RECEIVE_KNOWLEDGES,
    REQUEST_CUSTOM_TEXT,
    REQUEST_CLEAR_TEXT,
    REQUEST_LEARN,
    REQUEST_FORGET,
    REQUEST_SEND_SCREENSHOT,
    REQUEST_SAVE_SCREENSHOT,
    REQUEST_LOAD_AI_FRAME_FROM_USB,
    REQUEST_IS_PRO,
    REQUEST_FIRMWARE_VERSION,
    RETURN_BUSY,
) = [byte(x) for x in range(0x20, 0x3E)]
RETURN_IS_PRO = REQUEST_IS_PRO


ALGORITHM_FACE_RECOGNITION = const(0)
ALGORITHM_OBJECT_TRACKING = const(1)
ALGORITHM_OBJECT_RECOGNITION = const(2)
ALGORITHM_LINE_TRACKING = const(3)
ALGORITHM_COLOR_RECOGNITION = const(4)
ALGORITHM_TAG_RECOGNITION = const(5)
ALGORITHM_OBJECT_CLASSIFICATION = const(6)
ALGORITHM_QR_CODE_RECOGNITION = const(7)
ALGORITHM_BARCODE_RECOGNITION = const(8)

ARROWS = const(1)
BLOCKS = const(2)
FRAME = const(3)


class Arrow:
    def __init__(self, x_tail, y_tail, x_head, y_head, ID):
        self.x_tail = x_tail
        self.y_tail = y_tail
        self.x_head = x_head
        self.y_head = y_head
        self.ID = ID
        self.learned = True if ID > 0 else False
        self.direction = degrees(
            atan2(x_tail - x_head, y_tail - y_head)
        )  # Forward(up) = 0, left = 90
        self.type = "ARROW"

    def __repr__(self):
        return "ARROW - x tail:{}, y tail:{}, x head:{}, y head:{}, direction: {}, ID:{}".format(
            self.x_tail, self.y_tail, self.x_head, self.y_head, self.direction, self.ID
        )

    def to_bytes(self):
        return struct.pack(
            "5hB",
            self.x_tail,
            self.y_tail,
            self.x_head,
            self.y_head,
            self.direction,
            self.ID,
        )


class Block:
    def __init__(self, x, y, width, height, ID):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.ID = ID
        self.learned = True if ID > 0 else False
        self.type = "BLOCK"

    def __repr__(self):
        return "BLOCK - x:{}, y:{}, width:{}, height:{}, ID:{}".format(
            self.x, self.y, self.width, self.height, self.ID
        )

    def to_bytes(self):
        return struct.pack("4hB", self.x, self.y, self.width, self.height, self.ID)


class HuskyLens:
    def __init__(self, hl_port, baud=9600, debug=False, pwm=0, power=False):
        """Instantiatiates a huskylens object for communication with a HuskyLens.

        Args:
            hl_port (str, pybricks Port object or i2c object): The port to which you connected the HL
            baud (int, optional): Baud rate for serial mode. Defaults to 9600.
            debug (bool, optional): Print debug info. Defaults to False.
            pwm (int, optional): Voltage % output on SPIKE hub. Defaults to 0.
            power (bool, optional): Alternative way to enable power - by setting True. Defaults to False.
        """
        self.debug = debug
        port_dir = dir(hl_port)
        if "split" in port_dir:
            from hub import port

            # A string. We're on SPIKE/Robot Inventor
            self.uart = eval("port." + hl_port)
            self.uart.mode(1)
            time.sleep_ms(300)
            self.uart.baud(baud)
            # Put voltage on M+ or M- leads
            if power:
                pwm = 100
            if pwm:
                self.uart.pwm(pwm)
                time.sleep_ms(2200)  # Give the huskylens some time to boot
            time.sleep_ms(300)
            self.uart.read(32)
            self.next_write = time.ticks_ms()
            self.mode = INVENTOR
        elif "A" in port_dir:
            # We're probably on ev3dev/pybricks
            from pybricks.iodevices import UARTDevice

            self.uart = UARTDevice(hl_port, baud)
            self.mode = EV3PYBRICKS
        elif "readfrom" in port_dir:
            self.mode = ESP32I2C
            self.i2c = hl_port

    @staticmethod
    def calc_checksum(data):
        return byte(sum(bytearray(data)) & 0xFF)

    def write_cmd(self, command, payload=b""):
        length = byte(len(payload))
        data = HEADER + length + command + payload
        data += self.calc_checksum(data)

        if self.mode == INVENTOR or self.mode == EV3PYBRICKS:
            self.uart.write(data)
        elif self.mode == ESP32I2C:
            try:
                self.i2c.writeto_mem(50, 12, data)
            except Exception as e:  # Probably ENoDevice
                if self.debug:
                    print(e)
                return

        if self.debug:
            print("Sent: ", data)
        else:
            # Throttle a bit
            time.sleep_ms(5)

    def force_read(self, size=1, max_tries=150, search=b""):
        data = b""
        if search != b"":
            size = len(search)
        if self.mode == EV3PYBRICKS:
            n = 0
            while 1:
                n += 1
                if self.uart.waiting():
                    r = self.uart.read(1)
                    data += r
                if len(data) == size or n > max_tries:
                    if self.debug:
                        print("break n", n)
                    break
        elif self.mode == INVENTOR:
            r = self.uart.read(size)
            if self.debug:
                print(r)
            for i in range(max_tries):
                if r == None:  # On SPIKE b'' is returned, on OpenMV None
                    r = b""
                data += r

                if len(data) == size:
                    return data
                elif search:
                    if len(data) >= len(search):
                        if data[-len(search) :] == search:
                            return search

                time.sleep_ms(1)
                r = self.uart.read(1)

                if i > 3 and self.debug:
                    print("Waiting for data in force read. Tries:", i)

        elif self.mode == ESP32I2C:
            try:
                data = self.i2c.readfrom(50, size)
            except Exception as e:  # Probably ENODevice
                data = b""
                if self.debug:
                    print(e)

        return data

    def read_cmd(self):
        payload = b""
        r = self.force_read(search=HEADER)
        if r != HEADER:
            if self.debug:
                print("No answer from huskylens")
            return FAILED, "No header"
        length = self.force_read(1)
        command = self.force_read(1)
        if length[0] > 0:
            payload = self.force_read(length[0])
        checksum = self.force_read(1)
        if checksum != self.calc_checksum(HEADER + length + command + payload):
            if self.debug:
                print(
                    "Checksum failed",
                    checksum,
                    self.calc_checksum(HEADER + length + command + payload),
                )
            return FAILED, "Bad checksum"
        return command, payload

    def check_ok(self, timeout=1):
        result = False
        for i in range(timeout):
            answer_cmd, answer_params = self.read_cmd()
            if answer_cmd == RETURN_OK:
                result = True
                break
            elif self.debug:
                print("Try ", i, ". Expected OK, but got:", answer_cmd, answer_params)
            time.sleep_ms(1)

        return result

    def knock(self):
        self.write_cmd(REQUEST_KNOCK)
        return self.check_ok()

    def set_alg(self, algorithm):
        self.write_cmd(REQUEST_ALGORITHM, payload=struct.pack("h", algorithm))
        return self.check_ok(timeout=40)

    def process_info(self):
        blocks = []
        arrows = []
        ret, info = self.read_cmd()
        if ret != RETURN_INFO:
            if self.debug:
                print("Expected info")
            return {}

        try:
            n_blocks_arrows, n_ids, frame, _, _ = struct.unpack("hhhhh", info)
        except:
            n_blocks_arrows, n_ids, frame = (0, 0, 0)
        if self.debug:
            print(n_blocks_arrows, n_ids, frame)

        for i in range(n_blocks_arrows):
            obj_type, data = self.read_cmd()
            if obj_type == RETURN_BLOCK:
                blocks += [Block(*struct.unpack("hhhhh", data))]
            elif obj_type == RETURN_ARROW:
                arrows += [Arrow(*struct.unpack("hhhhh", data))]
            else:
                if self.debug:
                    print("Expected blocks or arrows")

        return {BLOCKS: blocks, ARROWS: arrows, FRAME: frame}

    def get_blocks(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_BLOCKS_BY_ID, struct.pack("h", ID))
        elif learned:
            self.write_cmd(REQUEST_BLOCKS_LEARNED)
        else:
            self.write_cmd(REQUEST_BLOCKS)
        result = self.process_info()
        if BLOCKS in result:
            return result[BLOCKS]
        else:
            return []

    def get_arrows(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_ARROWS_BY_ID, struct.pack("h", ID))
        elif learned:
            self.write_cmd(REQUEST_ARROWS_LEARNED)
        else:
            self.write_cmd(REQUEST_ARROWS)
        result = self.process_info()
        if ARROWS in result:
            return result[ARROWS]
        else:
            return []

    def get(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_BY_ID, struct.pack("h", ID))
        elif learned:
            self.write_cmd(REQUEST_LEARNED)
        else:
            self.write_cmd(REQUEST)
        return self.process_info()

    def show_text(self, text, position=(10, 10)):
        params = bytearray(len(text) + 4)
        params[0] = len(text)
        params[1] = 0 if position[0] <= 255 else 0xFF
        params[2] = position[0] % 255
        params[3] = position[1]
        params[4:] = bytes(text, "UTF-8")
        self.write_cmd(REQUEST_CUSTOM_TEXT, params)
        return self.check_ok(timeout=40)

    def clear_text(self):
        self.write_cmd(REQUEST_CLEAR_TEXT)
        return self.check_ok()

    def get_version(self):
        # This returns '.': OK and no payload on firmware 0.5.1
        self.write_cmd(REQUEST_FIRMWARE_VERSION)
        c, p = self.read_cmd()
        if not c:
            print("Version check failed. Older than 0.5?:", p)
            return None
        else:
            print("Version is:", p)
            return p


def clamp_int(r, low_cap=-100, high_cap=100):
    return int(min(max(r, low_cap), high_cap))
