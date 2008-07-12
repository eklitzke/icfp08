from unittest import main, TestCase
from message import Message


class TestParseSampleTelemetry(TestCase): 
    "Try parsing the sample message from the manual"

    sample_message = r"""T 3450 aL -234.040 811.100 47.5 8.450 b -220.000
    750.000 12.000 m -240.000 812.000 90.0 9.100 ;"""

    def test(self): 
        result = Message.parse(self.sample_message)
        assert result[0]['telemetry']
        tel = result[0]['telemetry']
        self.assertEquals(tel['position'][0], -234.040)
        self.assertEquals(tel['position'][1], 811.100)
        self.assertEquals(tel['direction'], 47.5)
        self.assertEquals(tel['velocity'], 8.45)

if __name__ == '__main__':
    main() 

