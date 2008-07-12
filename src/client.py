import sys
import time
import select
import socket

# local imports
import event
import message
import mars_math

RECV_SIZE = 4096 # should be way more than enough

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
		mess = message.parse_message(msg)
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

		# do something

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

if __name__ == '__main__':
	icfp_client = Client(sys.argv[1], int(sys.argv[2]))
	icfp_client.run()
