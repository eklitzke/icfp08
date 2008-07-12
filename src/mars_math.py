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
