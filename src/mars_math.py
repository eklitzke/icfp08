import math

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
	def __init__(object, radians):
		self.radians = float(radians) / (2 * math.pi)
		self.degrees = self.radians * 180 / math.pi
	
	def __add__(self, theta):
		return Angle(self.radians + theta.radians)

	def invert(self):
		return Angle(-1 * self.radians)

class Vector(object):
	def __init__(self, s, angle, pos=None):
		self.s = float(s)

		self.angle = angle

		# aliases
		self.speed = self.s
		self.angle = self.thea
		
		self.pos = pos if pos is not None else Point(0, 0)

		self.vx = self.speed * math.cos(self.theta)
		self.vy = self.speed * math.cos(self.theta)

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
