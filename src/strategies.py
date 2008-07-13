'''Steering strategies'''

import math
import mars_math
from message import *
from constants import *
from twisted.internet import reactor

def steer_rover(f):
	'''Decorates the function passed in by adding in steering logic. The
	function it decorates should take one parameter (the rover object) and
	return two parameters, turn angle and force turn. Turn angle is an Angle or
	TurnAngle representing the desired turn angle, and force_turn should be
	True if turning should be forced (it's better to have it as False, but of
	course sometimes the rover *needs* to turn.'''

	def new_func(rover):
		'''This steers the rover. It takes two parameters:
		* rover -- the rover object
		* turn_angle -- an Angle (or TurnAngle) object representing the turn that the rover should make
		* force_turn -- a boolean that tells the rover whether or not it should force turning
		'''
		turn_angle, force_turn = f(rover)
		soft_turn = rover.max_turn
		hard_turn = rover.max_hard_turn
		turn = rover.turning

		is_hard = (turn in ('r', 'R') and mars_math.is_right_turn(turn_angle)) or (turn in ('l', 'L') and mars_math.is_left_turn(turn_angle))
		omega = hard_turn if is_hard else soft_turn
		t = abs(turn_angle.degrees / omega) # FIXME is htis right?

		origin_distance = mars_math.distance(rover.origin, rover.position)

		if force_turn:
			rover.log.info('Fuck, please don\'t let me bump into anything')
		accel = 'b' if force_turn else rover.determineAcceleration(turn_angle)

		# turning angle should be in the range -pi to pi
		assert abs(turn_angle.radians < (math.pi * 1.01)), "Invalid turn angle %s" % turn_angle.radians

		# in this many milliseconds will send out another message reversing the
		# turn angle (i.e. to straighten out our path)

		# This is commented out because the processing time applies to
		# both the initial message and the straighten up message...
		#compensate_time = t - PROCESSING_TIME
		compensate_time = t

		# if the angle is small we should just keep moving forward
		if not force_turn and (abs(turn_angle.degrees) < SMALL_ANGLE) and (origin_distance > FORCE_TURN_DIST):
			if rover.turning == 'L' or (rover.turning == 'l' and turn_angle.degrees < 0):
				rover.client.sendMessage(Message.create(accel, RIGHT))
			elif rover.turning == 'R' or (rover.turning == 'r' and turn_angle.degrees < 0):
				rover.client.sendMessage(Message.create(accel, LEFT))
			else:
				rover.client.sendMessage(Message.create(accel))
			return

		if (abs(turn_angle.degrees) < SMALL_ANGLE) and (origin_distance < FORCE_TURN_DIST):
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
	return new_func

@steer_rover
def basic_strategy(rover):
	turn_angle, force_turn = mars_math.find_heading(rover.vector, rover.map.objects)
	return turn_angle, force_turn

# vim: noet sw=4
