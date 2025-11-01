"""
HuskyLens Universal Driver for MicroPython
Supports both V1 and V2 hardware with auto-detection

Memory optimization tips:
1. Use gc.collect() after large operations
2. Delete unused objects explicitly: del obj
3. Use const() for all constants to save RAM
4. Reuse Block/Arrow/Hand objects instead of creating new ones
5. Call get() with specific filters to reduce object creation
6. Pre-compile this module with mpy-cross
"""

import struct
import time
from micropython import const
from math import atan2, degrees
from machine import Pin, SoftI2C

# Protocol headers
HEADER_V1 = b"\x55\xaa\x11"
HEADER_V2 = b"\x55\xaa"

# V1 Commands (const for memory efficiency)
CMD_REQUEST = const(0x20)
CMD_REQUEST_BLOCKS = const(0x21)
CMD_REQUEST_ARROWS = const(0x22)
CMD_REQUEST_LEARNED = const(0x23)
CMD_REQUEST_BLOCKS_LEARNED = const(0x24)
CMD_REQUEST_ARROWS_LEARNED = const(0x25)
CMD_REQUEST_BY_ID = const(0x26)
CMD_REQUEST_BLOCKS_BY_ID = const(0x27)
CMD_REQUEST_ARROWS_BY_ID = const(0x28)
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
ALGORITHM_FACE_RECOGNITION = const(0)
ALGORITHM_OBJECT_TRACKING = const(1)
ALGORITHM_OBJECT_RECOGNITION = const(2)
ALGORITHM_LINE_TRACKING = const(3)
ALGORITHM_COLOR_RECOGNITION = const(4)
ALGORITHM_TAG_RECOGNITION = const(5)
ALGORITHM_OBJECT_CLASSIFICATION = const(6)
ALGORITHM_QR_CODE_RECOGNITION = const(7)
ALGORITHM_BARCODE_RECOGNITION = const(8)
# V2 additional algorithms
ALGORITHM_POSE_RECOGNITION = const(13)
ALGORITHM_HAND_RECOGNITION = const(14)

# Color IDs (0-9 for standard colors)
COLOR_BLACK = const(0)
COLOR_WHITE = const(1)
COLOR_RED = const(2)
COLOR_GREEN = const(3)
COLOR_BLUE = const(4)
COLOR_YELLOW = const(5)
COLOR_CYAN = const(6)
COLOR_MAGENTA = const(7)
COLOR_ORANGE = const(8)
COLOR_PURPLE = const(9)


class Arrow:
    """Arrow detection result.
    
    Properties:
        x_tail (int): X coordinate of arrow tail
        y_tail (int): Y coordinate of arrow tail
        x_head (int): X coordinate of arrow head
        y_head (int): Y coordinate of arrow head
        ID (int): Learned ID (0 if not learned)
        learned (bool): True if this arrow has been learned
        direction (float): Arrow direction in degrees (0=up, 90=left, 180=down, 270=right)
        type (str): Always "ARROW"
    """
    
    __slots__ = ('x_tail', 'y_tail', 'x_head', 'y_head', 'ID', 'learned', 'direction', 'type')
    
    def __init__(self, x_tail, y_tail, x_head, y_head, ID):
        self.x_tail = x_tail
        self.y_tail = y_tail
        self.x_head = x_head
        self.y_head = y_head
        self.ID = ID
        self.learned = ID > 0
        self.direction = degrees(atan2(x_tail - x_head, y_tail - y_head))
        self.type = "ARROW"

    def __repr__(self):
        return f"Arrow(tail=({self.x_tail},{self.y_tail}), head=({self.x_head},{self.y_head}), dir={self.direction:.1f}°, ID={self.ID})"


class Block:
    """Block detection result.
    
    Properties:
        x (int): X coordinate of block center
        y (int): Y coordinate of block center
        width (int): Block width in pixels
        height (int): Block height in pixels
        ID (int): Learned ID (0 if not learned)
        confidence (int): Detection confidence (0-255, V2 only)
        name (str): Object name (V2 only, empty for V1)
        content (str): Additional content (V2 only, empty for V1)
        learned (bool): True if this block has been learned
        type (str): Always "BLOCK"
    """
    
    __slots__ = ('x', 'y', 'width', 'height', 'ID', 'confidence', 'name', 'content', 'learned', 'type')
    
    def __init__(self, x, y, width, height, ID, confidence=0, name="", content=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.ID = ID
        self.confidence = confidence
        self.name = name
        self.content = content
        self.learned = ID > 0
        self.type = "BLOCK"

    def __repr__(self):
        s = f"Block(x={self.x}, y={self.y}, w={self.width}, h={self.height}, ID={self.ID}"
        if self.confidence: s += f", conf={self.confidence}"
        if self.name: s += f", name='{self.name}'"
        if self.content: s += f", content='{self.content}'"
        return s + ")"


class Face:
    """Face detection result with facial landmarks (V2 only).
    
    Inherits all Block properties plus:
        leye_x, leye_y (int): Left eye coordinates
        reye_x, reye_y (int): Right eye coordinates
        nose_x, nose_y (int): Nose coordinates
        lmouth_x, lmouth_y (int): Left mouth corner coordinates
        rmouth_x, rmouth_y (int): Right mouth corner coordinates
    """
    
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
        return f"Face(x={self.x}, y={self.y}, ID={self.ID}, eyes=({self.leye_x},{self.leye_y}),({self.reye_x},{self.reye_y}))"


class Hand:
    """Hand detection result with 21 keypoints (V2 only).
    
    Inherits all Block properties plus 21 hand keypoints:
        wrist_x, wrist_y (int): Wrist position
        thumb_cmc_x/y, thumb_mcp_x/y, thumb_ip_x/y, thumb_tip_x/y (int): Thumb joints
        index_finger_mcp_x/y, _pip_x/y, _dip_x/y, _tip_x/y (int): Index finger joints
        middle_finger_mcp_x/y, _pip_x/y, _dip_x/y, _tip_x/y (int): Middle finger joints
        ring_finger_mcp_x/y, _pip_x/y, _dip_x/y, _tip_x/y (int): Ring finger joints
        pinky_finger_mcp_x/y, _pip_x/y, _dip_x/y, _tip_x/y (int): Pinky finger joints
    """
    
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
        return f"Hand(x={self.x}, y={self.y}, ID={self.ID}, wrist=({self.wrist_x},{self.wrist_y}))"


class Pose:
    """Pose detection result with 17 body keypoints (V2 only).
    
    Inherits all Block properties plus 17 body keypoints:
        nose_x, nose_y (int): Nose position
        leye_x/y, reye_x/y (int): Left and right eye positions
        lear_x/y, rear_x/y (int): Left and right ear positions
        lshoulder_x/y, rshoulder_x/y (int): Left and right shoulder positions
        lelbow_x/y, relbow_x/y (int): Left and right elbow positions
        lwrist_x/y, rwrist_x/y (int): Left and right wrist positions
        lhip_x/y, rhip_x/y (int): Left and right hip positions
        lknee_x/y, rknee_x/y (int): Left and right knee positions
        lankle_x/y, rankle_x/y (int): Left and right ankle positions
    """
    
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
        return f"Pose(x={self.x}, y={self.y}, ID={self.ID}, nose=({self.nose_x},{self.nose_y}))"


class HuskyLens:
    """Universal HuskyLens driver with auto-detection for V1 and V2."""
    
    ADDR_V1 = const(0x32)
    ADDR_V2 = const(0x50)
    
    def __init__(self, i2c, debug=False):
        self.i2c = i2c
        self.debug = debug
        self.version = None
        self.address = None
        self.connected = False
        self.current_algorithm = ALGORITHM_OBJECT_RECOGNITION
        self._detect_version()
    
    def _detect_version(self):
        # Auto-detect by scanning I2C
        devices = self.i2c.scan()
        if self.ADDR_V1 in devices:
            self.version = 1
            self.address = self.ADDR_V1
        elif self.ADDR_V2 in devices:
            self.version = 2
            self.address = self.ADDR_V2
        if self.debug and self.version:
            print(f"HuskyLens V{self.version} @ 0x{self.address:02X}")
    
    # Common utilities
    def _checksum(self, data):
        return sum(bytearray(data)) & 0xFF
    
    def _flush(self):
        # Flush I2C buffer - only when needed
        try:
            for _ in range(5):  # Reduced from 10
                try:
                    self.i2c.readfrom(self.address, 16)  # Reduced from 32
                except:
                    break
        except:
            pass
    
    def _write(self, data):
        # Write with version-specific wrapper
        try:
            if self.version == 2:
                self._flush()  # Only flush for V2 before write
            self.i2c.writeto(self.address, data)
            time.sleep_ms(5)  # Reduced from 10ms
        except Exception as e:
            if self.debug: print(f"Write error: {e}")
    
    def _check_ok(self):
        # Check for OK response (works for both V1 and V2)
        return self.knock()
    
    # V1-specific protocol
    def _cmd_v1(self, command, payload=b""):
        length = bytes([len(payload)])
        data = HEADER_V1 + length + bytes([command]) + payload
        data += bytes([self._checksum(data)])
        self._write(data)
    
    def _read_v1(self):
        # Read V1 packet
        try:
            for _ in range(50):
                d = self.i2c.readfrom(self.address, 3)
                if d == HEADER_V1:
                    break
            else:
                return None, None
            
            length = self.i2c.readfrom(self.address, 1)[0]
            command = self.i2c.readfrom(self.address, 1)[0]
            payload = self.i2c.readfrom(self.address, length) if length else b""
            checksum = self.i2c.readfrom(self.address, 1)[0]
            
            if checksum != self._checksum(HEADER_V1 + bytes([length, command]) + payload):
                return None, None
            return command, payload
        except:
            return None, None
    
    # V2-specific protocol
    def _cmd_v2(self, command, algorithm=0, content=None):
        packet = bytearray([0x55, 0xAA, command, algorithm, len(content) if content else 0])
        if content:
            packet.extend(content)
        packet.append(self._checksum(packet))
        self._write(bytes(packet))
    
    def _read_v2(self):
        # Read V2 packet
        try:
            header = self.i2c.readfrom(self.address, 5)
            if len(header) == 5 and header[0] == 0x55 and header[1] == 0xAA:
                size = header[4]
                rest = self.i2c.readfrom(self.address, size + 1)
                return header + rest
        except:
            pass
        return None
    
    # Public API
    def knock(self):
        """Test connection. Returns True if connected."""
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
                    resp = self.i2c.readfrom(self.address, 6)
                    if len(resp) >= 3 and resp[0] == 0x55 and resp[1] == 0xAA and resp[2] == CMD_RETURN_OK_V2:
                        self.connected = True
                        return True
                except:
                    pass
                time.sleep_ms(50)
        self.connected = False
        return False
    
    def set_alg(self, algorithm=None):
        """Switch algorithm. If None, uses current_algorithm."""
        if algorithm is None:
            algorithm = self.current_algorithm
        
        if algorithm == self.current_algorithm and self.version == 2:
            return True  # V2 doesn't need to resend
        
        if self.version == 1:
            self._cmd_v1(CMD_REQUEST_ALGORITHM, struct.pack("h", algorithm))
            result = self._check_ok()
        else:  # V2
            content = bytearray([algorithm, 0])
            content.extend(struct.pack('<hhhh', 0, 0, 0, 0))
            self._cmd_v2(CMD_SET_ALGORITHM_V2, 0, content)
            result = self._check_ok()
        
        if result:
            self.current_algorithm = algorithm
        return result
    
    def set_multi_alg(self, *algorithms):
        """Set multiple algorithms (V2 only). Pass 2-5 algorithm constants."""
        if self.version != 2:
            if self.debug: print("Multi-algorithm only on V2")
            return False
        
        algos = [a for a in algorithms if a is not None]
        if len(algos) < 2 or len(algos) > 5:
            if self.debug: print("Need 2-5 algorithms")
            return False
        
        content = bytearray([len(algos), 0])
        for i in range(max(4, len(algos))):
            content.extend(struct.pack('<h', algos[i] if i < len(algos) else 0))
        
        self._cmd_v2(CMD_SET_MULTI_ALGORITHM_V2, 0, content)
        return self._check_ok()
    
    def set_multi_alg_ratio(self, *ratios):
        """Set multi-algorithm ratios (V2 only). Pass 2-5 ratio values."""
        if self.version != 2:
            return False
        
        r = [x for x in ratios if x >= 0]
        if len(r) < 2:
            return False
        
        content = bytearray([len(r), 0])
        for i in range(max(4, len(r))):
            content.extend(struct.pack('<h', r[i] if i < len(r) else 0))
        
        self._cmd_v2(CMD_SET_MULTI_ALGORITHM_RATIO_V2, 0, content)
        return self._check_ok()
    
    def get_version(self):
        """Get firmware version string."""
        if self.version == 1:
            self._cmd_v1(CMD_REQUEST_FIRMWARE_VERSION)
            cmd, payload = self._read_v1()
            if payload:
                try:
                    return payload.decode('utf-8')
                except:
                    return str(payload)
            return None
        else:  # V2
            if self.debug: print("get_version not implemented for V2")
            return None
    
    def get(self, algorithm=None, ID=None, learned=False):
        """Get all blocks and arrows. Returns {'blocks': [...], 'arrows': [...]}"""
        if algorithm is None:
            algorithm = self.current_algorithm
        
        blocks, arrows = [], []
        
        if self.version == 1:
            if ID is not None:
                self._cmd_v1(CMD_REQUEST_BY_ID, struct.pack("h", ID))
            elif learned:
                self._cmd_v1(CMD_REQUEST_LEARNED)
            else:
                self._cmd_v1(CMD_REQUEST)
            
            cmd, info = self._read_v1()
            if cmd == CMD_RETURN_INFO:
                try:
                    n_objs = struct.unpack("h", info[:2])[0]
                except:
                    n_objs = 0
                
                for _ in range(n_objs):
                    cmd, data = self._read_v1()
                    if cmd == CMD_RETURN_BLOCK:
                        blocks.append(Block(*struct.unpack("hhhhh", data)))
                    elif cmd == CMD_RETURN_ARROW:
                        arrows.append(Arrow(*struct.unpack("hhhhh", data)))
        
        else:  # V2
            self._flush()
            self._cmd_v2(CMD_GET_RESULT_V2, algorithm)
            time.sleep_ms(50)  # Reduced from 100ms
            
            info = self._read_v2()
            if info and info[2] == CMD_RETURN_INFO_V2:
                n_results = struct.unpack('<h', info[7:9])[0]
                
                for _ in range(n_results):
                    time.sleep_ms(10)  # Reduced from 50ms
                    pkt = self._read_v2()
                    if not pkt:
                        continue
                    
                    obj = self._parse_v2(pkt, algorithm)
                    if obj:
                        if obj.type in ("BLOCK", "FACE", "HAND", "POSE"):
                            blocks.append(obj)
                        elif obj.type == "ARROW":
                            arrows.append(obj)
            
            # Only flush at the end
            self._flush()
        
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
        # Parse V2 result packet with algorithm-specific handling
        # Packet structure from Result.cpp:
        # [0:2] Header (0x55 0xAA)
        # [2] Command (0x43=BLOCK, 0x44=ARROW)
        # [3] Algorithm ID
        # [4] Content size
        # [5] ID (int8)
        # [6] Level/Confidence (int8)
        # [7:9] First/xCenter (int16 little-endian)
        # [9:11] Second/yCenter (int16 little-endian)
        # [11:13] Third/width (int16 little-endian)
        # [13:15] Fourth/height (int16 little-endian)
        # [15+] Payload: String_t structures and extended data
        
        if len(data) < 15:
            return None
        
        cmd = data[2]
        size = data[4]
        if size < 10:
            return None
        
        # Parse basic PacketData_t structure
        ID = struct.unpack('b', data[5:6])[0]
        conf = struct.unpack('b', data[6:7])[0]
        x = struct.unpack('<h', data[7:9])[0]
        y = struct.unpack('<h', data[9:11])[0]
        w = struct.unpack('<h', data[11:13])[0]
        h = struct.unpack('<h', data[13:15])[0]
        
        # Parse payload: String_t for name and content
        # String_t structure: uint8_t length, followed by data
        name, content = "", ""
        offset = 15
        
        # Check if we have string data
        if size > 10 and len(data) > offset:
            try:
                # First String_t: name
                name_len = data[offset]
                offset += 1
                if name_len > 0 and len(data) >= offset + name_len:
                    try:
                        name = data[offset:offset+name_len].decode('utf-8')
                    except:
                        name = str(data[offset:offset+name_len])  # Fallback for bad UTF-8
                    offset += name_len
                
                # Second String_t: content
                if len(data) > offset:
                    content_len = data[offset]
                    offset += 1
                    if content_len > 0 and len(data) >= offset + content_len:
                        try:
                            content = data[offset:offset+content_len].decode('utf-8')
                        except:
                            content = str(data[offset:offset+content_len])  # Fallback
                        offset += content_len
            except Exception as e:
                if self.debug: print(f"String parse error: {e}")
        
        # Parse extended keypoints for special algorithms (after strings)
        keypoints = []
        if len(data) > offset + 1:  # +1 for checksum
            try:
                remaining = (len(data) - offset - 1) // 2  # -1 for checksum, //2 for int16s
                for i in range(remaining):
                    if offset + 2 <= len(data) - 1:
                        kp = struct.unpack('<h', data[offset:offset+2])[0]
                        keypoints.append(kp)
                        offset += 2
            except Exception as e:
                if self.debug: print(f"Keypoint parse error: {e}")
        
        # Return appropriate class based on algorithm
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
        
        return None
    
    def draw_text(self, text, x=10, y=10, color=COLOR_WHITE):
        """Draw text on screen."""
        if self.version == 1:
            params = bytearray(len(text) + 4)
            params[0] = len(text)
            params[1] = 0 if x <= 255 else 0xFF
            params[2] = x % 255
            params[3] = y
            try:
                params[4:] = text.encode('utf-8')
            except:
                params[4:] = text.encode()
            self._cmd_v1(CMD_REQUEST_CUSTOM_TEXT, params)
            return self._check_ok()
        else:  # V2
            content = bytearray([color, 0])
            content.extend(struct.pack('<hhhh', x, y, 0, 0))
            try:
                txt = text.encode('utf-8')
            except:
                txt = text.encode()
            content.append(len(txt))
            content.extend(txt)
            self._cmd_v2(CMD_ACTION_DRAW_TEXT_V2, 0, content)
            return self._check_ok()
    
    def clear_text(self):
        """Clear text from screen."""
        if self.version == 1:
            self._cmd_v1(CMD_REQUEST_CLEAR_TEXT)
        else:
            self._cmd_v2(CMD_ACTION_CLEAR_TEXT_V2, 0)
        return self._check_ok()
    
    def draw_rect(self, x1, y1, x2, y2, color=COLOR_WHITE):
        """Draw rectangle (V2 only)."""
        if self.version != 2:
            return False
        content = bytearray([color, 0])
        content.extend(struct.pack('<hhhh', x1, y1, x2, y2))
        self._cmd_v2(CMD_ACTION_DRAW_RECT_V2, 0, content)
        return self._check_ok()
    
    def clear_rect(self):
        """Clear rectangles (V2 only)."""
        if self.version != 2:
            return False
        self._cmd_v2(CMD_ACTION_CLEAN_RECT_V2, 0)
        return self._check_ok()


# Demo program
if __name__ == "__main__":
    print("=" * 60)
    print("HuskyLens Demo - Connect, Version, Text, Detection")
    print("=" * 60)
    
    # Initialize I2C
    i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=100000)
    hl = HuskyLens(i2c, debug=True)
    
    if not hl.version:
        print("\n✗ No HuskyLens found!")
        print(f"I2C devices: {[hex(d) for d in i2c.scan()]}")
    else:
        print(f"\n✓ Found HuskyLens V{hl.version}\n")
        
        # Step 1: Knock (connect)
        print("Step 1: Testing connection...")
        if hl.knock():
            print("✓ Connected!\n")
        else:
            print("✗ Connection failed!")
            raise SystemExit
        
        # Step 2: Get firmware version
        print("Step 2: Getting firmware version...")
        version = hl.get_version()
        if version:
            print(f"✓ Firmware: {version}\n")
        else:
            print("✗ Could not get version (may not be supported)\n")
        
        # Step 3: Write "Hello" on screen
        print("Step 3: Writing 'Hello' to screen...")
        if hl.draw_text("Hello", x=50, y=50, color=COLOR_GREEN):
            print("✓ Text displayed!\n")
            time.sleep(2)
            hl.clear_text()
        else:
            print("✗ Text display failed\n")
        
        # Step 4: Set algorithm to Object Recognition
        print("Step 4: Setting algorithm to Object Recognition...")
        if hl.set_alg(ALGORITHM_OBJECT_RECOGNITION):
            print("✓ Algorithm set!\n")
        else:
            print("✗ Algorithm switch failed\n")
        
        # Step 5: Get object detection results
        print("Step 5: Getting object recognition results...")
        blocks = hl.get_blocks()
        
        if blocks:
            print(f"✓ Found {len(blocks)} object(s):\n")
            for i, block in enumerate(blocks, 1):
                print(f"  Object {i}:")
                print(f"    Position: ({block.x}, {block.y})")
                print(f"    Size: {block.width}×{block.height}")
                print(f"    ID: {block.ID} {'(learned)' if block.learned else '(not learned)'}")
                if hl.version == 2:
                    print(f"    Confidence: {block.confidence}")
                    if block.name:
                        print(f"    Name: {block.name}")
                    if block.content:
                        print(f"    Content: {block.content}")
                print()
        else:
            print("✗ No objects detected")
        
        # Step 6: Framerate test - Get 20 blocks as fast as possible
        print("\n" + "=" * 60)
        print("Step 6: Framerate test - Getting 20 blocks...")
        print("=" * 60 + "\n")
        
        import gc
        gc.collect()  # Free memory before test
        
        start_time = time.ticks_ms()
        successful_reads = 0
        total_blocks = 0
        
        for i in range(20):
            blocks = hl.get_blocks()
            if blocks:
                successful_reads += 1
                total_blocks += len(blocks)
        
        elapsed = time.ticks_diff(time.ticks_ms(), start_time)
        fps = 20000 / elapsed if elapsed > 0 else 0
        
        print(f"Results:")
        print(f"  Total time: {elapsed}ms")
        print(f"  Average per read: {elapsed/20:.1f}ms")
        print(f"  Framerate: {fps:.1f} FPS")
        print(f"  Successful reads: {successful_reads}/20")
        print(f"  Total blocks detected: {total_blocks}")
        print(f"  Avg blocks per read: {total_blocks/successful_reads:.1f}" if successful_reads > 0 else "")
        
        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)