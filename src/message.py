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
