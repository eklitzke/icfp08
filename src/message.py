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

		#TODO: parse the object string
	return mess_dict

class Message(object): 
    @classmethod
    def parse(cls, input): 
        result = []
        for message in input.split(';'): 
            tokens = message.split()
            if tokens:
                result.append(cls._parse(tokens))
        return result

    @classmethod
    def _parse(cls, tokens):
        assert tokens
        result = {
                'telemetry': {}, 
                'crash': False, 
                'time_stamp': -1,
                'crater': False,
                'killed': False,
                'end': False,
                'score': -1,
                'duration': -1,
                'success': False,
                }
        token = tokens.pop(0) 
        if token == 'T':
            result['time_stamp'] = cls.parse_float(tokens)
            result['telemetry'] = cls.parse_telemetry(tokens)
        elif token == 'B': 
            result['crash'] = True
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'C':
            result['crater'] = True
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'K':
            result['killed'] = True
            result['time_stamp'] = cls.parse_float(tokens)
        elif token == 'E':
            result['end'] = True
            result['duration'] = cls.parse_float(tokens)
        elif token == 'S':
            result['success'] = True
            result['time_stamp'] = cls.parse_float(tokens)
        assert  not tokens
        return result

    @classmethod
    def parse_telemetry(cls, tokens): 
        tel = {} 
        tel['control'] = tokens.pop(0)
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
            object['kind'] = tokens.pop(0) 
            assert object['kind'] in ['m', 'b', 'c', 'h'], object['kind']
            object['position'] = cls.parse_float(tokens), cls.parse_float(tokens) 
            if object['kind'] == 'm':
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


