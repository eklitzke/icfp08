import math

def to_radians(deg):
    return deg / 180.0 * math.pi

def normalize_turn_angle(rads):
    while rads > math.pi:
        rads = -2 * math.pi + rads
    while rads < (-math.pi):
        rads = 2 * math.pi + rads
    return rads

class Ellipse(object):
    '''Given the min/max start parameters sent by the server, calculates the
    ellipse constants as seen in
    http://upload.wikimedia.org/wikipedia/commons/2/24/Elipse.svg'''

    def __init__(min, max):
        self.a = (min + max) / 2.0
        self.ecc = (max / self.a) - 1.0 # same as e
        self.b = math.sqrt(self.ecc**2 - self.a**2)
        self.e = self.ecc

        self.min = min
        self.max = max

class Point(object):
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

    def add(p):
        return Point(self.x + p.x, self.y + p.y)

    def norm(self):
        return math.sqrt(self.x**2 + self.y**2)

class Angle(object):
    def __init__(self, radians):
        self.radians = radians
        self.degrees = self.radians * 180 / math.pi
    
    def __add__(self, theta):
        return Angle(self.radians + theta.radians)

    def invert(self):
        return Angle(-1 * self.radians)

class TurnAngle(Angle):
    def __init__(self, radians):
        radians = normalize_turn_angle(radians)
        super(TurnAngle, self).__init__(radians)

class Vector(object):
    def __init__(self, pos, speed, angle):
        self.pos = pos
        self.speed = float(speed)
        self.angle = angle

        self.vx = self.speed * math.cos(self.angle.radians)
        self.vy = self.speed * math.cos(self.angle.radians)

    def future_position(self, t):
        vec = Point(self.vx * t, self.vy * t)
        return self.pos.add(vec)

# terminal velocity = sqrt ( a / k)
#
# dt should be the time for the first telemetry update, v should be the
# velocity at that time, and tv should be the terminal velocity sent in the
# intitial message. This will calculate the acceleration coefficient a and the
# drag coefficient k
def calculate_coefficients(dt, v, tv):
    a = float(v) / (dt**2) # need to go back and redo this right with calculus
    k = a / (tv**2)
    return a, k

# FIXME: this is for figuring out martian triangles
def predicted_path(vec, omega, dt):
    '''omega is the guess of the maximum angular velocity of the object over
    the time interval, vec should be a Vector, dt is the time interval that
    we're interested in measuring over.'''

    straight_point = vec.future_position(dt)

    # FIXME: this approximation only works if dt is small, but it can be
    # exactly computed if i spend a little bit more work to figure out the
    # right equation... This is an overestimate.

    # omega should be radians / second
    angle = Angle(abs(omega) * dt)
    right_angle = vec.angle + angle
    left_angle = vec.angle + angle.invert()

    leg_distance = math.sin(angle.radians) * vec.speed * dt

def angle_points_right(angle):
    half_pi = 0.5 * math.pi
    if -half_pi <= angle.radians <= half_pi:
        return True
    if angle.radians >= (math.pi + half_pi):
        return True
    return False

def angle_points_left(angle):
    return not angle_points_right(angle)

def steer_to_point(rover_vec, omega, dest):
    '''rover_vec is a vector representing the rover.
    turning params describes how well the rover can turn
    dest is the point we're trying to navigate to.'''

    # set the origin at the rover
    y_prime = dest.y - rover_vec.pos.y
    x_prime = dest.x - rover_vec.pos.x

    dest_prime = Point(x_prime, y_prime)

    if abs(x_prime) <= 0.01:
        # need to navigate straight up or down
        if y_prime < 0:
            if angle_points_right(rover_vec.angle):
                # do a right turn
                turning_angle = rover_vec.angle.radians + (math.pi * 0.5)
                t = turning_angle / omega
                return TurnAngle(turning_angle), t
            else:
                # do a left turn
                turning_angle = (1.5 * math.pi) - rover_vec.angle.radians
                t = turning_angle / omega
                return TurnAngle(turning_angle), t
        else:
            if angle_points_right(rover_vec.angle):
                # do a left turn
                turning_angle = (math.pi * 0.5) - rover_vec.angle.radians
                t = turning_angle / omega
                return TurnAngle(turning_angle), t
            else:
                # do a righ turn
                turning_angle = rover_vec.angle.radians - (math.pi * 0.5)
                t = turning_angle / omega
                return TurnAngle(turning_angle), t
    elif abs(y_prime) <= 0.001:
        if x_prime < 0:
            # need to turn west
            turning_angle = math.pi - rover_vec.angle.radians
            t = turning_angle / omega
            return TurnAngle(turning_angle), t
        else:
            # need to turn east
            turning_angle = -rover_vec.angle.radians
            t = turning_angle / omega
            return TurnAngle(turning_angle), t
    else:
        turning_angle = math.atan(y_prime / x_prime)
    print 'turning angle init %s' % turning_angle
    print 'y, x = %s %s' % (y_prime, x_prime)

    ny, nx = math.sin(turning_angle), math.cos(turning_angle)
    if (ny * y_prime < 0):
        turning_angle += math.pi
        ny, nx = math.sin(turning_angle), math.cos(turning_angle)
    print 'ny, nx = %s %s' % (ny, nx)
    #if (y_prime > 0) and (x_prime < 0): turning_angle -= math.pi
    #turning_angle = math.atan(y_prime / x_prime) - turning_angle


    if (ny > 0) and (nx < 0):
        turning_angle -= math.pi

    if turning_angle >= math.pi:
        turning_angle -= (2 * math.pi)
    
    # Right now the turning angle represents the angle from the rover to the
    # origin
    print 'ANGLE TO DEST IS %s, MY DIRECTION IS %s' % (turning_angle,
            rover_vec.angle.radians)

    # Adjust the turn angle to take into account the rover vector
    turning_angle -= rover_vec.angle.radians
    t = abs(turning_angle / omega)
    return TurnAngle(turning_angle), t

# vim: et ts=4 sw=4
