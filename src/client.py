import sys
import time
import select
import socket

# local imports
import event
import message

RECV_SIZE = 4096 # should be way more than enough

class Client(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.event_queue = event.EventQueue()

		self.mtime = 0 # martian time, in milliseconds
	
	def log(self, s):
		print s

	def connect(self):
		'''Creates self.sock and initializes it'''
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))
		self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	
	def handle_message(self, msg):
		'''Handles a message from the "server"'''
		self.log('handle_message(%r)' % msg)
		mess = message.parse_message(msg)
		print mess

	def schedule_event(self, callback, args, delta_t):
		future_time = time.time() + delta_t
		self.event_queue.insert(event.Event(callback, args, future_time))

	def scheduler_wait(self):
		self.log('scheduler_wait')
		delta_t = self.event_queue.next_time()
		got_message, _, _ = select.select([self.sock], [], [], delta_t)

		if got_message:
			data = self.sock.recv(RECV_SIZE)
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

if __name__ == '__main__':
	icfp_client = Client(sys.argv[1], int(sys.argv[2]))
	icfp_client.run()
