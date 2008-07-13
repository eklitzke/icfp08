#!/usr/bin/env python

import logging
import select
import socket
import sys
import time
import pprint

import random

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

# local imports
import event
from message import * 
import mars_math
import utils

r = math.sin(math.pi / 4) * 5
BASE_POINTS = ((-5.0, 0.0), (0.0, 5.0), (5.0, 0.0), (-5.0, 0.0), (r, r), (r, -r), (-r, -r), (-r, r))
del r

# The docs say the processing time is less than 20 milliseconds
PROCESSING_TIME = 0.015

def similar(a, b, precision=0.95): 
    d = abs(a - b)
    return d <= ((1.0 - precision) * abs(a))

def similar_position((x1, y1), (x2, y2)):
    return similar(x1, x2) and similar(y1, y2)

class Map(object): 
    log = logging.getLogger('Map') 

    def __init__(self): 
        self.size = -1, -1
        self.objects = []

    def notice(self, object):
        if object['kind'] == MARTIAN:
            return
        for o in self.objects:
            if o['kind'] == object['kind'] \
                    and similar_position(object['position'], o['position']):
                break
        else:
            self.log.debug('found new object: %r', object)
            self.objects.append(object)

class RoverController(object):
    """responsible for sending and receiving messages from the client
    
    Instance variables:
        client -- server client
        map_size -- (int, int), width height of map
        initialized -- bool, has this rover been initialized?
        time_limit -- int, time limit in seconds
        min_sensor -- float, minimum sensor range in meters 
        max_sensor -- float, max sensor range in meters
        
    """

    log = logging.getLogger('RoverController') 
    telemetry_log = logging.getLogger('RoverController.telemetry') 
    telemetry_log.setLevel(logging.INFO)

    def __init__(self, client):
        self.client = client
        self.map_size = -1, -1
        self.time_limit = -1
        self.min_sensor = -1
        self.max_sensor = -1
        self.max_speed = -1
        self.max_turn = -1
        self.max_hard_turn = -1 
        self.velocity = -1 
        self.objects = []
        self.position = -1, -1
        self.direction = -1
        self.controls = ''
        self.initialized = False
        self.acceleration = ROLL
        self.map = Map() 
        self.origin = mars_math.Point(0.0, 0.0)

        # holds up to three intervals
        self.MAX_INTERVALS = 3
        self.telemetry_intervals = []

    def recordCommunicationsData(self):
        '''This keeps track of communication data, like the rate that the
        controller is getting telemetry data.'''

        # INTERVALS LOGIC
        # The idea here is that when we're turning we schedule compensation
        # turns later on... so if we need to turn right twenty degrees, we
        # issue a right turn, and then wait some number of milliseconds and
        # then compensate by turning left to stabilize the position.
        #
        # If the amount of time we have to wait is longer than the average
        # amount of time between telemetry updates there's no reason in
        # scheduling the compensation since we'll have better logic soon
        intervals = self.telemetry_intervals + [time.time()]

        self.avg_interval = 0
        if len(intervals) > 1:
            delta_sum = sum(y - x for x, y in zip(intervals[:-1], intervals[1:]))
            interval_amt = (len(intervals) - 1)
            self.avg_interval = delta_sum / interval_amt

        self.telemetry_intervals = intervals
        if len(intervals) > self.MAX_INTERVALS:
            self.telemetry_intervals = intervals[1:]

        # fudge factor
        self.avg_interval *= 0.9

    def findHomePoint(self):

        # We want to steer for the furthest point on the origin. The reason is
        # if we have a situation like this:
        #
        #  ------------------>..--..
        #                   /       \
        #                  |    H    |
        #                   \       /
        #                    ',.__.'
        #
        # Where the arrow shows the trajectory of the rover, we really want to
        # be making a pretty hard right to make sure we don't shoot past the
        # target.

        distance_sq = self.position.x**2 + self.position.y**2

        # It's wasteful to optimize this when we're far away
        if distance_sq > 400:
            return self.origin

        # Sample 8 points around the circle:
        normsq = lambda (x, y): (self.position.x - x)**2 + (self.position.y - y)**2
        distances = [(pt, normsq(pt)) for pt in BASE_POINTS]
        return mars_math.Point(*max(distances, key=lambda x: x[1])[0])

    def steerToPoint(self, point=None):
        if point is None:
            point = self.findHomePoint()
        turn_angle, t = mars_math.steer_to_point(self.vector, self.max_turn, point)

        # turning angle should be in the range -pi to pi
        assert abs(turn_angle.radians < (math.pi * 1.01)), "Invalid turn angle %s" % turn_angle.radians

        # in this many milliseconds will send out another message reversing the
        # turn angle (i.e. to straighten out our path)
        compensate_time = t - PROCESSING_TIME

        # if the angle is small we should just keep moving forward
        if abs(turn_angle.degrees) < 5.0:
            if self.turning == 'L':
                self.client.sendMessage(Message.create(ACCELERATE, RIGHT))
            elif self.turning == 'R':
                self.client.sendMessage(Message.create(ACCELERATE, LEFT))
            else:
                self.client.sendMessage(Message.create(ACCELERATE))
            return

        sched_time = min(t, self.avg_interval)
        if turn_angle.radians < 0:
            self.log.debug('Scheduling right turn for %1.3f seconds (%3.3f degrees)' % (sched_time, abs(turn_angle.degrees),))
            self.client.sendMessage(Message.create(ACCELERATE, RIGHT))

            if 0 < compensate_time < self.avg_interval:
                def turn_left():
                    self.client.sendMessage(Message.create(ACCELERATE, LEFT))
                reactor.callLater(compensate_time, turn_left)
        else:
            self.log.debug('Scheduling left turn for %1.3f seconds (%3.3f degrees)' % (sched_time, abs(turn_angle.degrees),))
            self.client.sendMessage(Message.create(ACCELERATE, LEFT))
 
            if 0 < compensate_time < self.avg_interval:
                def turn_right():
                    self.client.sendMessage(Message.create(ACCELERATE, RIGHT))
                reactor.callLater(compensate_time, turn_right)

    def setTelemetry(self, telemetry):
        """This is called when telemetry is updated"""
        self.telemetry_log.debug('set: %r', telemetry) 
        if self.acceleration != telemetry['acceleration']:
            self.acceleration = telemetry['acceleration']
            self.telemetry_log.info('new acceleration: %r', self.acceleration)

        self.turning = telemetry['turning']
        self.position = mars_math.Point(*telemetry['position'])
        self.velocity = telemetry['velocity']
        self.direction = telemetry['direction']
        for object in telemetry['objects']:
            self.map.notice(object)
        self.direction = mars_math.Angle(mars_math.to_radians(telemetry['direction']))
        self.vector = mars_math.Vector(self.position, self.velocity, self.direction)

        self.recordCommunicationsData()
        self.steerToPoint()

    def setInitial(self, initial):
        """This is called with initial data"""
        self.log.debug('received initial data: %r', initial)
        self.map.size = initial['dx'], initial['dy']
        self.time_limit = initial['time_limit']
        self.min_sensor = initial['min_sensor']
        self.max_sensor = initial['max_sensor']
        self.max_speed = initial['max_speed']
        self.max_turn = mars_math.to_radians(initial['max_turn'])
        self.max_hard_turn = mars_math.to_radians(initial['max_hard_turn'])
        self.initialized = True
        reactor.callLater(1.0, self.start)
        #self.start() 

    def start(self): 
        self.log.info('started')
        self.client.sendMessage(Message.create(ACCELERATE))
        def stop():
            self.client.sendMessage(Message.create(BRAKE)) 
        reactor.callLater(3.0, stop)

class TwistedClient(Protocol): 
    log = logging.getLogger('TwistedClient')
    log.setLevel(logging.INFO)

    def __init__(self): 
        # for storing input
        self.buf = []
        self.rover_ctl = RoverController(self)

    def connectionMade(self): 
        self.log.info("connection made")
        self.transport.setTcpNoDelay(True)

    def dataReceived(self, data):
        """This is called by twisted every time the client socket receives data
        Args:
            data -- str, data
        """
        self.buf.extend(data)
        while True:
            try:
                idx = self.buf.index(';')
            except ValueError:
                break
            msg_s = ''.join(self.buf[:idx + 1])
            del self.buf[:idx + 1]
            msg = Message.parse(msg_s) 
            self.log.debug('msg: %r', msg)
            self.messageReceived(msg)

    def messageReceived(self, msg): 
        """This is called every time the client receives a message.
        Args:
            msg -- dict, the parsed message dict, see Message
        """
        if msg['type'] == 'telemetry':
            self.rover_ctl.setTelemetry(msg['telemetry'])
        elif msg['type'] == 'initial':
            self.rover_ctl.setInitial(msg['initial'])
        elif msg['type'] == 'success':
            self.log.info('Successful!')
        elif msg['type'] == 'end':
            self.log.info('End of run (took %d martian seconds).' % msg['time_stamp'])
        else:
            self.log.error('unhandled message:%r', msg['type']) 

    def sendMessage(self, message): 
        self.log.info('send: %r', message)
        return self.transport.write(message)

class TwistedClientFactory(ReconnectingClientFactory):
    protocol = TwistedClient
    log = logging.getLogger('TwistedClient')

    def clientConnectionFailed(self, connector, reason):
        self.log.error('connection failed')
        reactor.stop()
    

    def clientConnectionLost(self, connector, reason):
        self.log.error('connection lost')
        reactor.stop() 

if __name__ == '__main__':

    if len(sys.argv) >= 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        # just use the default
        host = 'localhost'
        port = 17676

    # this creates clients when connections occur
    clientFactory = TwistedClientFactory()

    # the twisted reactor is a singleton in the app
    # you can do things with it like:
    #   reactor.crash, reactor.callLater, reactor.stop, reactor.callFromThread
    #
    # see here for a simple client info:
    #   http://twistedmatrix.com/projects/core/documentation/howto/clients.html
    reactor.connectTCP(host, port, clientFactory)
    reactor.run()

# vim: et st=4 sw=4
