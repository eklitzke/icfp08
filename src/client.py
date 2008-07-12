import logging
import select
import socket
import sys
import time
import pprint

from twisted.internet import reactor
from twisted.internet.protocol import Protocol, ReconnectingClientFactory

# local imports
import event
from message import * 
import mars_math
import utils

RECV_SIZE = 4096 # should be way more than enough

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

    def setTelemetry(self, telemetry):
        """This is called when telemetry is updated"""
        self.telemetry_log.debug('set: %r', telemetry) 
        if self.acceleration != telemetry['acceleration']:
            self.acceleration = telemetry['acceleration']
            self.telemetry_log.info('new acceleration: %r', self.acceleration)

        self.turning = telemetry['turning']
        self.position = telemetry['position']
        self.velocity = telemetry['velocity']
        self.direction = telemetry['direction']
        for object in telemetry['objects']:
            self.map.notice(object)

    def setInitial(self, initial):
        """This is called with initial data"""
        self.log.debug('received initial data: %r', initial)
        self.map.size = initial['dx'], initial['dy']
        self.time_limit = initial['time_limit']
        self.min_sensor = initial['min_sensor']
        self.max_sensor = initial['max_sensor']
        self.max_speed = initial['max_speed']
        self.max_turn = initial['max_turn']
        self.max_hard_turn = initial['max_hard_turn']
        self.initialized = True
        reactor.callLater(1.0, self.start)
        #self.start() 

    def start(self): 
        self.log.info('started')
        self.client.sendMessage(Message.create(ACCELERATE))
        def stop():
            self.client.sendMessage(Message.create(BRAKE)) 
        reactor.callLater(3.0, stop)

class Client(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.event_queue = event.EventQueue()

		self.mtime = 0 # martian time, in milliseconds
		self.vector = None

	def log(self, s):
		print s

	def connect(self):
		'''Creates self.sock and initializes it'''
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

	def handle_message(self, msg):
		'''Handles a message from the "server"'''
		mess = parse_message(msg)
		self.log('handle_message: %s' % mess)

		if mess['type'] == 'initial':
			self.vector = None # this is the only time the vector can be None
			self.time_limit = mess['time_limit']
			self.min_sens = mess['min_sens']
			self.max_sens = mess['max_sens']
			self.max_speed = mess['max_speed']
			self.max_turn = mess['max_turn']
			self.max_hard_turn = mess['max_hard_turn']

			# this is a special case -- everything else should fall through and
			# take an action based on the current state. for the initial
			# message we wait until we get telemetry data (which happens
			# IMMEDIATELY, i.e. at mtime = 0)
			return

		elif mess['type'] == 'telemetry':
			self.mtime = mess['time_stamp']

			pos = mars_math.Point(mess['x_pos'], mess['y_pos'])
			ang = mars_math.Angle(mess['direction']['radians'])
			self.vector = mars_math.Vector(pos, mess['speed'], ang)

		elif mess['type'] == 'something else':
			pass

		# accelerate!
		self.send_message('a;')

	def send_message(self, msg):
		self.sock.send(msg)

	def schedule_event(self, callback, args, delta_t):
		future_time = time.time() + delta_t
		self.event_queue.insert(event.Event(callback, args, future_time))

	def scheduler_wait(self):
		self.log('scheduler_wait')
		delta_t = self.event_queue.next_time()
		got_message, _, _ = select.select([self.sock], [], [], delta_t)

		if got_message:
			data = self.sock.recv(RECV_SIZE)
			if not data:
				self.finish() # server has closed its connection
			messages = [msg.strip() for msg in data.split(';') if msg.strip()]
			for msg in messages:
				self.handle_message(msg)
		else:
			event = self.event_queue.pop()
			event.execute()

	def run(self):
		'''Runs the client'''
		self.connect()

		# loop in the scheduler
		while True:
			self.scheduler_wait()

	def finish(self):
		'''Runs when the server shuts down'''
		self.log('Finishing...')
		sys.exit(0)

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
    if '-t' in sys.argv:
        sys.argv.remove('-t') 
        twisted = True
    else:
        twisted = False

    host = sys.argv[1]
    port = int(sys.argv[2])

    if not twisted:
        icfp_client = Client(sys.argv[1], int(sys.argv[2]))
        icfp_client.run()
    else:
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


