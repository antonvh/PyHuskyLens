#!/usr/bin/env pybricks-micropython

# This program is for a robot with motors on ports b and c, 
# and a huskylens connected to port S1, in serial mode 9600 baud.
# On the huskylens 'learn' the line with the teach button.
# Then run this program to follow the learned line.

from pybricks.hubs import EV3Brick
from pybricks.ev3devices import (
    Motor,
    TouchSensor,
    ColorSensor,
    InfraredSensor,
    UltrasonicSensor,
    GyroSensor,
)
from pybricks.parameters import Port, Stop, Direction, Button, Color
from pybricks.tools import wait, StopWatch, DataLog
from pybricks.robotics import DriveBase
from pybricks.media.ev3dev import SoundFile, ImageFile
from pyhuskylens import HuskyLens, ALGORITHM_LINE_TRACKING

# This program requires LEGO EV3 MicroPython v2.0 or higher.
# Click "Open user guide" on the EV3 extension tab for more information.

# Create your objects here.
ev3 = EV3Brick()


# Write your program here.
ev3.speaker.beep()
print("Beep!")

hl = HuskyLens(Port.S1)

hl.set_alg(ALGORITHM_LINE_TRACKING)
ev3.speaker.beep()
hl.clear_text()
ev3.speaker.beep()
hl.show_text("EV3 connected")
ev3.speaker.beep()

lm = Motor(Port.B)
rm = Motor(Port.C)
db = DriveBase(lm, rm, 56, 150)

# db.straight(50)

while 1:
    data = hl.get_arrows(learned=True)
    # print(data)
    if len(data) > 0:
        head_off_center = data[0].x_head - 160
        tail_off_center = data[0].x_tail - 160
        steer = (head_off_center * 10 + tail_off_center * 6) / 16
        print(steer)
        db.drive(50,steer*.6)
    else:
        db.stop()
        
    
    
