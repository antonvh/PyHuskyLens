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
Unless you power the HuskyLens with an extra power bank over USB, it will randomly crash during use. The problem is not with this Python library. Either supply extra power or downgrade to 0.4.7

## Mindstorms EV3
Todo.

# Example code
``` python
from projects.pyhuskylens import HuskyLens, ALGORITHM_FACE_RECOGNITION

hl = HuskyLens('E', debug=False)

print(hl.get_version())

# Show some text on screen
print("Clearing screen")
hl.clear_text()
print("Displaying text")
hl.show_text("hello from SPIKE", position=(120,120))
print("Starting face recognition")
hl.set_alg(ALGORITHM_FACE_RECOGNITION)
```

# TODO
- Implement loading and saving learned models
- Implement saving screenshots and pictures