import argparse

parser = argparse.ArgumentParser(description='Generates designed scenario of data streams')
parser.add_argument('output_file', help='The file to save data streams to')
parser.add_argument('-b', type=int, default=-1, help='A batch size of data streams saved to a single file')

args = parser.parse_args()

legend = """#Stream naming convention:
# * the '+' signals concurrent drifts
# * the '_' signals sequential drifts
# * StaticIm[N]: stream starts with the N% minority share
# * Split[N]: drift splits minority class into N clusters 
# * Move[N]: drift changes the positions of N clusters in attribute space
# * Im[N]: drift changes imbalance ratio to N% minority share
# * Borderline[N]: drift increases borderline examples to N%
# * Rare[N]: drift increases rare examples to N%\n\n 
"""

post_drift_suffix = '-post-drift'

#-----FUNCTIONS---------------------------------------------------------------------------------------------------------
def stream(name, clusters, minority_share, safe, borderline, rare, drifts):
	drifts = ':\\\n\t'.join(list(filter(None, drifts)))
	stream.count += 1
	return ('# {}\n$(STRM_DIR)/{}.arff:\n'
			'\t@make .stream FILE=$@ GENERATOR="generators.ImbalancedDriftGenerator \\\n'
			'\t-a $(ATTRIBUTES) -n {:d} -m {:f} -s {:f} -b {:f} -p {:f} -o 0 -u \\\n'
			'\t-d \'\\\n\t{}\\\n\t\'"\n\n').format(stream.count, name, clusters, minority_share,
												   safe, borderline, rare, drifts)
stream.count = 0

def write_to_file(str):
	if write_to_file.streams_written in [0, args.b]:
		if write_to_file.file is not None:
			write_to_file.file.close()
		write_to_file.curr_file_nr += 1
		write_to_file.file = open(args.output_file if args.b == -1
								  else '{}.part{:d}'.format(args.output_file, write_to_file.curr_file_nr), 'w')
		write_to_file.file.write(legend)
		write_to_file.streams_written = 0
	write_to_file.file.write(str)
	write_to_file.streams_written += 1
write_to_file.file = None
write_to_file.curr_file_nr = 0
write_to_file.streams_written = 0

def instance_type_drift(type, drift_start, drift_end, start_ratio, end_ratio, divisor = 1):
	return '{}-ratio/{},start={:d},end={:d},value-start=1,value-end={:f}'.format(
		type, 'sudden' if drift_start == drift_end else 'incremental', drift_start, drift_end,
		round(end_ratio / (1 - end_ratio), 6) / round(start_ratio / (1 - start_ratio), 6) / divisor)

def borderline_drift(drift_start, drift_end, start_ratio, end_ratio):
	return instance_type_drift('borderline', drift_start, drift_end, start_ratio, end_ratio)

def rare_drift(drift_start, drift_end, start_ratio, end_ratio):
	return instance_type_drift('rare', drift_start, drift_end, start_ratio, end_ratio)

def borderline_rare_drift(drift_start, drift_end, start_ratio, end_ratio):
	return '{}:\\\n\t{}'.format(
		instance_type_drift('borderline', drift_start, drift_end, start_ratio, end_ratio, 2),
		instance_type_drift('rare', drift_start, drift_end, start_ratio, end_ratio, 2))

def imbalance_drift(drift_start, drift_end, start_ratio, end_ratio):
	return 'minority-share/{},start={:d},end={:d},value-start=1,value-end={:f}'.format(
		'sudden' if drift_start == drift_end else 'incremental', drift_start, drift_end, end_ratio / start_ratio)

def merge_clusters_at_beggining():
	return 'splitting-clusters/sudden,start=1,end=1,value-start=0,value-end=0'

def move_drift(drift_start, drift_end):
	return ('clusters-movement/incremental,start={0:d},end={1:d},value-start=0,value-end=1:\\\n\t'
			'clusters-movement/incremental,start={1:d},end={2:d},value-start=0,value-end=1').format(
			drift_start, int(drift_start + (drift_end - drift_start) / 2), drift_end)

def split_drift(drift_start, drift_end):
	return merge_clusters_at_beggining() + ':\\\n\t' + move_drift(drift_start, drift_end)

def join_drift(drift_start, drift_end):
	return 'splitting-clusters/incremental,start={:d},end={:d},value-start=1,value-end=0'.format(drift_start, drift_end)

#-----------------------------------------------------------------------------------------------------------------------

drift_start, drift_end = 70000, 100000
pd_start, pd_end = 2, 4
epsilon = 0.000001

#-----Imbalance ratio streams-------------------------------------------------------------------------------------------

imbalance = [.5, .4, .3, .2, .1, .05, .03, .02, .01]
for im1 in imbalance:
	for im2 in imbalance:
		name, drift = 'StaticIm{:d}'.format(int(im1 * 100)), ['']
		if im1 > im2:
			name = '{}Im{:d}'.format('' if im1 == .5 else name + '_', int(im2 * 100))
			drift = [imbalance_drift(drift_start, drift_end, im1, im2)]
		if im1 < im2: continue
		write_to_file(stream(name, 1, im1, 1, 0, 0, drift))

#----- Class swaps (minority -> majority)-------------------------------------------------------------------------------

for im1 in imbalance[1:]:
	for im2 in {1 - im1, .6, .7, .8, .9}:
		write_to_file(stream('StaticIm{:d}_Im{:d}'.format(int(im1 * 100), int(im2 * 100)), 1, im1, 1, 0, 0,
							 [imbalance_drift(drift_start, drift_end, im1, im2)]))



#-----Split vs Move vs Join streams---------------------------------------------------------------------------------------------

for static_im in [.5, .1, .01]:
	for clusters in [3, 5, 7]:
		static = 'StaticIm{:d}_'.format(int(static_im * 100)) if static_im != .5 else ''
		split_name = static + 'Split{}'.format(clusters)
		move_name = static + 'Move{}'.format(clusters)
		join_name = static + 'Join{}'.format(clusters)
		write_to_file(stream(split_name, clusters, static_im, 1, 0, 0, [split_drift(drift_start, drift_end)]))
		write_to_file(stream(split_name + post_drift_suffix, clusters, static_im, 1, 0, 0, [split_drift(pd_start, pd_end)]))
		write_to_file(stream(move_name, clusters, static_im, 1, 0, 0, [move_drift(drift_start, drift_end)]))
		write_to_file(stream(move_name + post_drift_suffix, clusters, static_im, 1, 0, 0, [move_drift(pd_start, pd_end)]))
		write_to_file(stream(join_name, clusters, static_im, 1, 0, 0, [join_drift(drift_start,drift_end)]))
		write_to_file(stream(join_name + post_drift_suffix, clusters, static_im, 1, 0, 0, [join_drift(pd_start, pd_end)]))


#-----instance type streams---------------------------------------------------------------------------------------------

# for static_im in [.5, .1, .01]:
# 	static = 'StaticIm{:d}+'.format(int(static_im * 100)) if static_im != .5 else ''
# 	for borderline in [.2, .5, 1]:
# 		write_to_file(stream('{}StaticBorderline{}'.format(static, int(100 * borderline)),
# 						  1, static_im, 1 - borderline, borderline, 0, [""]))
#
# for static_im in [.5, .1, .01]:
# 	static = 'StaticIm{:d}+'.format(int(static_im * 100)) if static_im != .5 else ''
# 	for rare in [.2, .5, 1]:
# 		write_to_file(stream('{}StaticRare{}'.format(static, int(100 * rare)),
# 						  1, static_im, 1 - rare, 0, rare, [""]))
#
# for static_im in [.5, .1, .01]:
# 	static = 'StaticIm{:d}_'.format(int(static_im * 100)) if static_im != .5 else ''
# 	write_to_file(stream('{}Borderline20_Borderline50_Borderline100'.format(static), 1, static_im, 1, epsilon, 0,
# 					  [borderline_drift(50000, 50000, epsilon, .2),
# 					   borderline_drift(80000, 80000, .2, .5),
# 					   borderline_drift(110000, 110000, .5, .999999)]))
# for static_im in [.5, .1, .01]:
# 	static = 'StaticIm{:d}_'.format(int(static_im * 100)) if static_im != .5 else ''
# 	write_to_file(stream('{}Rare20_Rare50_Rare100'.format(static), 1, static_im, 1, 0, epsilon,
# 					  [rare_drift(50000, 50000, epsilon, .2),
# 					   rare_drift(80000, 80000, .2, .5),
# 					   rare_drift(110000, 110000, .5, .999999)]))


#-----StaticIm+Split5+Im+Borderline/Rare streams------------------------------------------------------------------------
clusters = 5
borderline_levels = .2, .4, .6, .8, 1 - epsilon
rare_levels = borderline_levels
borderline_rare_levels = .4, .8

static_ims = {'': .5,
			  'StaticIm10': .1}
splits = {'': lambda ds, de: merge_clusters_at_beggining(),
		  'Split{}'.format(clusters): lambda ds, de: split_drift(ds, de)}
ims = {'': lambda ds, de, x: "",
	   'Im10': lambda ds, de, x: imbalance_drift(ds, de, x, .1),
	   'Im1': lambda ds, de, x: imbalance_drift(ds, de, x, .01)}
types_borderline = {'Borderline{:d}'.format(int((val + epsilon) * 100)):
						(epsilon, 0, lambda ds, de, v = val: borderline_drift(ds, de, epsilon, v))
					for val in borderline_levels}
types_rare = {'Rare{:d}'.format(int((val + epsilon) * 100)):
				  (0, epsilon, lambda ds, de, v = val: rare_drift(ds, de, epsilon, v)) for val in rare_levels}
types_borderline_rare = {'Borderline{0:d}+Rare{0:d}'.format(int((val / 2 + epsilon) * 100)):
							 (epsilon, epsilon, lambda ds, de, v = val: borderline_rare_drift(ds, de, epsilon, v))
						 for val in borderline_rare_levels}
types = {'': (0, 0, lambda ds, de: ''), **types_borderline, **types_rare, **types_borderline_rare}

for static_im in static_ims.keys():
	for split in splits.keys():
		for im in ims.keys():
			for type in types.keys():
				name = '+'.join(list(filter(None, [split, im, type])))
				name = '_'.join(list(filter(None, [static_im, name])))
				if (static_im == 'StaticIm10' and im == 'Im10') or name is "": continue
				drifts = [splits[split](drift_start, drift_end),
						  ims[im](drift_start, drift_end, static_ims[static_im]),
						  types[type][2](drift_start, drift_end)]
				write_to_file(stream(name, clusters, static_ims[static_im],
								  1, types[type][0], types[type][1], drifts))
				post_drifts = [splits[split](pd_start, pd_end), ims[im](pd_start, pd_end, static_ims[static_im]), types[type][2](pd_start, pd_end)]
				write_to_file(stream(name + post_drift_suffix, clusters, static_ims[static_im],
									 1, types[type][0], types[type][1], post_drifts))
#-----------------------------------------------------------------------------------------------------------------------

print("Written {} streams to {}{}".format(stream.count, args.output_file, '' if write_to_file.curr_file_nr == 1 else '({} parts)'.format(write_to_file.curr_file_nr)))
write_to_file.file.close()