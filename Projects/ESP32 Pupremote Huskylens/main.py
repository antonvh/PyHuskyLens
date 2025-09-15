# Copy this file to the LMS-ESP32 with ViperIDE and name it main.py
# Connect the LMS-ESP32 to the SPIKE Prime hub though port A
# Run this program on the LMS-ESP32

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

# Initialize i2c. Timeout is 2000 microseconds, because PUPremote balks if a
# function hangs much longer.
i2c = SoftI2C(scl=Pin(2), sda=Pin(26), timeout=2000)

hlens = HuskyLens(i2c)

def hl(*argv):
    global hlens
    if argv:
        # Pybricks tries to set a mode. Let's pass it on with set_alg()
        if not hlens.set_alg(argv[0]):
            # There was a problem setting the mode. Return id -1
            return (0,0,0,0,-1)
            
    else:
        # No mode asked, just get identified blocks.
        blocks = hlens.get_blocks()
        if blocks:
            return (blocks[0].x,
            blocks[0].y,
            blocks[0].width,
            blocks[0].height,
            blocks[0].ID)
        else:
            # No blocks found, return all zeroes.
            return (0,0,0,0,0)

p=PUPRemoteSensor(sensor_id=SPIKE_ULTRASONIC, power=False)
p.add_command('hl',from_hub_fmt="b", to_hub_fmt="hhhhB")
### End of pupremote setup code

### Main loop
while(True):
    connected=p.process()



