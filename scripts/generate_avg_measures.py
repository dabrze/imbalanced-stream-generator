import pandas as pd
import os
import argparse

parser = argparse.ArgumentParser(description='Computes average measures')
parser.add_argument('input_dir', help='The directory to get .csv files from')
parser.add_argument('output_dir', help='The directory to save .csv with average measures')
parser.add_argument('-m', nargs='+', help='The list of metrics to plot')

args = parser.parse_args()

metrics = args.m if args.m is not None else ['G-Mean', 'Kappa', 'Recall' , 'Accuracy', 'AUC', 'sAUC', 'Periodical holdout AUC']
classifier_order = None
data = {}

for directory in os.scandir(args.input_dir):
	classifiers = {os.path.splitext(entry.name)[0]: pd.read_csv(entry.path) for entry in os.scandir(directory.path)}
	if classifier_order is None:
		classifier_order = classifiers.keys()
	data[directory.name] = {name: classifiers[name].mean(axis=0)[metrics] for name in classifiers.keys()}

os.makedirs(args.output_dir, exist_ok=True)
for metric in metrics:
	with open(os.path.join(args.output_dir, metric + '.csv'), 'w') as file:
		file.write(' '.join(['Experiment'] + list(classifier_order)) + '\n')
		for experiment in sorted(data.keys()):
			file.write(' '.join([experiment] + [str(data[experiment][classifier][metric]) for classifier in classifier_order]) + '\n')
