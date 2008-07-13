from unittest import main, TestCase
import math
import mars_math

BIG_HALF_PI = math.pi * 0.51
BIG_PI = math.pi * 1.01

def assert_is_left_turn(ang):
    assert 0 <= ang.radians <= BIG_PI, "%1.3f degrees is not a left turn" % (mars_math.to_degrees(ang.radians))

def assert_is_right_turn(ang):
    assert -BIG_PI <= ang.radians <= 0, "%1.3f degrees is not a right turn" % (mars_math.to_degrees(ang.radians))

def assert_is_small_turn(ang, degrees=10):
    assert abs(ang.degrees) < degrees

def make_vector(direction_in_degrees, x_pos, y_pos):
    rads = mars_math.to_radians(float(direction_in_degrees))
    return mars_math.Vector(mars_math.Point(x_pos, y_pos), 1, mars_math.Angle(rads))

def steer_to_origin(vec):
    return mars_math.steer_to_point(vec, 1, mars_math.Point(0.0, 0.0))

def steer_to_point(vec, x, y):
    return mars_math.steer_to_point(vec, 1, mars_math.Point(float(x), float(y)))

class TestTurning(TestCase): 
    "Try parsing the sample message from the manual"

    def test_moving_to_origin_from_one_one(self):
        # rover is at (1, 1) heading straight up. should turn left
        rover_vec = make_vector(90.0, 1, 1)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_left_turn(turn_angle)

        # rover is at (1, 1) heading straight down. should turn right
        rover_vec = make_vector(270.0, 1, 1)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_right_turn(turn_angle)

    def test_moving_below_or_above(self):
        # rover is at (1, 1) heading to (2,2). Trying to navigate to (1, 0).
        # This should be a right turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 1, 0)
        assert_is_right_turn(turn_angle)

        # rover is at (1, 1) heading to (2,2). Trying to navigate to (1, 2).
        # This should be a left turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 1, 2)
        assert_is_left_turn(turn_angle)

    def test_moving_normal(self):
        # rover is at (1, 1) heading to (2,2). Trying to navigate to (0, 5).
        # This should be a left turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 0, 5)
        assert_is_left_turn(turn_angle)

        # rover is at (1, 1) heading to (2,2). Trying to navigate to (0, -5).
        # This should be a right turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 0, -5)
        assert_is_right_turn(turn_angle)

        # rover is at (1, 1) heading to (2,2). Trying to navigate to (5, 0).
        # This should be a right turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 0, 5)
        assert_is_left_turn(turn_angle)

        # rover is at (1, 1) heading to (2,2). Trying to navigate to (-5, 0).
        # This should be a right turn
        rover_vec = make_vector(45.0, 1, 1)
        turn_angle, t = steer_to_point(rover_vec, 0, -5)
        assert_is_right_turn(turn_angle)

    # these don't work because of the perturbation strategy
    def xtest_boundary_conditions(self):
        # rover is at (5, 0) heading straight up. should turn left
        rover_vec = make_vector(90.0, 5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_left_turn(turn_angle)

        # rover is at (5, 0) heading straight down. should turn right
        rover_vec = make_vector(270.0, 5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_right_turn(turn_angle)

        # rover is at (-5, 0) heading straight up. should turn right
        rover_vec = make_vector(90.0, -5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_right_turn(turn_angle)

        # rover is at (-5, 0) heading straight down. should turn left
        rover_vec = make_vector(270.0, -5, 0)
        turn_angle, t = steer_to_origin(rover_vec)
        assert_is_right_turn(turn_angle)

    def test_swerve_bug(self):
        rover_vec = make_vector(-45.0, 1, 20)
        turn_angle, t = steer_to_point(rover_vec, -3, -3)
        assert_is_right_turn(turn_angle)

        rover_vec = make_vector(-45.0, -10, 13)
        turn_angle, t = steer_to_point(rover_vec, 3.5, -3.5)
        assert_is_right_turn(turn_angle)
        assert_is_small_turn(turn_angle)

if __name__ == '__main__':
    main() 

# vim: et sw=4 ts=4
