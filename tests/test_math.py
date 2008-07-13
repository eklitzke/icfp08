from unittest import main, TestCase
import math
import mars_math

class TestMarsMath(TestCase): 
    "Try parsing the sample message from the manual"

    def test_vector_sim(self):
        assert mars_math.vector_sim (0.01, -0.01) > 0.9
        assert mars_math.vector_sim (0.0, -math.pi) < 0.1

if __name__ == '__main__':
    main() 

# vim: et sw=4 ts=4
