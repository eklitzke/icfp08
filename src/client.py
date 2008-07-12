import sys
import time
import select

# local imports
import event

RECV_SIZE = 4096 # should be way more than enough

class Client(object):
	def __init__(self, host, port):
		self.host = host
		self.port = port
		self.event_queue = event.EventQueue()

	def connect(self):
		'''Creates self.sock and initializes it'''
		self.sock = socket.soket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host, self.port))

	def schedule_event(self, callback, args, delta_t):
		future_time = time.time() + delta_t
		self.event_queue.insert(event.Event(callback, args, future_time))
	
	def scheduler_wait(self):
		delta_t = self.event_queue.next_time() # probably want to cap this?
		in, _, _ = select.select([self.sock], [], [], delta_t)

		if not in:
			# Timed out waiting for a message, execute the next event in the
			# event queue...
			event = self.event_queue.pop()
			event.execute()
		else:
			# Got a telemetry or status update...
			data = self.sock.recv(RECV_SIZE)
			self.handle_message(data)

	def run(self):
		'''Runs the client'''
		self.connect()

		# loop in the scheduler
		while True:
			self.scheduler_wait()

if __name__ == '__main__':
	icfp_client = Client(sys.argv[1], int(sys.argv[2]))
	icfp_client.run()
