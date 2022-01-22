# LEGO Huskylens Library
The purpose of this library is to connect LEGO robots to the Huskylens. It uses MicroPython and should work on LEGO MINDSTORMS EV3, LEGO SPIKE Prime, and LEGO MINDSTORMS Robot Inventor.

![Huskylens with LEGO SPIKE Prime](huskylens_lego.jpg)

# Installation
## SPIKE and Robot Inventor
1. Create a new Python project
2. Paste the script from Library/SPIKEInstaller.py
3. Run it once and discard the project
4. Create another new project
5. Paste the code from Library/SPIKEBoilerplate.py
6. Start coding

Alternatively, you can copy and paste the contents of [Library/pyhuskylens.py](Library/pyhuskylens.py) above your script.

To connect the Huskylens to your hub [use a breakout board](https://antonsmindstorms.com/product/uart-breakout-board-for-spike-and-ev3-openmv-compatible/) or [solder the included cable to a spare Wedo wire](#)

## Warning for Huskylens firmware 0.5+ and SPIKE/Robot Inventor##
The Huskylens will randomly crash during use unless you power it over USB. Either supply extra power or downgrade to 0.4.7

## Mindstorms EV3
Todo.

# Example code
``` python
from hub import button
from projects.mpy_robot_tools.pyhuskylens import HuskyLens, ALGORITHM_FACE_RECOGNITION

hl = HuskyLens('A', debug=False)

# This returns '.': OK and no payload on firmware 0.5.1 may not work on newer
print(hl.get_version())

# Show some text on screen
hl.clear_text()
hl.show_text("hello from SPIKE", position=(120,120))

# Get x/y loc of a face
print("Starting face recognition")
hl.set_alg(ALGORITHM_FACE_RECOGNITION)

while not button.right.is_pressed():
    blocks = hl.get_blocks()
    if len(blocks) > 0:
        face_x = blocks[0].x
        face_y = blocks[0].y
        error_x = (face_x-155)
        error_y = (face_y-120)
        print('face found:', face_x,face_y)

```

# TODO
- Implement loading and saving learned models
- Implement saving screenshots and pictures
