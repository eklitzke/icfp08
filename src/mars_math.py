import math

class Ellipse(object):
		self.b 	
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
