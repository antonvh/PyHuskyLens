# Copy this file in a new Pybricks program.
# Also copy pupremote.py in a new Pybricks program with exactly that name.

from pybricks.parameters import Button, Color, Direction, Port, Side, Stop
from pupremote import PUPRemoteHub
from pybricks.tools import wait, StopWatch

p=PUPRemoteHub(Port.B)
p.add_command('hl',from_hub_fmt="b", to_hub_fmt="hhhhB")
COLOR_DETECT = 4

# Set Huskylens to color detect mode
print(p.call('hl',COLOR_DETECT))
while 1:
    # Print the blocks detected by Huskylens
    print(p.call('hl'))