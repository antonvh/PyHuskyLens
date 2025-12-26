"""
PyHuskyLens Quick Start Example for SPIKE/MINDSTORMS
This example shows basic usage after installation
"""

from pyhuskylens import *
from hub import port
from time import sleep_ms

# Connect HuskyLens to port E using I2C
hl = HuskyLens(port.E)

print("Connecting to HuskyLens...")
if hl.knock():
    print("Connected!")

    # Set to object recognition mode
    hl.set_alg(ALGORITHM_OBJECT_RECOGNITION)
    print("Algorithm set to Object Recognition")

    # Display message on HuskyLens screen
    hl.show_text("Hello SPIKE!", position=(50, 50), color=COLOR_GREEN)

    # Detect objects for 10 seconds
    print("\nLooking for objects...")
    for i in range(20):
        blocks = hl.get_blocks()
        if blocks:
            print(f"Found {len(blocks)} object(s):")
            for block in blocks:
                print(f"  - Object {block.ID} at ({block.x}, {block.y})")
        else:
            print("No objects detected")
        sleep_ms(500)

    print("\nDemo complete!")
else:
    print("ERROR: Cannot connect to HuskyLens")
    print("Check connections and try again")
