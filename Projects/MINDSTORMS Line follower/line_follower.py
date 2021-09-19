from mindstorms import MSHub, Motor, MotorPair, ColorSensor, DistanceSensor, App
from mindstorms.control import wait_for_seconds, wait_until, Timer
from mindstorms.operator import greater_than, greater_than_or_equal_to, less_than, less_than_or_equal_to, equal_to, not_equal_to
import math

from projects.pyhuskylens import (HuskyLens, 
ALGORITHM_FACE_RECOGNITION, 
ALGORITHM_FACE_RECOGNITION,
ALGORITHM_OBJECT_TRACKING,
ALGORITHM_OBJECT_RECOGNITION,
ALGORITHM_LINE_TRACKING,
ALGORITHM_COLOR_RECOGNITION,
ALGORITHM_TAG_RECOGNITION,
ALGORITHM_OBJECT_CLASSIFICATION,
ALGORITHM_QR_CODE_RECOGNITION,
ALGORITHM_BARCODE_RECOGNITION, 
ARROWS, # key for get() dict
BLOCKS, # key for get() dict
FRAME, # key for get() dict
clamp_int)

### huskylens usage ###
# get_blocks(ID=None, learned=False) returns a list of block objects
# blocks have x, y , width , height, ID properties.
# get_arrows(ID=None, learned=False) returns a list of arrow objects
# arrows have x_tail, y_tail , x_head , y_head, ID and direction properties

# get(ID=None, learned=False) returns a dict with blocks, arrows & frame

# on firmware 0.5+ you also have these class methods available:
# show_text("text", position=(10,10))
# clear_text()

# Create your objects here.
ms_hub = MSHub()
hl = HuskyLens('E', baud=9600)
ma = Motor('A')
mb = Motor('B')

# Write your program here.
ms_hub.speaker.beep()

# Get direction of a learned arrow
print("Starting line tracking")
hl.set_alg(ALGORITHM_LINE_TRACKING)
while not ms_hub.left_button.is_pressed():
    arrows = hl.get_arrows(learned=True)
    if len(arrows) > 0:
        direction = ((arrows[0].x_head+arrows[0].x_tail)/2 - 160)/-6
        ma.start_at_power(clamp_int(30+direction))
        mb.start_at_power(clamp_int(-30+direction))
    else:
        ma.start_at_power(0)
        mb.start_at_power(0)
ma.start_at_power(0)
mb.start_at_power(0)
