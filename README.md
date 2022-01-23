# LEGO Huskylens Library
The purpose of this library is to allow connecting LEGO robots to the Huskylens. 
It uses MicroPython and should work on LEGO MINDSTORMS EV3, LEGO SPIKE Prime, and LEGO MINDSTORMS 51515 Robot Inventor.

![Huskylens with LEGO SPIKE Prime](huskylens_lego.jpg)

# Installation

## SPIKE and Robot Inventor 51515
   1. Create a new Python project
   2. Paste the script from [Library/SPIKEInstaller.py](https://github.com/antonvh/LEGO-HuskyLenslib/blob/master/Library/SPIKEInstaller.py)
   3. Run it once and discard the project
   4. Create another new project
   5. Paste the code from [Library/SPIKEBoilerplate.py](https://github.com/antonvh/LEGO-HuskyLenslib/blob/master/Library/SPIKEBoilerplate.py)
   6. Start coding

Alternatively, you can copy and paste the contents of [Library/pyhuskylens.py](Library/pyhuskylens.py) above your script.

To connect the Huskylens to your hub [use a breakout board](https://antonsmindstorms.com/product/uart-breakout-board-for-spike-and-ev3-openmv-compatible/) or solder the included huskeylens header/wires to a spare Wedo2plug pin 5 and 6 (ID1/ID2 lines) via UART to HusleyLens pin 2 and 1 (Rx/Tx) 

Further details on pinout and ID1/ID2 [here.](https://www.philohome.com/wedo2reverse/wedo2.htm) Details on the pinout of the HuskeyLens [here](https://wiki.dfrobot.com/HUSKYLENS_V1.0_SKU_SEN0305_SEN0336#target_3) (Pin1=Tx=Green Pin2=Rx=Blue)

Powering the Huskylens is done with a USB battery pack or LPF. ***Warning*** that using LPF-Motor(M1/M2 lines) the Huskeylens firmware 0.5+ and SPIKE/Robot Inventor The Huskylens will randomly crash during use, unless you power it over USB (example, USB battery pack). Either supply extra power or downgrade to [firmware](https://github.com/HuskyLens/HUSKYLENSUploader)0.4.7

# Spike/51515 Example code
``` python
from hub import button
from projects.mpy_robot_tools.pyhuskylens import HuskyLens, ALGORITHM_FACE_RECOGNITION

hl = HuskyLens('A', debug=False)

# This returns '.': OK and no payload on firmware 0.5.1 may not work on newer
print(hl.get_version())

# Show some text on screen
hl.clear_text()
hl.show_text("hello from SPIKE", position=(120,120))

print("Starting face recognition")
hl.set_alg(ALGORITHM_FACE_RECOGNITION)

while not button.right.is_pressed():
    # Get x/y loc of a face
    blocks = hl.get_blocks()
    if len(blocks) > 0:
        face_x = blocks[0].x
        face_y = blocks[0].y
        error_x = (face_x-155)
        error_y = (face_y-120)
        print('face found:', face_x,face_y)

```

# TODO
- Make EV3 example
- Implement loading and saving learned models
- Implement saving screenshots and pictures
