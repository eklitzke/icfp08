#!/usr/bin/env python

import logging
import sys
import time

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

# local imports
import event
from message import * 
from constants import *
import mars_math
import utils
import strategies

def similar(a, b, precision=0.95): 
    d = abs(a - b)
    return d <= ((1.0 - precision) * abs(a))

def similar_position((x1, y1), (x2, y2)):
    return similar(x1, x2) and similar(y1, y2)

def similar_position(p1, p2):
    return similar(p1.x, p2.x) and similar(p1.y, p2.y)

class Map(object): 
    log = logging.getLogger('Map') 

    def __init__(self): 
        self.size = -1, -1
        self.objects = []

    

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
        self.origin = mars_math.Point(0.0, 0.0)
        self.objects = []
        self.martians = []

        # holds up to three intervals
        self.MAX_INTERVALS = 3
        self.telemetry_intervals = []
        self.martian_intervals = []

    def noticeObject(self, object):
        if object['kind'] == MARTIAN:
            self.martians.append(object)

        for o in self.objects:
            if o['kind'] == object['kind'] \
                    and similar_position(object['position'], o['position']):
                break
        else:
            self.log.debug('found new object: %r', object)
            self.objects.append(object)

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

        # to prevent an update from being sent if it's going to be really close
         # to a telemetry update anyways
        self.avg_interval *= INTERVAL_SCALE

    def determineAcceleration(self, angle):
        '''Determine whether to accelerate, roll, or brake based on the angle
        that we're trying to turn.'''
        degrees = abs(angle.degrees)

        if degrees < 30.0:
            return ACCELERATE
        elif degrees < 60:
            return ROLL
        else:
            return BRAKE

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
            if 'position' in object:
                object['position'] = mars_math.Point(*object['position'])
            self.noticeObject(object)
        self.direction = mars_math.Angle(mars_math.to_radians(telemetry['direction']))
        self.vector = mars_math.Vector(self.position, self.velocity, self.direction)

        self.recordCommunicationsData()

        # XXX: you can try out different strategies by altering this
        if self.secondsBehind() < 0.5:
            print "SECONDS BEHIND", self.secondsBehind()
            strategies.current_strategy(self)

    def secondsBehind(self): 
        return time.time() - (self.time_start + self.latest_mtime)

    def recordMartianTime(self, mtime):
        '''Since the simulation appears to run it real time this isn't strictly
        necessary, but it's nice to have it anyways since it is "correct".'''
        mtime = mtime / 1000.0 # martian time is sent in milliseconds
        if self.time_start == None:
            self.time_start = time.time() - 0.02
        self.latest_mtime = mtime

        intervals = self.martian_intervals + [mtime]

        self.avg_martian_interval = 0
        if len(intervals) > 1:
            delta_sum = sum(y - x for x, y in zip(intervals[:-1], intervals[1:]))
            interval_amt = (len(intervals) - 1)
            self.avg_martian_interval = delta_sum / interval_amt

        self.martian_intervals = intervals
        if len(intervals) > self.MAX_INTERVALS:
            self.martian_intervals = intervals[1:]

    def endRun(self): 
        self.time_start = None

    def setInitial(self, initial):
        """This is called with initial data"""
        self.log.debug('received initial data: %r', initial)
        self.map_size = initial['dx'], initial['dy']
        self.time_start = None
        self.time_limit = initial['time_limit']
        self.min_sensor = initial['min_sensor']
        self.max_sensor = initial['max_sensor']
        self.max_speed = initial['max_speed']
        self.max_turn = mars_math.to_radians(initial['max_turn'])
        self.max_hard_turn = mars_math.to_radians(initial['max_hard_turn'])
        self.initialized = True

        
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
            self.rover_ctl.recordMartianTime(msg['time_stamp'])
            self.rover_ctl.setTelemetry(msg['telemetry'])
        elif msg['type'] == 'initial':
            self.rover_ctl.setInitial(msg['initial'])
        elif msg['type'] == 'success':
            self.log.info('Successful!')
        elif msg['type'] == 'end':
            self.rover_ctl.endRun()
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
