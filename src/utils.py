import sys
import logging

logging.basicConfig(level=logging.DEBUG, 
        format='%(asctime)s %(name)-15s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M', stream=sys.stderr)

