#! /usr/bin/env python3

import argparse
import sys
import pathlib
import collections

import yaml
import tqdm

import question
import remote
import gift

# ================================= command line arguments

parser = argparse.ArgumentParser(description='GIFT-wrapper')

parser.add_argument(
	'-p', '--parameters_file', type=argparse.FileType('r'), default='parameters.yaml', help='parameters file', nargs='?')

parser.add_argument(
	'-q', '--questions_file', type=argparse.FileType('r'), default='bank.yaml', help='questions file', nargs='?')

parser.add_argument(
	'-l', '--local', default=False, action='store_true', help="don't try to copy the images to the server")

command_line_arguments = parser.parse_args(sys.argv[1:])

# ================================= parameters' reading

# the file with the parameters is read
with open(command_line_arguments.parameters_file.name) as yaml_data:

	parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

questions_file = pathlib.Path(command_line_arguments.questions_file.name)

# ================================= questions' reading

# the file containing the questions is read
with open(questions_file) as yaml_data:

	categories = yaml.load(yaml_data, Loader=yaml.FullLoader)

# =================================

# if "local" running was requested...
if command_line_arguments.local:

	# ...a "fake" connections is instantiated
	connection = remote.FakeConnection()

# if NO local running was requested...
else:

	# ...an actual connection with the requested host is opened
	connection = remote.Connection(parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

# output file has the same name as the input with the ".gift" suffix
output_file = questions_file.with_suffix('.gift')

with open(output_file, 'w') as f:

	# for every category...
	for cat in tqdm.tqdm(categories, desc='category'):

		# if a name was actually provided...
		if cat['name']:

			f.write(gift.from_category(cat['name']))

		# the names of *all* the questions
		all_names = [q['name'] for q in cat['questions']]

		# list with names that show up more than once
		duplicates = [name for name, count in collections.Counter(all_names).items() if count > 1]

		# all the names should be different
		assert not duplicates, f'duplicates in category {cat["name"]}: {duplicates}'

		# for every question in the category...
		for q in tqdm.tqdm(cat['questions'], desc='question', leave=False):

			# that class that will be instantiated for this particular question
			question_class = getattr(question, q['class'])

			# if field `images_settings` is not present...
			if 'images_settings' not in q:

				# `None` values for width and height are assumed (meaning automatic size adjustment)
				q['images_settings'] = {'width': None, 'height': None}

			# the class is removed from the dictionary so that it doesn't get passed to the initializer
			del q['class']

			# question is instantiated and decorated
			q = question.SvgToHttp(
				question.TexToSvg(question_class(**q)), connection,
				parameters['images hosting']['copy']['directories'], parameters['images hosting']['public URL'])

			f.write(f'{q.gift}\n\n')

print(f'file "{output_file}" created')