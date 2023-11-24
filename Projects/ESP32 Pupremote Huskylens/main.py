# Copy this file to the LMS-ESP32 with Thonny and name it main.py
# Copy pupremote.py and lpf2.py to the LMS-ESP32 with Thonny
# Connect the LMS-ESP32 to the SPIKE Prime hub though port A
# Run this program on the LMS-ESP32 by rebooting it (ctrl-D in Thonny)


### Setup pupremote code
from pupremote import  PUPRemoteSensor, SPIKE_ULTRASONIC
from time import ticks_ms, sleep_ms
from pyhuskylens import HuskyLens
from machine import SoftI2C, Pin

# Connect huskylens to LMS-ESP32 like this: 
# 5V (red line)
# GND (black line)
# IO2 (blue line)
# IO26 (green line)
i2c = SoftI2C(scl=Pin(2), sda=Pin(26))

hlens = HuskyLens(i2c)

def hl(*argv):
    global hlens
    if argv:
        print(hlens.set_alg(argv[0]))
        print(hlens.knock())
            
    else:
        blocks = hlens.get_blocks()
        if blocks:
            return (blocks[0].x,
            blocks[0].y,
            blocks[0].width,
            blocks[0].height,
            blocks[0].ID)

def msg(*argv):
    if argv!=():
        print(argv)
    sleep_ms(500)
    return str(value)

value=0
def num(*argv):
    global value
    if argv!=():
        print(argv)
    else:
        print("num called without args")
    value += 1
    return 2*value,-3*value,4*value

sm_data=None
def sdata(*argv):
    global sm_data
    if argv!=():
        print(argv)
        sm_data = argv
    else:
        print("smalldata() called without args")
    return sm_data

# 32 bytes crashes the connection somehow.
lg_data=tuple(range(32))
def ldata(*argv):
    global lg_data
    if argv!=():
        print(argv)
        lg_data = argv
    else:
        print("largedata() called without args")
    
    return lg_data


p=PUPRemoteSensor(sensor_id=SPIKE_ULTRASONIC, power=False)
p.add_command('hl',from_hub_fmt="b", to_hub_fmt="hhhhB")
p.add_command('msg',"repr","repr")
p.add_command('num',from_hub_fmt="3b", to_hub_fmt="3b")
p.add_command('sdata',from_hub_fmt="16b", to_hub_fmt="16b")
p.add_command('ldata',from_hub_fmt="32B", to_hub_fmt="32B")
### End of pupremote setup code

### Main loop
while(True):
    connected=p.process()



