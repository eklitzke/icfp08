'''Steering strategies'''

import math
import time

import mars_math
from message import *
from constants import *
from twisted.internet import reactor
from nav import MapGrid


def steer_rover(f):
	'''Decorates the function passed in by adding in steering logic. The
	function it decorates should take one parameter (the rover object) and
	return two parameters, turn angle and force turn. Turn angle is an Angle or
	TurnAngle representing the desired turn angle, and force_turn should be
	True if turning should be forced (it's better to have it as False, but of
	course sometimes the rover *needs* to turn.  
    
    This is called whenever setTelemetry is called so it should work in ~< 10ms
    '''

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
		t = abs(turn_angle.radians / omega)

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

class PathStrategy(object): 
    def __init__(self): 
        self.last_path_update = 0
        self.update_path_interval = 5.0
        self.update_no = 0
        self.path = []
        self.grid = None

    def getRotation(self, rover):
        """Get the desired turn angle for the rover
        Args:
            rover
        Returns:
            turn angle, force turn
        """
        # init the path
        if self.path == [] or (self.update_path_interval < time.time() - self.last_path_update):
            self.grid = MapGrid(rover.map_size[0], rover.map_size[1], 100 if self.update_no == 0 else 201)
            print "UPDATING PATHS", self.update_path_interval, self.last_path_update, time.time() - self.last_path_update
            process_start = time.time()
            self.recalculatePath(rover) 
            process_end = time.time()

        shift = rover.secondsBehind()
        print "TIME SHIFT", shift
        expected_pos = rover.vector.future_position(shift + 0.0)

        # find the nearest path member and head to the next one
        def dist(p):
            return math.hypot(expected_pos.x - p.x, expected_pos.y - p.y)
        
        nearest_idx = min((dist(p), i) for i, p in enumerate(self.path))[1]
        try:
            next = self.path[nearest_idx + 1]
        except IndexError:
            next = self.path[-1]

        angle = mars_math.direction(expected_pos, next)
        ta = mars_math.TurnAngle(angle - rover.vector.angle.radians)
        print "Heading to", next, ta.radians * 57.77
        return ta, False

    def recalculatePath(self, rover): 
        print "RECALCULATE"
        for object in rover.objects:
            if object['kind'] in (CRATER, BOULDER):
                self.grid.add_obstacle((object['position'].x, object['position'].y), max(2, (1.3 * object['radius'])))
        pos = rover.vector.pos
        path = self.grid.path(pos, mars_math.find_home_point(rover.vector.pos))
        # add every 15 meters
        self.path = [path.pop(0)]
        end = path.pop()
        while path:
            point = path.pop(0)
            prev = self.path[-1]
            dist = math.hypot(prev.x - point.x, prev.y - point.y)
            if dist < 15:
                continue
            self.path.append(point)
        self.path.append(end)
        self.last_path_update = time.time()

# This is the default / most simple strategy.  This is called on every
# setTelemetry update
basic_strategy = steer_rover(mars_math.find_heading)

path_strategizer = PathStrategy()

# Strategy to use A* calc'ed paths
path_strategy = steer_rover(path_strategizer.getRotation)

current_strategy = path_strategy
# vim: noet sw=4
