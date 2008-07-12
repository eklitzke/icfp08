import math

MESS_TELEMETRY = 1

def safe_split(s, sep, n):
	split = s.split(sep, n - 1)
	while len(split) < n:
		split.append('')
	return split

def parse_message(data):
	type = data[0]
	mess_dict = {}
	if type == 'I':
		mess_dict['type'] = 'initial'
		_, dx, dy, time_limit, min_sens, max_sens, max_speed, max_turn, max_hard_turn = data.strip().split(' ')
		mess_dict['dx'] = dx
		mess_dict['dy'] = dy
		mess_dict['time_limit'] = int(time_limit)
		mess_dict['min_sens'] = float(min_sens)
		mess_dict['max_sens'] = float(max_sens)
		mess_dict['max_speed'] = float(max_speed)
		mess_dict['max_turn'] = float(max_turn)
		mess_dict['max_hard_turn'] = float(max_hard_turn)
	if type == 'T':
		mess_dict['type'] = 'telemetry'
		_, time_stamp, vehicle_ctl, vx, vy, dir, speed, object_str = safe_split(data, ' ', 8)
		print 'object_str = %r' % object_str
		mess_dict['time_stamp'] = int(time_stamp)
		mess_dict['accel_state'] = vehicle_ctl[0]
		mess_dict['turn_state'] = vehicle_ctl[1]
		mess_dict['x_pos'] = float(vx)
		mess_dict['y_pos'] = float(vy)
		mess_dict['direction'] = {'degrees': float(dir), 'radians': float(dir) * math.pi / 180.0}
		mess_dict['speed'] = float(speed)
		mess_dict['objects'] = []

		# parse the objects string
		if object_str:
			objects = object_str.split(' ')
			while objects:
				print objects
				obj = {}
				if objects[0] == 'b':
					_, x_pos, y_pos, radius = objects[:4]
					obj['type'] = 'boulder'
					obj['x_pos'] = float(x_pos)
					obj['y_pos'] = float(y_pos)
					obj['radius'] = float(radius)
					objects = objects[4:]
				elif objects[0] == 'c':
					_, x_pos, y_pos, radius = objects[:4]
					obj['type'] = 'crater'
					obj['x_pos'] = float(x_pos)
					obj['y_pos'] = float(y_pos)
					obj['radius'] = float(radius)
					objects = objects[4:]
				elif objects[0] == 'm':
					_, x_pos, y_pos, dir, speed = objects[:5]
					obj['type'] = 'martian'
					obj['x_pos'] = float(x_pos)
					obj['y_pos'] = float(y_pos)
					obj['dir'] = {'degrees': float(dir), 'radians': float(dir) * math.pi / 180.0}
					obj['speed'] = float(speed)
					obj['radius'] = 0.4
					objects = objects[5:]

				mess_dict['objects'].append(obj)

		#TODO: parse the object string
	return mess_dict

# Acceleration states
ROLL = '-'
ACCELERATE = 'a'
BRAKE = 'b'

# Turn states
LEFT = 'l'
RIGHT = 'r'
HARDRIGHT = 'R'
HARDLEFT = 'L'
STRAIGHT = '-'

class Message(object): 
    @classmethod
    def create(cls, accel=None, turn=None): 
        """Create a message to send to the rover via the server.
        Args:
            accel -- None or str, or a accel state
            turn -- None or str, one of turn states
        """
        msg = ""
        if accel:
            msg += accel
            assert accel in [ACCELERATE, BRAKE]

        if turn:
            assert turn in [LEFT, RIGHT]
            msg += turn
        assert msg
        msg += ";"
        return msg

    @classmethod
    def parse(cls, msg):
        """Parse a message from the server.
        Messages should end with a ';'.
        Returns:
            {
            'type': message type,
            'time_stamp': time stamp 
            'telemetry': telemetry 
            ...
            }
        """
        tokens = msg.split() 
        assert tokens[-1] == ';'
        tokens.pop()
        assert tokens
        result = {
                'type': '',
                'telemetry': {}, 
                'time_stamp': -1,
                'end': False,
                'score': -1,
                'duration': -1,
                }
        token = tokens.pop(0) 
        if token == 'T':
            result['type'] = 'telemetry'
            result['time_stamp'] = cls.parse_float(tokens)
            result['telemetry'] = cls.parse_telemetry(tokens)
        elif token == 'B': 
            result['type'] = 'crash'
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'C':
            result['type'] = 'crater'
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'K':
            result['type'] = 'killed'
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'E':
            result['type'] = 'end'
            result['duration'] = cls.parse_float(tokens)
        elif token == 'S':
            result['type'] = 'success'
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'I':
            result['type'] = 'initial'
            result['initial'] = cls.parse_initial(tokens)
        else:
            raise ValueError('unknown message type: ' + token)
        return result

    @classmethod
    def parse_initial(cls, tokens): 
        x = {} 
        for i in ['dx', 'dy', 'time_limit', 'min_sensor', 'max_sensor',
                'max_speed', 'max_turn', 'max_hard_turn']:
            x[i] = cls.parse_float(tokens)  
        return x

    @classmethod
    def parse_controls(cls, tokens): 
        accel, turn = tokens.pop(0)
        assert accel in [ACCELERATE, BRAKE, ROLL]
        assert turn in [LEFT, STRAIGHT, RIGHT, HARDLEFT, HARDRIGHT]
        return accel, turn

    @classmethod
    def parse_telemetry(cls, tokens): 
        tel = {} 
        tel['acceleration'], tel['turning'] = cls.parse_controls(tokens)
        tel['position'] = cls.parse_float(tokens), cls.parse_float(tokens) 
        tel['direction'] = cls.parse_float(tokens) 
        tel['velocity'] = cls.parse_float(tokens) 
        tel['objects'] = cls.parse_objects(tokens) 
        return tel

    @classmethod
    def parse_objects(cls, tokens): 
        objects = []
        while tokens:
            object = {}
            objects.append(object) 
            kind = tokens.pop(0)
            object['kind'] = {
                    'm': 'martian',
                    'b': 'boulder',
                    'c': 'crater', 
                    'h': 'home',
                }[kind]
            object['position'] = cls.parse_float(tokens), cls.parse_float(tokens) 
            if object['kind'] == 'martian':
                object['direction'] = cls.parse_float(tokens)
                object['speed'] = cls.parse_float(tokens)
                object['radius'] = None
            else:
                object['radius'] = cls.parse_float(tokens) 
        assert objects
        return objects

    @classmethod
    def parse_float(cls, tokens): 
        atom = tokens.pop(0) 
        return float(atom) 


