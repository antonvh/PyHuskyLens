__author__ = "Anton Vanhoucke & Ste7an"
__copyright__ = "Copyright 2023, AntonsMindstorms.com"
__license__ = "GPL"
__version__ = "1.0.1"
__status__ = "Production"

try:
    import ustruct as struct
except ImportError:
    import struct

try:
    from pybricks.iodevices import PUPDevice
    from pybricks.tools import wait
except:
    # We surely aren't on pybricks.
    class PUPDevice:
        def __init__(self, port):
            pass
        def read(self, mode):
            pass
        def write(self, mode, data):
            pass
    def wait(ms):
        pass
    # Pybricks has no time module, so here it's safe to import
    try:
        from time import ticks_ms
    except:
        from time import time as time_s
        def ticks_ms():
            return round(time_s()*1000)

try:
    from micropython import const
except ImportError:
    # micropython.const() is not available on normal Python
    # but we can use a normal function instead for unit tests
    def const(x):
        return x



MAX_PKT     = const(32)

#: OpenMV board platform type
OPENMV      = const(0)
#: LMS-ESP32 board platform type
ESP32       = const(1)

# Dictionary keys
NAME        = const(0)
SIZE        = const(1)
TO_HUB_FORMAT      = const(2)
FROM_HUB_FORMAT    = const(3)
CALLABLE    = const(4)

#: WeDo Ultrasonic sensor id
WEDO_ULTRASONIC = const(35)
#: SPIKE Color sensor id
SPIKE_COLOR = const(61)
#: SPIKE Ultrasonic sensor id
SPIKE_ULTRASONIC = const(62)

CALLBACK = const(0)
CHANNEL = const(1)


class PUPRemote:
    """
    Base class for PUPRemoteHub and PUPRemoteSensor. Defines a list of commands
    and their formats. Contains encoding/decoding functions.
    """

    def __init__(self):
        # Store commands, size and format
        self.commands = []
        # Store mode names (commands) to look up their index
        self.modes = {}

    def add_channel(self, mode_name: str, to_hub_fmt: str =""):
        """
        Define a data channel to read on the hub. Use this function with identical parameters on both
        the sensor and the hub. You can call a channel like a command, but to update the data
        on the sensor side, you need to `update_channel(<name>, *args)`.

        :param mode_name: The name of the mode you defined on the sensor side.
        :type mode_name: str
        :param to_hub_fmt: The format string of the data sent from the sensor
            to the hub. Use 'repr' to receive any python object. Or use a struct format string,
            to receive a fixed size payload. See https://docs.python.org/3/library/struct.html

        :type to_hub_fmt: str
        """
        self.add_command(mode_name, to_hub_fmt=to_hub_fmt, command_type=CHANNEL)

    def add_command(
        self,
        mode_name: str,
        to_hub_fmt: str = "",
        from_hub_fmt: str = "",
        command_type=CALLBACK,
    ):
        """Define a remote call. Use this function with identical parameters on both
        the sensor and the hub.

        :param mode_name: The name of the mode you defined on the sensor side.
        :type mode_name: str
        :param to_hub_fmt: The format string of the data sent from the sensor
            to the hub. Use 'repr' to receive any python object. Or use a struct format string,
            to receive a fixed size payload. See https://docs.python.org/3/library/struct.html

        :type to_hub_fmt: str
        :param from_hub_fmt: The format string of the data sent from the hub
        :type from_hub_fmt: str

        """
        if to_hub_fmt == "repr" or from_hub_fmt == "repr":
            msg_size = MAX_PKT
        else:
            size_to_hub_fmt = struct.calcsize(to_hub_fmt)
            size_from_hub_fmt = struct.calcsize(from_hub_fmt)
            msg_size = max(size_to_hub_fmt,size_from_hub_fmt )

        self.commands.append(
            {
            NAME: mode_name,
            TO_HUB_FORMAT: to_hub_fmt,
            SIZE: msg_size,
            }
        )
        if command_type == CALLBACK:
            self.commands[-1][FROM_HUB_FORMAT] = from_hub_fmt
            # self.commands[-1][CALLABLE] = eval(mode_name)

        # Build a dictionary of mode names and their index
        self.modes[mode_name] = len(self.commands)-1

    def decode(self, fmt: str, data: bytes):
        if fmt == "repr":
            # Remove trailing zero's (b'\x00') and eval the string
            clean = bytearray( [c for c in data if c != 0] )
            if clean:
                return (eval(clean),)
            else:
                # Probably nothing left after stripping zero's
                return ('',)
            
        else:
            size = struct.calcsize(fmt)
            data = struct.unpack(fmt, data[:size])

        return data

    def encode(self, size, format, *argv):
        if format == "repr":
            s = bytes(repr(*argv), "UTF-8")
        else:
            s = struct.pack(format, *argv)

        assert len(s) <= size, "Payload exceeds maximum packet size"

        return s


class PUPRemoteSensor(PUPRemote):
    """
    Class to communicate with a PUPRemoteHub. Use this class on the sensor side,
    on any board that runs MicroPython. You can enable 8V power on the M+ wire,
    so the buck converter on the SPIKE-OPENMV or LMS-ESP32 board side can supply high
    currents (op to 1700mA) to your appliances.

    :param sensor_id: The id of the sensor of the sensor to emulate, defaults to 1.
    :type sensor_id: int
    :param power: Set to True if the PUPRemoteHub needs 8V power on M+ wire, defaults to False.
    :type power: bool
    :param platform: Set to ESP32 or OPENMV, defaults to ESP32.
    :type platform: int
    """

    try:
        import lpf2 as LPF2
    except:
        pass

    def __init__(self, sensor_id=1, power=False, platform=ESP32):
        super().__init__()
        self.connected = False
        self.power = power
        self.mode_names = []
        self.last_heartbeat = ticks_ms()
        self.heartbeat_interval = 20

        if platform == ESP32:
            self.lpup = self.LPF2.ESP_LPF2([],sensor_id=sensor_id)
        elif platform == OPENMV:
            self.lpup = self.LPF2.OpenMV_LPF2([],sensor_id=sensor_id)
        # self.lpup.set_call_back(self.call_back)

    def add_command(
        self,
        mode_name: str,
        to_hub_fmt: str = "",
        from_hub_fmt: str = "",
        command_type=CALLBACK,
    ):
        super().add_command(mode_name, to_hub_fmt, from_hub_fmt, command_type)
        writeable = 0
        if command_type == CALLBACK:
            self.commands[-1][CALLABLE] = eval(mode_name)
        if from_hub_fmt != "":
            writeable = self.LPF2.ABSOLUTE
        max_mode_name_len = 5 if self.power else MAX_PKT
        if len(mode_name) > max_mode_name_len:
            print(
                "Error: mode_name can't be longer than %d%s."
                % (max_mode_name_len, " if power=True" if self.power else "")
            )
        else:  # only enable power when len(mode_name)<=5
            if self.power:
                mode_name = (
                    mode_name.encode("ascii")
                    + b"\x00" * (5 - len(mode_name))
                    + b"\x00\x80\x00\x00\x00\x05\x04"
                )
        self.lpup.modes.append(
            self.lpup.mode(
                mode_name,
                self.commands[-1][SIZE], # This packet size of the last command we added (this one)
                self.LPF2.DATA8,
                writeable
                )
            )

    def process(self):
        """
        Process the commands. Call this function in your main loop, preferably at least once every 20ms.
        It will handle the communication with the LEGO Hub, connect to it if needed,
        and call the registered commands.

        :return: True if connected to the hub, False otherwise.
        """
        # Check if it's not to early to process a heartbeat
        if ticks_ms() - self.last_heartbeat < self.heartbeat_interval:
            return self.lpup.connected
        else:
            self.last_heartbeat = ticks_ms()
            
        # Get data from the hub and return previously stored payloads
        data = self.lpup.heartbeat()

        # Send data to the hub, by calling a function
        mode = self.lpup.current_mode
        if CALLABLE in self.commands[mode]:
            result = None
            if data is not None:
                args = self.decode(
                    self.commands[mode][FROM_HUB_FORMAT],
                    data
                    )
                result = self.commands[mode][CALLABLE](*args)

            else:
                try:
                    result = self.commands[mode][CALLABLE]()
                except TypeError:
                    # print("Error: function %s() needs arguments." % self.commands[mode][NAME])
                    pass

            if result is not None: # Allow for 0
                if not isinstance(result, tuple):
                    result = (result,)
                pl = self.encode(
                    self.commands[mode][SIZE],
                    self.commands[mode][TO_HUB_FORMAT],
                    *result
                    )
                self.lpup.send_payload(pl)
        else:
            # No callback. Just write the stored data from self.update_channel()
            self.lpup.writeIt(self.lpup.payloads[mode])

        return self.lpup.connected

    def update_channel(self, mode_name: str, *argv):
        mode = self.modes[mode_name]

        pl = self.encode(
            self.commands[mode][SIZE],
            self.commands[mode][TO_HUB_FORMAT],
            *argv
            )
        self.lpup.load_payload(pl, mode=mode)


class PUPRemoteHub(PUPRemote):
    """
    Class to communicate with a PUPRemoteSensor. Use this class on the hub side,
    on any hub that runs Pybricks. Copy the commands you defined on the sensor side
    to the hub side.

    :param port: The port to which the PUPRemoteSensor is connected.
    :type port: Port (Example: Port.A)
    :param power: Set to True if the PUPRemoteSensor needs 8V power on M+ wire.
    :type power: bool
    """

    def __init__(self, port):
        super().__init__()
        self.port = port
        try:
            self.pup_device = PUPDevice(port)
        except OSError:
            self.pup_device = None
            print("PUPDevice not ready on port", port)

    def call(self, mode_name: str, *argv, wait_ms=0):
        """
        Call a remote function on the sensor side with the mode_name you defined on both sides.

        :param mode_name: The name of the mode you defined on the sensor side.
        :type mode_name: str
        :param argv: As many arguments as you need to pass to the remote function.
        :type argv: Any
        :param wait_ms: The time to wait for the sensor to respond after
            a write from the hub, defaults to 100ms. This does not delay the read,
            i.e. when you don't pass any arguments, the read will happen immediately.
        :type wait_ms: int
        """
    
        mode = self.modes[mode_name]
        size = self.commands[mode][SIZE] 
        # Dummy read action to work around mode setting bug in Pybricks beta 2.2.0b8
        # Also check if a sensor or sensor emulator is connected.abs
        try:
            self.pup_device.read(mode)
        except:
            print("PUPRemote Error: Nothing connected or no script running on remote\n")
            return None

        if len(argv) > 0:
            payl = self.encode(
                size,
                self.commands[mode][FROM_HUB_FORMAT],
                *argv
                )
            self.pup_device.write(
                mode, 
                tuple(payl + b'\x00'*( size - len(payl)))
                )
            wait(wait_ms+size*1.5)

        data = self.pup_device.read(mode)
        size=len(data)
        raw_data = struct.pack('%db'%size,*data)
        result = self.decode(
            self.commands[mode][TO_HUB_FORMAT],
            raw_data)
        # Convert tuple size 1 to single value
        if len(result)==1: 
            return result[0]
        else:
            return result
