import math
import random

import sys
import constants
from message import * 

r = math.sin(math.pi / 4) * 5
BASE_POINTS = ((-5.0, 0.0), (0.0, 5.0), (5.0, 0.0), (-5.0, 0.0), (r, r), (r, -r), (-r, -r), (-r, r))
del r

def to_radians(deg):
    return deg / 180.0 * math.pi

def to_degrees(rad):
    return rad * 180.0 / math.pi

def normalize_turn_angle(rads):
    while rads > math.pi:
        rads = -2 * math.pi + rads
    while rads < (-math.pi):
        rads = 2 * math.pi + rads
    return rads

def is_right_turn(angle):
    return angle < 0

def is_left_turn(angle):
    return angle > 0

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

    def perturb(self, magnitude=0.1):
        new_x = random.random() * magnitude + self.x
        new_y = random.random() * magnitude + self.y
        return Point(new_x, new_y)

    def __repr__(self):
        return 'Point(%1.4f, %1.4f)' % (self.x, self.y)

    __str__ = __repr__

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

def prime_point(rover_vec, dest):
    y_prime = dest.y - rover_vec.pos.y
    x_prime = dest.x - rover_vec.pos.x
    return x_prime, y_prime, Point(x_prime, y_prime)

def edge_case(x, y):
    eps = 0.001
    return abs(x) <= eps or abs(y) <= eps


def direction(p1, p2, v=None):
    '''Return the direction from p1 to p2'''
    x = p2.x - p1.x
    y = p2.y - p1.y

    # these are boundary cases (surprisingly I really did have to add this
    # because it came up and I got a ZeroDivisionError)
    if x == 0 or y == 0:
        if not v:
            p1_prime = p1.perturb()
        else:
            p1_prime = Point(p1.x + v.vx * 0.1, p1.y + v.vy * 0.1)
        return direction(p1_prime, p2)

    theta = math.atan(y / x)

    ny = math.sin(theta)
    if (ny * y < 0):
        theta = theta + math.pi
    return theta

def distance(p1, p2): 
    return math.hypot(p1.x - p2.x, p1.y-p2.y)

def to_extent(point, radius): 
    """get the square extents around a radius"""
    big_radius = radius * constants.BLOAT # (bloat the object)
    minx, miny = point.x - big_radius, point.y - big_radius  
    maxx, maxy = point.x + big_radius, point.y + big_radius  
    return [Point(minx, miny),
            Point(minx, maxy),
            Point(maxx, miny),
            Point(maxx, maxy)]

class RadianRange(object): 
    def __init__(self, a, b): 
        self.a = a
        self.b = b

    def __contains__(self, x): 
        """Test if x is between a and b"""
        a = self.a
        b = self.b
        if a < b:
            return a <= x <= b
        else: 
            return a <= x <= (2 * math.pi) or 0 <= x <= b

    @classmethod
    def make_smallest_range(self, rads, bloat=False):
        m1 = min(rads)
        m2 = max(rads)
        if bloat:
            m1, m2 = constants.BLOAT * m1, constants.BLOAT * m2
        if (m2 - m1) <= math.pi:
            return RadianRange(m1, m2) 
        else:
            return RadianRange(m2, m1)

def min_vector_difference(d1, d2): 
    "find the smaller distance between two vectors"
    v1 = (d1 - d2) % (2.0 * math.pi)
    v2 = (d1 - d2) % (2.0 * math.pi)
    return min(v1, v2)

def vector_sim(d1, d2):
    """Find the similarity of two vectors"""
    d = min_vector_difference(d1, d2) / math.pi
    return 1.0 - d

def find_home_point(pos):

    # We want to steer for the furthest point on the origin. The reason is
    # if we have a situation like this:
    #
    #  ------------------>..--..
    #                   /       \
    #                  |    H    |
    #                   \       /
    #                    ',.__.'
    #
    # Where the arrow shows the trajectory of the rover, we really want to
    # be making a pretty hard right to make sure we don't shoot past the
    # target.

    # FIXME: it would be even better to take into account the direction of
    # motion (although this is pretty good already)

    distance_sq = pos.x**2 + pos.y**2

    # It's wasteful to optimize this when we're far away
    if distance_sq > (constants.FORCE_TURN_SQ):
        return Point(0.0, 0.0)

    # Sample 8 points around the circle:
    normsq = lambda (x, y): (pos.x - x)**2 + (pos.y - y)**2
    distances = [(pt, normsq(pt)) for pt in BASE_POINTS]
    return Point(*max(distances, key=lambda x: x[1])[0])

def get_origin_dir_and_distance(source_point):
    '''Auxilliary function used by find_heading, used to find the angle and
    distance to the origin. This is factored out this way to make some of the
    other functions more easily testable.'''
    origin = find_home_point(source_point)
    #origin = Point(0, 0)
    origin_dir = direction(source_point, origin)
    origin_distance = distance(source_point, origin)
    return origin_dir, origin_distance

def find_heading(source_vec, objects, samples=64, max_dist=20.0):
    """Find a direction (radians) that we should head to from source, given
    objects and samples

    Arguments:
        source_vec: the source vector
        objects -- a list of objects on the map
    """

    # Say there are n different possible headings we can take 0 ... i .. 2 pi
    # The best heading is the one that is not occluded and that is nearest our
    # destination, the origin

    origin_dir, origin_distance = get_origin_dir_and_distance(source_vec.pos)

    # this somehow prunes some of the objects out that aren't nearby
    object_ranges = []
    for obj in objects:
        if obj['kind'] == HOME:
            # we like home
            continue
        adj_obj_radius = (1.1 * obj['radius']) + 0.4
        extent_points = to_extent(obj['position'], adj_obj_radius)
        extent_distance = min(distance(source_vec.pos, p) for p in extent_points)
        # get rid of far away objects
        if extent_distance > origin_distance:
            continue
        if extent_distance > max_dist:
            continue
        extent_dirs = [direction(source_vec.pos, p, source_vec) for p in extent_points]
        score = extent_distance / max_dist
        assert score <= 1.0
        object_ranges.append((score, RadianRange.make_smallest_range(extent_dirs)))

    for score, obj_range in object_ranges:
        print >> sys.stderr, "OBJECTS:", score, to_degrees(obj_range.a), to_degrees(obj_range.b)
    else:
        print >> sys.stderr, "NO OBJECTS"

    def origin_score(direction):
        """return a score between 0 and 1 for how close the direction is toward the origin"""
        return vector_sim(direction, origin_dir)

    def occlusion_score(direction):
        """return a score between 0 and 1 for how occluded that direction is"""
        score = 1.0
        for obj_score, obj_range in object_ranges:
            if direction in obj_range:
                score = min(obj_score, score)
                break
        return score

    # We want the samples to be more densely packed in front of the rover than
    # behind

    THIRD_PI = math.pi / 3.0
    # Put 1/3 of them in the range -30 degrees to + 30 degrees
    front_samples = [THIRD_PI * (float(i) * 3 / samples) - (math.pi / 6.0) for i in range(samples / 3)]

    # Put another 1/2 in the range (-90 to -30) and (30 to 90)
    side_samples = [THIRD_PI * float(i) * 4 / samples + (math.pi / 6.0) for i in range (samples / 4)]
    side_samples += [-x for x in side_samples]

    # Put 1/6 behind the rover (TODO)
    directions = front_samples + side_samples
    directions = [d + source_vec.angle.radians for d in directions]

    #assert all(-91 <= to_degrees(d) <= 91 for d in directions)

    force_turn = any(occlusion_score(d) < 0.5 for d in front_samples if abs(to_degrees(d)) <= (constants.SMALL_ANGLE * constants.BLOAT))
    angle_score, angle = max(((occlusion_score(d) + origin_score(d), d) for d in directions), key=lambda x: x[0])

    print >> sys.stderr, "CHOOSING ANGLE:", to_degrees(angle)

    angle = TurnAngle(angle - source_vec.angle.radians)

    return angle, force_turn

def steer_to_angle(rover_vec, turn_state, turning_angle):
    turning_angle = normalize_turn_angle(turning_angle - rover_vec.angle.radians)
    #soft_turn, hard_turn, turn = turn_state
    #is_hard = (turn in ('r', 'R') and is_right_turn(turning_angle)) or (turn in ('l', 'L') and is_left_turn(turning_angle))
    #omega = hard_turn if is_hard else soft_turn
    #t = abs(turning_angle / omega)
    return TurnAngle(turning_angle) #, t

def steer_to_point(rover_vec, omega, dest):
    '''rover_vec is a vector representing the rover.
    turning params describes how well the rover can turn
    dest is the point we're trying to navigate to.'''

    rover_pos_copy = rover_vec.pos
    x_prime, y_prime, dest_prime = prime_point(rover_vec, dest)

    if edge_case(x_prime, y_prime):
        # move the point forward
        delta_t = 0.1 # FIXME: too small/large?
        new_x = rover_vec.pos.x + rover_vec.vx * delta_t
        new_y = rover_vec.pos.y + rover_vec.vy * delta_t

        rover_vec.pos = Point(new_x, new_y)
        x_prime, y_prime, dest_prime = prime_point(rover_vec, dest)
        while edge_case(x_prime, y_prime):
            rover_vec.pos = rover_pos_copy.perturb()
            new_x = rover_vec.pos.x + rover_vec.vx * delta_t
            new_y = rover_vec.pos.y + rover_vec.vy * delta_t
            rover_vec.pos = Point(new_x, new_y)
            x_prime, y_prime, dest_prime = prime_point(rover_vec, dest)

    turning_angle = math.atan(y_prime / x_prime)
    ny, nx = math.sin(turning_angle), math.cos(turning_angle)
    if (ny * y_prime < 0):
        turning_angle += math.pi
        ny, nx = math.sin(turning_angle), math.cos(turning_angle)
    #print '(nx, ny), angle = %s, %s' % ((nx, ny), turning_angle)

    if (x_prime * nx < 0) or (y_prime * ny < 0):
        print 'atan got fucked up: x, y = %s, nx, ny = %s' % ((x_prime, y_prime), (nx, ny))
        turning_angle = normalize_turn_angle(turning_angle + math.pi)

    # Adjust the turn angle to take into account the rover vector
    result = steer_to_angle(rover_vec, omega, turning_angle)
    rover_vec.pos = rover_pos_copy
    return result

# vim: et ts=4 sw=4
