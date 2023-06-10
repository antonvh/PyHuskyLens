import struct
import time
from micropython import const
from math import atan2, degrees
try:
    from hub import port
except:
    pass

try:
    from pybricks.iodevices import UARTDevice
except:
    pass


def byte(num):
    return bytes([num])

HEADER = b'\x55\xaa\x11'
FAILED = b''

(REQUEST, #0x20 = 32 etc....
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
RETURN_BUSY) = [byte(x) for x in range(0x20, 0x3e)]
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
    def __init__(self, x_tail, y_tail , x_head , y_head, ID):
        self.x_tail=x_tail
        self.y_tail=y_tail
        self.x_head=x_head
        self.y_head=y_head
        self.ID=ID
        self.learned= True if ID > 0 else False
        self.direction = degrees(atan2(x_tail-x_head, y_tail-y_head)) # Forward(up) = 0, left = 90
        self.type="ARROW"
    
    def __repr__(self):
        return "ARROW - x tail:{}, y tail:{}, x head:{}, y head:{}, direction: {}, ID:{}".format(
            self.x_tail,
            self.y_tail,
            self.x_head,
            self.y_head,
            self.direction,
            self.ID)

class Block:
    def __init__(self, x, y , width , height, ID):
        self.x=x
        self.y=y
        self.width=width
        self.height=height
        self.ID=ID
        self.learned= True if ID > 0 else False
        self.type="BLOCK"

    def __repr__(self):
        return "BLOCK - x:{}, y:{}, width:{}, height:{}, ID:{}".format(
            self.x,
            self.y,
            self.width,
            self.height,
            self.ID)

class HuskyLens():
    def __init__(self, port_str, baud=9600, debug=False, pwm=0):
        self.debug = debug
        if type(port_str) == str:
            # We're on SPIKE/Robot Inventor
            self.uart = eval("port."+port_str)
            self.uart.mode(1)
            time.sleep_ms(300)
            self.uart.baud(baud)
            self.uart.pwm(pwm)
            if pwm: time.sleep_ms(2200) # Give the huskylens some time to boot
            time.sleep_ms(300)
            self.uart.read(32)
            self.next_write = time.ticks_ms()
        else:
            # We're probably on ev3dev/pybricks
            self.uart = UARTDevice(port_str, baud)
        if not self.knock():
            print("Huskylens connection failed. Check wires and port is {}?".format(port_str))
        else:
            print("Connected")

    @staticmethod
    def calc_checksum(data):
        return byte(sum(bytearray(data)) & 0xff)

    def write_cmd(self, command, payload=b''):
        length = byte(len(payload))
        data = HEADER + length + command + payload
        data += self.calc_checksum(data)
        self.uart.write(data)
        if self.debug: 
            pass
            print("Sent: ",data)
        else:
            time.sleep_ms(5)

    def force_read(self, size=1, max_tries=150, search=b''):
        data = b''
        r=self.uart.read(size)
        for i in range(max_tries):
            if r==None:
                # On SPIKE b'' is returned, on OpenMV None
                r=b''
            data += r
            if search:
                if len(data) >= len(search):
                    if data[-len(search):] == search:
                        return search
            elif len(data) == size:
                return data
            
            time.sleep_ms(1)
            r=self.uart.read(1)

            if i > 3 and self.debug:
                print("Waiting for data in force read. Tries:", i)
        return data

    def read_cmd(self):
        payload = b''
        r = self.force_read(search=HEADER)
        if r is not HEADER:
            if self.debug: print("No answer from huskylens")
            return FAILED, "No header"
        length = self.force_read(1)
        command = self.force_read(1)
        if length[0] > 0:
            payload = self.force_read(length[0])
        checksum = self.force_read(1) 
        if checksum != self.calc_checksum(HEADER+length+command+payload):
            if self.debug: print("Checksum failed", checksum, self.calc_checksum(HEADER+length+command+payload))
            return FAILED, "Bad checksum"
        return command, payload

    def check_ok(self):
        answer_cmd, answer_params = self.read_cmd()
        if answer_cmd == RETURN_OK: 
            return True
        else:
            print("Expected OK, but got:", answer_cmd, answer_params)
            return False

    def knock(self):
        self.write_cmd(REQUEST_KNOCK)
        return self.check_ok()
        
    def set_alg(self, algorithm):
        self.write_cmd(REQUEST_ALGORITHM, payload=struct.pack('h', algorithm))
        return self.check_ok()

    def process_info(self):
        blocks = []
        arrows = []
        ret, info= self.read_cmd()
        if ret != RETURN_INFO:
            if self.debug: 
                print("Expected info")
            return {}

        try:
            n_blocks_arrows, n_ids, frame, _, _ = struct.unpack('hhhhh',info)
        except:
            n_blocks_arrows, n_ids, frame = (0,0,0)
        if self.debug: print(n_blocks_arrows, n_ids, frame)

        for i in range(n_blocks_arrows):
            obj_type, data = self.read_cmd()
            if obj_type == RETURN_BLOCK:
                blocks += [Block(*struct.unpack('hhhhh',data))]
            elif obj_type == RETURN_ARROW:
                arrows += [Arrow(*struct.unpack('hhhhh',data))]
            else:
                if self.debug:
                    print("Expected blocks or arrows")

        return {BLOCKS: blocks, 
                ARROWS: arrows,
                FRAME: frame}

    def get_blocks(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_BLOCKS_BY_ID, struct.pack('h', ID))
        elif learned:
            self.write_cmd(REQUEST_BLOCKS_LEARNED)
        else:
            self.write_cmd(REQUEST_BLOCKS)
        return self.process_info()[BLOCKS]

    def get_arrows(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_ARROWS_BY_ID, struct.pack('h', ID))
        elif learned:
            self.write_cmd(REQUEST_ARROWS_LEARNED)
        else:
            self.write_cmd(REQUEST_ARROWS)
        return self.process_info()[ARROWS]

    def get(self, ID=None, learned=False):
        if ID:
            self.write_cmd(REQUEST_BY_ID, struct.pack('h', ID))
        elif learned:
            self.write_cmd(REQUEST_LEARNED)
        else:
            self.write_cmd(REQUEST)
        return self.process_info()

    def show_text(self, text, position=(10,10)):
        params = bytearray(len(text)+4)
        params[0] = len(text)
        params[1] = 0 if position[0] <= 255 else 0xFF
        params[2] = position[0] % 255
        params[3] = position[1]
        params[4:] = bytes(text, "UTF-8")
        self.write_cmd(REQUEST_CUSTOM_TEXT, params)
        time.sleep_ms(40)
        return self.check_ok()

    def clear_text(self):
        self.write_cmd(REQUEST_CLEAR_TEXT)
        return self.check_ok()

    def get_version(self):
        # This returns '.': OK and no payload on firmware 0.5.1
        self.write_cmd(REQUEST_FIRMWARE_VERSION)
        c,p = self.read_cmd()
        if not c:
            print("Version check failed. Older than 0.5?:", p)
            return None
        else:
            print("Version is:", p)
            return p


def clamp_int(r, low_cap=-100, high_cap=100):
    return int(min(max(r,low_cap), high_cap))