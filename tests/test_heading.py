from unittest import TestCase, main
from mars_math import * 
import math

class HeadingFinder(TestCase): 
    def test(self): 
       d = radial_sim(0, 2 * math.pi) 
       print "d", d
       assert d >= 0.95
       d = radial_sim(0, math.pi) 
       assert d <= .05, d

if __name__ == '__main__':
    main() 

