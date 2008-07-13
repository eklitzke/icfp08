from unittest import TestCase, main
from mars_math import * 
import math

class VectorSim(TestCase): 
    def test(self): 
       d = vector_sim(0, 2 * math.pi) 
       assert d >= 0.95
       d = vector_sim(0, math.pi) 
       assert d <= .05, d

class FindHeading(TestCase): 
    def test(self): 
        start = Point(-5, 0)
        result = find_heading(start, [], 360)
        assert (result % (2 * math.pi)) <= 0.01, result

if __name__ == '__main__':
    main() 
