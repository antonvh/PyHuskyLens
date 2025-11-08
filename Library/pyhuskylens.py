"""
HuskyLens Universal Driver for MicroPython
Supports V1 and V2 hardware with I2C and Serial interfaces

Copyright (c) 2025 Antons Mindstorms
"""

import struct
import time
from micropython import const
from math import atan2, degrees

# Demo constants when running as main
EV3_PYBRICKS_SERIAL = const(0)
INVENTOR_SERIAL = const(1)
ESP32_I2C = const(3)
MAIN_DEMO_TYPE = ESP32_I2C  # Change this to test different interfaces

# Protocol headers
HEADER_V1 = b"\x55\xaa\x11"
HEADER_V2 = b"\x55\xaa"

# V1 Commands
CMD_REQUEST = const(0x20)
CMD_REQUEST_BY_ID = const(0x26)
CMD_REQUEST_LEARNED = const(0x23)
CMD_RETURN_INFO = const(0x29)
CMD_RETURN_BLOCK = const(0x2A)
CMD_RETURN_ARROW = const(0x2B)
CMD_REQUEST_KNOCK = const(0x2C)
CMD_REQUEST_ALGORITHM = const(0x2D)
CMD_RETURN_OK = const(0x2E)
CMD_REQUEST_CUSTOM_TEXT = const(0x34)
CMD_REQUEST_CLEAR_TEXT = const(0x35)
CMD_REQUEST_FIRMWARE_VERSION = const(0x3C)

# V2 Commands
CMD_KNOCK_V2 = const(0x20)
CMD_GET_RESULT_V2 = const(0x21)
CMD_SET_ALGORITHM_V2 = const(0x30)
CMD_SET_MULTI_ALGORITHM_V2 = const(0x32)
CMD_SET_MULTI_ALGORITHM_RATIO_V2 = const(0x33)
CMD_RETURN_OK_V2 = const(0x40)
CMD_RETURN_INFO_V2 = const(0x42)
CMD_RETURN_BLOCK_V2 = const(0x43)
CMD_RETURN_ARROW_V2 = const(0x44)
CMD_ACTION_DRAW_TEXT_V2 = const(0x58)
CMD_ACTION_CLEAR_TEXT_V2 = const(0x59)
CMD_ACTION_DRAW_RECT_V2 = const(0x56)
CMD_ACTION_CLEAN_RECT_V2 = const(0x57)

# Algorithms
ALGORITHM_MENU = const(0)
ALGORITHM_FACE_RECOGNITION = const(1)
ALGORITHM_OBJECT_TRACKING = const(2)
ALGORITHM_OBJECT_RECOGNITION = const(3)
ALGORITHM_LINE_TRACKING = const(4)
ALGORITHM_COLOR_RECOGNITION = const(5)
ALGORITHM_TAG_RECOGNITION = const(6)
ALGORITHM_OBJECT_CLASSIFICATION = const(7)
ALGORITHM_OCR = const(8)
ALGORITHM_LICENSE_RECOGNITION = const(9)
ALGORITHM_QR_CODE_RECOGNITION = const(10)
ALGORITHM_BARCODE_RECOGNITION = const(11)
ALGORITHM_FACE_EMOTION_RECOGNITION = const(12)
ALGORITHM_POSE_RECOGNITION = const(13)
ALGORITHM_HAND_RECOGNITION = const(14)

# Colors
COLOR_BLACK = const(0)
COLOR_WHITE = const(1)
COLOR_RED = const(2)
COLOR_GREEN = const(3)
COLOR_BLUE = const(4)
COLOR_YELLOW = const(5)

# I2C Register for V1
I2C_REG_V1 = const(0x0C)


class Arrow:
    """Arrow detection result."""
    __slots__ = ('x_tail', 'y_tail', 'x_head', 'y_head', 'ID', 'learned', 'direction', 'type')
    
    def __init__(self, x_tail, y_tail, x_head, y_head, ID):
        self.x_tail, self.y_tail, self.x_head, self.y_head, self.ID = x_tail, y_tail, x_head, y_head, ID
        self.learned = ID > 0
        self.direction = degrees(atan2(x_tail - x_head, y_tail - y_head))
        self.type = "ARROW"

    def __repr__(self):
        return "Arrow(tail=(" + str(self.x_tail) + "," + str(self.y_tail) + "), head=(" + str(self.x_head) + "," + str(self.y_head) + "), dir=" + str(self.direction) + ", ID=" + str(self.ID) + ")"


class Block:
    """Block detection result."""
    __slots__ = ('x', 'y', 'width', 'height', 'ID', 'confidence', 'name', 'content', 'learned', 'type')
    
    def __init__(self, x, y, width, height, ID, confidence=0, name="", content=""):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.ID, self.confidence, self.name, self.content = ID, confidence, name, content
        self.learned = ID > 0
        self.type = "BLOCK"

    def __repr__(self):
        s = "Block(x=" + str(self.x) + ", y=" + str(self.y) + ", w=" + str(self.width) + ", h=" + str(self.height) + ", ID=" + str(self.ID)
        if self.confidence: s += ", conf=" + str(self.confidence)
        if self.name: s += ", name='" + self.name + "'"
        if self.content: s += ", content='" + self.content + "'"
        return s + ")"


class Face:
    """Face with landmarks (V2 only)."""
    __slots__ = ('x', 'y', 'width', 'height', 'ID', 'confidence', 'name', 'content', 'learned', 'type',
                 'leye_x', 'leye_y', 'reye_x', 'reye_y', 'nose_x', 'nose_y',
                 'lmouth_x', 'lmouth_y', 'rmouth_x', 'rmouth_y')
    
    def __init__(self, x, y, width, height, ID, confidence, name, content, landmarks):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.ID, self.confidence, self.name, self.content = ID, confidence, name, content
        self.learned = ID > 0
        self.type = "FACE"
        if len(landmarks) >= 10:
            self.leye_x, self.leye_y = landmarks[0], landmarks[1]
            self.reye_x, self.reye_y = landmarks[2], landmarks[3]
            self.nose_x, self.nose_y = landmarks[4], landmarks[5]
            self.lmouth_x, self.lmouth_y = landmarks[6], landmarks[7]
            self.rmouth_x, self.rmouth_y = landmarks[8], landmarks[9]

    def __repr__(self):
        return "Face(x=" + str(self.x) + ", y=" + str(self.y) + ", ID=" + str(self.ID) + ")"


class Hand:
    """Hand with 21 keypoints (V2 only)."""
    __slots__ = ('x', 'y', 'width', 'height', 'ID', 'confidence', 'name', 'content', 'learned', 'type',
                 'wrist_x', 'wrist_y', 'thumb_cmc_x', 'thumb_cmc_y', 'thumb_mcp_x', 'thumb_mcp_y',
                 'thumb_ip_x', 'thumb_ip_y', 'thumb_tip_x', 'thumb_tip_y',
                 'index_finger_mcp_x', 'index_finger_mcp_y', 'index_finger_pip_x', 'index_finger_pip_y',
                 'index_finger_dip_x', 'index_finger_dip_y', 'index_finger_tip_x', 'index_finger_tip_y',
                 'middle_finger_mcp_x', 'middle_finger_mcp_y', 'middle_finger_pip_x', 'middle_finger_pip_y',
                 'middle_finger_dip_x', 'middle_finger_dip_y', 'middle_finger_tip_x', 'middle_finger_tip_y',
                 'ring_finger_mcp_x', 'ring_finger_mcp_y', 'ring_finger_pip_x', 'ring_finger_pip_y',
                 'ring_finger_dip_x', 'ring_finger_dip_y', 'ring_finger_tip_x', 'ring_finger_tip_y',
                 'pinky_finger_mcp_x', 'pinky_finger_mcp_y', 'pinky_finger_pip_x', 'pinky_finger_pip_y',
                 'pinky_finger_dip_x', 'pinky_finger_dip_y', 'pinky_finger_tip_x', 'pinky_finger_tip_y')
    
    def __init__(self, x, y, width, height, ID, confidence, name, content, keypoints):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.ID, self.confidence, self.name, self.content = ID, confidence, name, content
        self.learned = ID > 0
        self.type = "HAND"
        if len(keypoints) >= 42:
            self.wrist_x, self.wrist_y = keypoints[0], keypoints[1]
            self.thumb_cmc_x, self.thumb_cmc_y = keypoints[2], keypoints[3]
            self.thumb_mcp_x, self.thumb_mcp_y = keypoints[4], keypoints[5]
            self.thumb_ip_x, self.thumb_ip_y = keypoints[6], keypoints[7]
            self.thumb_tip_x, self.thumb_tip_y = keypoints[8], keypoints[9]
            self.index_finger_mcp_x, self.index_finger_mcp_y = keypoints[10], keypoints[11]
            self.index_finger_pip_x, self.index_finger_pip_y = keypoints[12], keypoints[13]
            self.index_finger_dip_x, self.index_finger_dip_y = keypoints[14], keypoints[15]
            self.index_finger_tip_x, self.index_finger_tip_y = keypoints[16], keypoints[17]
            self.middle_finger_mcp_x, self.middle_finger_mcp_y = keypoints[18], keypoints[19]
            self.middle_finger_pip_x, self.middle_finger_pip_y = keypoints[20], keypoints[21]
            self.middle_finger_dip_x, self.middle_finger_dip_y = keypoints[22], keypoints[23]
            self.middle_finger_tip_x, self.middle_finger_tip_y = keypoints[24], keypoints[25]
            self.ring_finger_mcp_x, self.ring_finger_mcp_y = keypoints[26], keypoints[27]
            self.ring_finger_pip_x, self.ring_finger_pip_y = keypoints[28], keypoints[29]
            self.ring_finger_dip_x, self.ring_finger_dip_y = keypoints[30], keypoints[31]
            self.ring_finger_tip_x, self.ring_finger_tip_y = keypoints[32], keypoints[33]
            self.pinky_finger_mcp_x, self.pinky_finger_mcp_y = keypoints[34], keypoints[35]
            self.pinky_finger_pip_x, self.pinky_finger_pip_y = keypoints[36], keypoints[37]
            self.pinky_finger_dip_x, self.pinky_finger_dip_y = keypoints[38], keypoints[39]
            self.pinky_finger_tip_x, self.pinky_finger_tip_y = keypoints[40], keypoints[41]

    def __repr__(self):
        return "Hand(x=" + str(self.x) + ", y=" + str(self.y) + ", ID=" + str(self.ID) + ", wrist=(" + str(self.wrist_x) + "," + str(self.wrist_y) + "))"


class Pose:
    """Pose with 17 body keypoints (V2 only)."""
    __slots__ = ('x', 'y', 'width', 'height', 'ID', 'confidence', 'name', 'content', 'learned', 'type',
                 'nose_x', 'nose_y', 'leye_x', 'leye_y', 'reye_x', 'reye_y',
                 'lear_x', 'lear_y', 'rear_x', 'rear_y',
                 'lshoulder_x', 'lshoulder_y', 'rshoulder_x', 'rshoulder_y',
                 'lelbow_x', 'lelbow_y', 'relbow_x', 'relbow_y',
                 'lwrist_x', 'lwrist_y', 'rwrist_x', 'rwrist_y',
                 'lhip_x', 'lhip_y', 'rhip_x', 'rhip_y',
                 'lknee_x', 'lknee_y', 'rknee_x', 'rknee_y',
                 'lankle_x', 'lankle_y', 'rankle_x', 'rankle_y')
    
    def __init__(self, x, y, width, height, ID, confidence, name, content, keypoints):
        self.x, self.y, self.width, self.height = x, y, width, height
        self.ID, self.confidence, self.name, self.content = ID, confidence, name, content
        self.learned = ID > 0
        self.type = "POSE"
        if len(keypoints) >= 34:
            self.nose_x, self.nose_y = keypoints[0], keypoints[1]
            self.leye_x, self.leye_y = keypoints[2], keypoints[3]
            self.reye_x, self.reye_y = keypoints[4], keypoints[5]
            self.lear_x, self.lear_y = keypoints[6], keypoints[7]
            self.rear_x, self.rear_y = keypoints[8], keypoints[9]
            self.lshoulder_x, self.lshoulder_y = keypoints[10], keypoints[11]
            self.rshoulder_x, self.rshoulder_y = keypoints[12], keypoints[13]
            self.lelbow_x, self.lelbow_y = keypoints[14], keypoints[15]
            self.relbow_x, self.relbow_y = keypoints[16], keypoints[17]
            self.lwrist_x, self.lwrist_y = keypoints[18], keypoints[19]
            self.rwrist_x, self.rwrist_y = keypoints[20], keypoints[21]
            self.lhip_x, self.lhip_y = keypoints[22], keypoints[23]
            self.rhip_x, self.rhip_y = keypoints[24], keypoints[25]
            self.lknee_x, self.lknee_y = keypoints[26], keypoints[27]
            self.rknee_x, self.rknee_y = keypoints[28], keypoints[29]
            self.lankle_x, self.lankle_y = keypoints[30], keypoints[31]
            self.rankle_x, self.rankle_y = keypoints[32], keypoints[33]

    def __repr__(self):
        return "Pose(x=" + str(self.x) + ", y=" + str(self.y) + ", ID=" + str(self.ID) + ", nose=(" + str(self.nose_x) + "," + str(self.nose_y) + "))"


class HuskyLensBase:
    """Base class with all HuskyLens logic."""
    
    def __init__(self, debug=False):
        self.debug = debug
        self.version = None
        self.connected = False
        self.current_algorithm = ALGORITHM_OBJECT_RECOGNITION
    
    # Abstract methods for subclasses
    def _transport_write(self, data):
        raise NotImplementedError
    
    def _transport_read(self, size):
        raise NotImplementedError
    
    def _transport_flush(self):
        raise NotImplementedError
    
    def _detect_version(self):
        raise NotImplementedError
    
    # Utilities
    def _checksum(self, data):
        return sum(data) & 0xFF
    
    def _write(self, data):
        try:
            if self.version == 2:
                self._transport_flush()
            self._transport_write(data)
            time.sleep_ms(5)
        except Exception as e:
            if self.debug: 
                print("Write error: " + str(e))
    
    # V1 protocol
    def _cmd_v1(self, command, payload=None):
        if payload is None:
            payload = bytearray()
        data = bytearray(HEADER_V1)
        data.append(len(payload))
        data.append(command)
        data.extend(payload)
        data.append(self._checksum(data))
        self._write(bytes(data))
    
    def _read_v1(self):
        try:
            for _ in range(50):
                if self._transport_read(3) == HEADER_V1:
                    break
            else:
                return None, None
            
            length = self._transport_read(1)[0]
            command = self._transport_read(1)[0]
            payload = self._transport_read(length) if length else bytearray()
            checksum = self._transport_read(1)[0]
            
            expected = bytearray(HEADER_V1)
            expected.append(length)
            expected.append(command)
            expected.extend(payload)
            
            if checksum == self._checksum(expected):
                return command, payload
        except Exception as e:
            if self.debug:
                print("Read V1 error: " + str(e))
        return None, None
    
    # V2 protocol
    def _cmd_v2(self, command, algorithm=0, content=None):
        packet = bytearray([0x55, 0xAA, command, algorithm, len(content) if content else 0])
        if content:
            packet.extend(content)
        packet.append(self._checksum(packet))
        self._write(bytes(packet))
    
    def _read_v2(self):
        try:
            header = self._transport_read(5)
            if len(header) == 5 and header[:2] == HEADER_V2:
                size = header[4]
                return header + self._transport_read(size + 1)
        except Exception as e:
            if self.debug:
                print("Read V2 error: " + str(e))
        return None
    
    # Public API
    def knock(self):
        """Test connection."""
        if self.version == 1:
            self._cmd_v1(CMD_REQUEST_KNOCK)
            for _ in range(10):
                cmd, _ = self._read_v1()
                if cmd == CMD_RETURN_OK:
                    self.connected = True
                    return True
                time.sleep_ms(10)
        else:  # V2
            for _ in range(5):
                try:
                    self._cmd_v2(CMD_KNOCK_V2)
                    resp = self._transport_read(6)
                    if len(resp) >= 3 and resp[:2] == HEADER_V2 and resp[2] == CMD_RETURN_OK_V2:
                        self.connected = True
                        return True
                except Exception as e:
                    if self.debug:
                        print("Knock V2 error: " + str(e))
                time.sleep_ms(50)
        self.connected = False
        return False
    
    def set_alg(self, algorithm=None):
        """Switch algorithm."""
        if algorithm is None:
            algorithm = self.current_algorithm
        if algorithm == self.current_algorithm and self.version == 2:
            return True
        
        if self.version == 1:
            # check algo available, and +1 for V1 indexing
            if 0 < algorithm < 7:
                algorithm -= 1
            elif 10 <= algorithm <= 11:
                algorithm -= 3
            payload = bytearray(struct.pack("h", algorithm))
            self._cmd_v1(CMD_REQUEST_ALGORITHM, payload)
        else:  # V2
            content = bytearray([algorithm, 0])
            content.extend(struct.pack('<hhhh', 0, 0, 0, 0))
            self._cmd_v2(CMD_SET_ALGORITHM_V2, 0, content)
        
        result = self.knock()
        if result:
            self.current_algorithm = algorithm
        return result
    
    def set_multi_alg(self, *algorithms):
        """Set multiple algorithms (V2 only)."""
        if self.version != 2 or len(algorithms) < 2 or len(algorithms) > 5:
            return False
        
        content = bytearray([len(algorithms), 0])
        for i in range(4):
            content.extend(struct.pack('<h', algorithms[i] if i < len(algorithms) else 0))
        
        self._cmd_v2(CMD_SET_MULTI_ALGORITHM_V2, 0, content)
        return self.knock()
    
    def get_version(self):
        """Get firmware version (V1 only)."""
        if self.version != 1:
            return None
        self._cmd_v1(CMD_REQUEST_FIRMWARE_VERSION)
        cmd, payload = self._read_v1()
        if payload:
            try:
                return payload.decode('utf-8')
            except Exception as e:
                if self.debug:
                    print("Version decode error: " + str(e))
                return str(payload)
        return None
    
    def get(self, algorithm=None, ID=None, learned=False):
        """Get all blocks and arrows."""
        if algorithm is None:
            algorithm = self.current_algorithm
        
        blocks, arrows = [], []
        
        if self.version == 1:
            if ID is not None:
                payload = bytearray(struct.pack("h", ID))
                self._cmd_v1(CMD_REQUEST_BY_ID, payload)
            elif learned:
                self._cmd_v1(CMD_REQUEST_LEARNED)
            else:
                self._cmd_v1(CMD_REQUEST)
            
            cmd, info = self._read_v1()
            if cmd == CMD_RETURN_INFO:
                try:
                    n_objs = struct.unpack("h", info[:2])[0] if info else 0
                except Exception as e:
                    if self.debug:
                        print("Info parse error: " + str(e))
                    n_objs = 0
                
                for _ in range(n_objs):
                    cmd, data = self._read_v1()
                    try:
                        if cmd == CMD_RETURN_BLOCK:
                            blocks.append(Block(*struct.unpack("hhhhh", data)))
                        elif cmd == CMD_RETURN_ARROW:
                            arrows.append(Arrow(*struct.unpack("hhhhh", data)))
                    except Exception as e:
                        if self.debug:
                            print("Object parse error: " + str(e))
        
        else:  # V2
            self._cmd_v2(CMD_GET_RESULT_V2, algorithm)
            time.sleep_ms(50)
            
            info = self._read_v2()
            if info and info[2] == CMD_RETURN_INFO_V2:
                try:
                    n_results = struct.unpack('<h', info[7:9])[0]
                except Exception as e:
                    if self.debug:
                        print("V2 info parse error: " + str(e))
                    n_results = 0
                
                for _ in range(n_results):
                    time.sleep_ms(10)
                    pkt = self._read_v2()
                    if pkt:
                        obj = self._parse_v2(pkt, algorithm)
                        if obj:
                            if obj.type in ("BLOCK", "FACE", "HAND", "POSE"):
                                blocks.append(obj)
                            elif obj.type == "ARROW":
                                arrows.append(obj)
            
            self._transport_flush()
        
        # Apply filters
        if ID is not None:
            blocks = [b for b in blocks if b.ID == ID]
            arrows = [a for a in arrows if a.ID == ID]
        elif learned:
            blocks = [b for b in blocks if b.learned]
            arrows = [a for a in arrows if a.learned]
        
        return {'blocks': blocks, 'arrows': arrows}
    
    def get_blocks(self, algorithm=None, ID=None, learned=False):
        """Get blocks only."""
        return self.get(algorithm, ID, learned)['blocks']
    
    def get_arrows(self, algorithm=None, ID=None, learned=False):
        """Get arrows only."""
        return self.get(algorithm, ID, learned)['arrows']
    
    def _parse_v2(self, data, algorithm):
        """Parse V2 result packet."""
        if len(data) < 15:
            return None
        
        cmd, size = data[2], data[4]
        if size < 10:
            return None
        
        try:
            ID, conf = struct.unpack('bb', bytes(data[5:7]))
            x, y, w, h = struct.unpack('<hhhh', bytes(data[7:15]))
        except Exception as e:
            if self.debug:
                print("V2 header parse error: " + str(e))
            return None
        
        # Parse strings
        name, content, offset = "", "", 15
        if size > 10 and len(data) > offset:
            try:
                name_len = data[offset]
                offset += 1
                if name_len > 0 and len(data) >= offset + name_len:
                    name = bytes(data[offset:offset+name_len]).decode('utf-8')
                    offset += name_len
                
                if len(data) > offset:
                    content_len = data[offset]
                    offset += 1
                    if content_len > 0 and len(data) >= offset + content_len:
                        content = bytes(data[offset:offset+content_len]).decode('utf-8')
                        offset += content_len
            except Exception as e:
                if self.debug:
                    print("String parse error: " + str(e))
        
        # Parse keypoints
        keypoints = []
        if len(data) > offset + 1:
            try:
                for i in range((len(data) - offset - 1) // 2):
                    if offset + 2 <= len(data) - 1:
                        keypoints.append(struct.unpack('<h', bytes(data[offset:offset+2]))[0])
                        offset += 2
            except Exception as e:
                if self.debug:
                    print("Keypoint parse error: " + str(e))
        
        # Return appropriate class
        try:
            if cmd == CMD_RETURN_BLOCK_V2:
                if algorithm == ALGORITHM_FACE_RECOGNITION and keypoints:
                    return Face(x, y, w, h, ID, conf, name, content, keypoints)
                elif algorithm == ALGORITHM_HAND_RECOGNITION and keypoints:
                    return Hand(x, y, w, h, ID, conf, name, content, keypoints)
                elif algorithm == ALGORITHM_POSE_RECOGNITION and keypoints:
                    return Pose(x, y, w, h, ID, conf, name, content, keypoints)
                else:
                    return Block(x, y, w, h, ID, conf, name, content)
            elif cmd == CMD_RETURN_ARROW_V2:
                return Arrow(x, y, w, h, ID)
        except Exception as e:
            if self.debug:
                print("Object creation error: " + str(e))
        
        return None
    
    def draw_text(self, text, x=10, y=10, color=COLOR_WHITE):
        """Draw text on screen."""
        if self.version == 1:
            params = bytearray([len(text), 0 if x <= 255 else 0xFF, x % 255, y])
            params.extend(text.encode('utf-8'))
            self._cmd_v1(CMD_REQUEST_CUSTOM_TEXT, params)
        else:  # V2
            content = bytearray([color, 0])
            content.extend(struct.pack('<hhhh', x, y, 0, 0))
            txt = text.encode('utf-8')
            content.append(len(txt))
            content.extend(txt)
            self._cmd_v2(CMD_ACTION_DRAW_TEXT_V2, 0, content)
        return self.knock()
    
    def clear_text(self):
        """Clear text from screen."""
        if self.version == 1:
            self._cmd_v1(CMD_REQUEST_CLEAR_TEXT)
        else:
            self._cmd_v2(CMD_ACTION_CLEAR_TEXT_V2, 0)
        return self.knock()
    
    def draw_rect(self, x1, y1, x2, y2, color=COLOR_WHITE):
        """Draw rectangle (V2 only)."""
        if self.version != 2:
            return False
        content = bytearray([color, 0])
        content.extend(struct.pack('<hhhh', x1, y1, x2, y2))
        self._cmd_v2(CMD_ACTION_DRAW_RECT_V2, 0, content)
        return self.knock()
    
    def clear_rect(self):
        """Clear rectangles (V2 only)."""
        if self.version != 2:
            return False
        self._cmd_v2(CMD_ACTION_CLEAN_RECT_V2, 0)
        return self.knock()


class HuskyLensI2C(HuskyLensBase):
    """HuskyLens I2C driver."""
    
    ADDR_V1 = const(0x32)
    ADDR_V2 = const(0x50)
    
    def __init__(self, i2c, debug=False):
        super().__init__(debug)
        self.i2c = i2c
        self.address = None
        self.use_register = False
        self._detect_version()
    
    def _detect_version(self):
        devices = self.i2c.scan()
        if self.ADDR_V1 in devices:
            self.version, self.address = 1, self.ADDR_V1
        elif self.ADDR_V2 in devices:
            self.version, self.address = 2, self.ADDR_V2
        if self.debug and self.version:
            print("HuskyLens V" + str(self.version) + " @ 0x" + hex(self.address)[2:])
    
    def _transport_write(self, data):
        if self.version == 1:
            # V1: Write to register 0x0C
            self.i2c.writeto_mem(self.address, I2C_REG_V1, data)
        else:
            # V2: Direct write
            self.i2c.writeto(self.address, data)
    
    def _transport_read(self, size):
        if self.version == 1:
            # V1: Read from register 0x0C
            return self.i2c.readfrom_mem(self.address, I2C_REG_V1, size)
        else:
            # V2: Direct read
            return self.i2c.readfrom(self.address, size)
    
    def _transport_flush(self):
        # Only V2 needs flushing
        if self.version == 2:
            for _ in range(5):
                self.i2c.readfrom(self.address, 16)


class HuskyLensSerial(HuskyLensBase):
    """HuskyLens Serial/UART driver."""
    
    def __init__(self, uart, debug=False):
        super().__init__(debug)
        self.uart = uart
        # Abstract waiting method
        if hasattr(uart, 'waiting'):
            self._has_data = lambda: uart.waiting()
        elif hasattr(uart, 'any'):
            self._has_data = lambda: uart.any()
        else:
            self._has_data = lambda: True  # Fallback: always try to read
        self._detect_version()
    
    def _detect_version(self):
        # Try V2 first
        self.version = 2
        if self.knock():
            if self.debug: print("HuskyLens V2 (UART)")
            return
        # Try V1
        self.version = 1
        if self.knock():
            if self.debug: print("HuskyLens V1 (UART)")
            return
        self.version = None
        if self.debug: print("No HuskyLens on UART")
    
    def _transport_write(self, data):
        self.uart.write(data)
    
    def _transport_read(self, size):
        """Read with pybricks/ev3dev compatibility."""
        data = bytearray()
        for _ in range(150):
            if self._has_data():
                chunk = self.uart.read(1)
                if chunk:
                    data.extend(chunk)
            if len(data) >= size:
                return bytes(data[:size])
            time.sleep_ms(1)
        return bytes(data)
    
    def _transport_flush(self):
        """Flush with pybricks/ev3dev compatibility."""
        try:
            for _ in range(10):
                if self._has_data():
                    amount = self._has_data() if callable(self._has_data()) else 64
                    if isinstance(amount, bool):
                        amount = 64
                    self.uart.read(min(amount, 64))
                else:
                    break
        except Exception as e:
            if self.debug:
                print("Flush error: " + str(e))


# Demo
if __name__ == "__main__":
    if MAIN_DEMO_TYPE == ESP32_I2C:
        from machine import Pin, SoftI2C
        
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
                hl_i2c.draw_text("Hello!", 50, 50, COLOR_GREEN)
                print("V Text demo complete")
                
                # Set algorithm and get blocks
                print("\nSetting algorithm to Object Recognition...")
                hl_i2c.set_alg(ALGORITHM_OBJECT_RECOGNITION)
                time.sleep(2)
                print("Getting blocks...")
                for i in range(20):
                    blocks = hl_i2c.get_blocks()
                    print("V Found " + str(len(blocks)) + " blocks")
                    for block in blocks:
                        print("  " + str(block))
            else:
                print("X Connection failed!")
    
    if MAIN_DEMO_TYPE == EV3_PYBRICKS_SERIAL or MAIN_DEMO_TYPE == INVENTOR_SERIAL:
        if MAIN_DEMO_TYPE == EV3_PYBRICKS_SERIAL:
            print("\n--- Serial Example Ev3dev Pybricks ---")
            from pybricks.iodevices import UARTDevice
            from pybricks.parameters import Port
            uart = UARTDevice(Port.A, 9600)
                
        elif MAIN_DEMO_TYPE == INVENTOR_SERIAL:
            print("\n--- Serial Example LEGO Inventor and SPIKE LEGACY---")
            from hub import port
            uart = port.A
            uart.mode(1)
            time.sleep_ms(300)
            uart.baud(9600)
            # Put voltage on M+ or M- leads
            uart.pwm(100)
            time.sleep_ms(2200)  # Give the huskylens some time to boot
            time.sleep_ms(300)
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
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)