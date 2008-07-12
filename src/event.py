# really wish i knew twisted...

LARGE_NUM = 1.0e6

class Event(object):
	def __init__(self, callback, args, time):
		self.callback = callback
		self.args = args
		self.time = time
	
	def execute(self):
		return self.callback(*args)

class EventQueue(object):
	def __init__(self):
		self.queue = []
	
	def insert(self, event):
		self.queue.append(event)
		self.queue.sort(key=lambda x: getattr(x, 'time'))
	
	def pop(self):
		return self.queue.pop(0)

	def next_time(self):
		'''Returns the number of seconds in the future for the next event or a
		large number if no events are in the queue.'''
		if not self.queue:
			return LARGE_NUM
		return self.queue[0].time - time.time()
