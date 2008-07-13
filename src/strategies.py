'''Steering strategies'''

import math
import mars_math
from message import *
from constants import *
from twisted.internet import reactor

def basic_strategy(rover):
	turn_angle, t, origin_dist, force_turn = mars_math.find_heading(rover.vector, (rover.max_turn, rover.max_hard_turn, rover.turning), rover.map.objects)
	accel = rover.determineAcceleration(turn_angle)

	# turning angle should be in the range -pi to pi
	assert abs(turn_angle.radians < (math.pi * 1.01)), "Invalid turn angle %s" % turn_angle.radians

	# in this many milliseconds will send out another message reversing the
	# turn angle (i.e. to straighten out our path)

	# This is commented out because the processing time applies to
	# both the initial message and the straighten up message...
	#compensate_time = t - PROCESSING_TIME
	compensate_time = t

	# if the angle is small we should just keep moving forward
	if not force_turn and (abs(turn_angle.degrees) < SMALL_ANGLE) and (origin_dist > FORCE_TURN_DIST):
		if rover.turning == 'L' or (rover.turning == 'l' and turn_angle.degrees < 0):
			rover.client.sendMessage(Message.create(accel, RIGHT))
		elif rover.turning == 'R' or (rover.turning == 'r' and turn_angle.degrees < 0):
			rover.client.sendMessage(Message.create(accel, LEFT))
		else:
			rover.client.sendMessage(Message.create(accel))
		return

	if (abs(turn_angle.degrees) < SMALL_ANGLE) and (origin_dist < FORCE_TURN_DIST):
		rover.log.info('Forcing turn due to home proximity')

	if t >= rover.avg_interval:
		sched_time = 'until next telemetry update [~%1.4f seconds]' % (rover.avg_interval / INTERVAL_SCALE)
	else:
		sched_time = 'for %1.3f seconds' % t
	if turn_angle.radians < 0:
		rover.log.debug('Scheduling right turn %s (targeting %3.3f degrees)' % (sched_time, abs(turn_angle.degrees),))
		rover.client.sendMessage(Message.create(accel, RIGHT))

		if 0 < compensate_time < rover.avg_interval:
			def turn_left():
				rover.client.sendMessage(Message.create(accel, LEFT))
			reactor.callLater(compensate_time, turn_left)
	else:
		rover.log.debug('Scheduling left turn %s (targeting %3.3f degrees)' % (sched_time, abs(turn_angle.degrees),))
		rover.client.sendMessage(Message.create(accel, LEFT))

		if 0 < compensate_time < rover.avg_interval:
			def turn_right():
				rover.client.sendMessage(Message.create(accel, RIGHT))
			reactor.callLater(compensate_time, turn_right)
