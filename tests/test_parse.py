from unittest import main, TestCase

from parse import *

sample_message = r"""T 3450 aL -234.040 811.100 47.5 8.450 b -220.000 750.000 12.000 m -240.000 812.000 90.0 9.100 ;"""

class TestParseSampleTelemetry(TestCase): 
    def test(self): 
        result = Telemetry.parse(sample_message)
        self.assertEquals(result['position'][0], -234.040)
        self.assertEquals(result['position'][1], 811.100)
        self.assertEquals(result['direction'], 47.5)
        self.assertEquals(result['velocity'], 8.45)

if __name__ == '__main__':
    main() 

