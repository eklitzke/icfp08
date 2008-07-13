# The docs say the processing time is less than 20 milliseconds
#PROCESSING_TIME = 0.015
PROCESSING_TIME = 0.010

INTERVAL_SCALE = 0.95

# Number of degrees for a small angle... if the angle is smaller than this then
# the rover won't try to turn, to help keep the path straight
SMALL_ANGLE = 7.0

# Ensure that the rover isn't in a hard turn for this kind of angle
SOFT_ANGLE = 20.0

FORCE_TURN_DIST = 40.0

FORCE_TURN_SQ = FORCE_TURN_DIST ** 2
