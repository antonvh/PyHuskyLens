#!/usr/bin/env pybricks-micropython

# This program is for a robot with motors on ports b and c,
# and a huskylens connected to port S1, in serial mode 9600 baud.
# On the huskylens 'learn' the line with the teach button.
# Then run this program to follow the learned line.

# Use VSCode with the MINDSTORMS extension to run it

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
hl = HuskyLens(Port.S1)
lm = Motor(Port.B)
rm = Motor(Port.C)
db = DriveBase(lm, rm, 56, 150)

# Initialize.
ev3.speaker.beep()
hl.set_alg(ALGORITHM_LINE_TRACKING)
hl.show_text("EV3 connected")

# Continuously read arrow data and steer accordingly.
while 1:
    arrow_list = hl.get_arrows(learned=True)
    # Test if the list of arrows contains at least one item.
    if len(arrow_list) > 0:
        arrow = arrow_list[0]
        head_off_center = arrow.x_head - 160
        tail_off_center = arrow.x_tail - 160
        # Steer the robot onto the line. The tail is more important than the head.
        steer = (head_off_center * 3 + tail_off_center * 10) / 13
        # Tune the speed values and steer multiplier for a stable run.
        db.drive(70, steer * 0.75)
    else:
        # No line to be seen. Stop the engines.
        db.stop()
