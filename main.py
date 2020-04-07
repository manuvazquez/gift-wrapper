#! /usr/bin/env python3

import argparse
import sys
import pathlib
import logging.config

import yaml
import tqdm

import question
import remote
import gift

# ================================= command line arguments

parser = argparse.ArgumentParser(description='Uncertainty propagation')

parser.add_argument(
	'questions_file', type=argparse.FileType('r'), default='sample_questions.yaml', help='questions file', nargs='?')

command_line_arguments = parser.parse_args(sys.argv[1:])

# the file with the parameters is read
with open('parameters.yaml') as yaml_data:

	parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

questions_file = pathlib.Path(command_line_arguments.questions_file.name)

# the file containing the questions is read
with open(questions_file) as yaml_data:

	categories = yaml.load(yaml_data, Loader=yaml.FullLoader)

connection = remote.Connection(parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])
# connection = remote.FakeConnection()

with open(questions_file.with_suffix('.gift'), 'w') as f:

	for cat in tqdm.tqdm(categories, desc='category'):

		if cat['name']:

			f.write(gift.from_category(cat['name']))

		for q in tqdm.tqdm(cat['questions'], desc='question', leave=False):

			question_class = getattr(question, q['class'])

			# the class is removed from the dictionary so that it doesn't get passed to the initializer
			del q['class']

			q = question.SvgToHttp(
				question.TexToSvg(question_class(**q)), connection,
				parameters['images hosting']['copy']['directory'], parameters['images hosting']['public URL'])

			f.write(f'{q.gift}\n\n')
