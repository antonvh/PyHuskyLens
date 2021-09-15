from projects.pyhuskylens import HuskyLens, ALGORITHM_FACE_RECOGNITION, clamp_int
from hub import button

hl = HuskyLens('E', baud=9600, debug=False)

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
        speed_x = -100 if error_x > 0 else 100
        speed_y = 100 if error_y > 0 else -100
        port.A.motor.run_for_degrees(clamp_int(error_x*0.2), speed_x)
        port.B.motor.run_for_degrees(clamp_int(error_x*0.2), speed_x)
        port.F.motor.run_for_degrees(clamp_int(error_y*0.1), speed_y)

