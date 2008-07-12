from unittest import main, TestCase
import math
import mars_math

def is_left_turn(ang):
    return -math.pi <= ang.radians <= 0

def is_right_turn(ang):
    return 0 <= ang.radians <= math.pi

def make_vector(direction_in_degrees, x_pos, y_pos):
    rads = mars_math.to_radians(float(direction_in_degrees))
    return mars_math.Vector(mars_math.Point(x_pos, y_pos), 1, mars_math.Angle(rads))

def steer_to_origin(vec):
    return mars_math.steer_to_point(vec, 1, mars_math.Point(0.0, 0.0))

class TestTurning(TestCase): 
    "Try parsing the sample message from the manual"

    def test(self):
        # rover is at (5, 0) heading straight up. should turn left
        rover_vec = make_vector(90.0, 5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert is_left_turn(turn_angle)

        # rover is at (5, 0) heading straight down. should turn right
        rover_vec = make_vector(270.0, 5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert is_left_turn(turn_angle)

        # rover is at (-5, 0) heading straight up. should turn right
        rover_vec = make_vector(90.0, -5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert is_right_turn(turn_angle)

        # rover is at (-5, 0) heading straight down. should turn left
        rover_vec = make_vector(270.0, -5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert is_right_turn(turn_angle)


if __name__ == '__main__':
    main() 

# vim: et sw=4 ts=4
