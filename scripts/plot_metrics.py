import matplotlib
matplotlib.use('Agg')
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib import ticker
from itertools import cycle
import os
import argparse

parser = argparse.ArgumentParser(description='Plots given metrics against learning instances')
parser.add_argument('input_dir', help='The directory to get .csv files from')
parser.add_argument('output_dir', help='The directory to save .png files to')
parser.add_argument('metrics', nargs='+', help='The list of metrics to plot')
parser.add_argument('-r', action='store_true', help='scan for .csv files in immediate subdirectories')
parser.add_argument('-y', action='store_true', help='Plot data in fixed y range [0, 1]')
parser.add_argument('-s', type=int, default=0, help='the number of first entries in each dataframe to skip')
parser.add_argument('-o', nargs='+', help='The order of classifiers to use')
parser.add_argument('-d', nargs='+', type=int, help='x coordinates to mark begginings and ends of incremental drifts')
parser.add_argument('-a', type=int, help='The window size for moving average plots')

args = parser.parse_args()

lw = 0.5
me = 10
ms = 5
plt.rcParams.update({'font.size': 13})

def RGB(R,G,B):
	return R/255, G/255, B/255

colors = [RGB(204,51,17), RGB(0,153,136), RGB(0,119,187), RGB(238,119,51), RGB(238,51,119)]
#colors = ['r', 'g', 'b', 'orange', 'm']

lines_styles = cycle([
	{'color': colors[0], 'ls': '-', 'marker': 'o', 'markevery': me, 'markersize': ms, 'linewidth': lw},
	{'color': colors[1], 'ls': '--', 'marker': 's', 'markevery': me, 'markersize': ms, 'linewidth': lw},
	{'color': colors[2], 'ls': '-.', 'marker': '^', 'markevery': me, 'markersize': ms, 'linewidth': lw},
	{'color': colors[3], 'ls': ':', 'marker': '*', 'markevery': me, 'markersize': ms, 'linewidth': lw},
	{'color': colors[4], 'ls': '-.', 'marker': 'X', 'markevery': me, 'markersize': ms, 'linewidth': lw}
])

def plot_metrics(input_dir, output_dir):
	x_label = 'learning evaluation instances'
	classifiers = {os.path.splitext(entry.name)[0]: pd.read_csv(entry.path, skiprows=range(1, 1 + args.s))
				   for entry in os.scandir(input_dir)}
	for metric in args.metrics:
		ax = plt.gca()
		for point_name in [' ', 'start', 'pre-dirft', 'post-drift', 'end']:
			ax.plot([], [], ' ', label=point_name)
		for name in classifiers.keys() if args.o is None else args.o:
			data = classifiers[name]

			if name == "ESOS_ELM":
				name = "ESOS"

			y_label = metric
			if args.a is not None:
				y_label = 'rolling_' + metric
				data[y_label] = data[metric].rolling(window=args.a, min_periods=1).mean()
			ax = data.plot(**next(lines_styles), x=x_label, y=y_label, label=name, ax=ax, figsize=(7, 5))
			legend_data = [
				data[y_label].iloc[0],
				data.loc[data[x_label] == args.d[0], y_label].item(),
				data.loc[data[x_label] == args.d[1], y_label].item(),
				data[y_label].iloc[-1]]
			for value in legend_data:
				ax.plot([], [], ' ', label='{:.4f}'.format(value))
		#ax.set_title(os.path.basename(input_dir) + ': ' + metric)
		ax.set_xlabel('Number of processed instances [x1000]')
		ax.set_ylabel(metric)
		if args.y:
			ax.set_ylim([-0.05, 1.05])
			ax.yaxis.set_major_locator(ticker.MultipleLocator(0.1))
		ax.xaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x / 1000)))

		if args.d is not None and not '-post-drift' in input_dir \
				and not ("Static" in input_dir and not '_' in input_dir):
			#the post-drift scenarios are to be static. The script is used in makefile where the whole
			#evaluation folder is passed so for execution simplicity the post-drift streams need to be filtered out
			for i, coord in enumerate(args.d):
				ax.axvline(x=coord, linestyle=(0, (5, 10)), color='k', linewidth=.5)
				if i % 2 == 1:
					ax.axvspan(args.d[i], args.d[i - 1], facecolor='lightgray', alpha=0.5)
		ax.legend(loc='lower center', bbox_to_anchor=(-0.25, 1.02, 1.25, 0.2), ncol=6, mode="expand", borderaxespad=0.,
				  frameon=False)
		plt.savefig(os.path.join(output_dir, metric + '.png'), bbox_inches='tight', dpi=96)
		plt.savefig(os.path.join(output_dir, metric + '.svg'), bbox_inches='tight')
		plt.close()

if args.r:
	for directory in os.scandir(args.input_dir):
		print('Plotting metrics for {}'.format(directory.name))
		out = os.path.join(args.output_dir, directory.name)
		os.makedirs(out, exist_ok=True)
		plot_metrics(directory.path, out)
else:
	os.makedirs(args.output_dir, exist_ok=True)
	plot_metrics(args.input_dir, args.output_dir)
