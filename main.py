#! /usr/bin/env python3

import argparse
import sys
import logging.config

import yaml

import question
import remote
import image

# ================================= command line arguments

parser = argparse.ArgumentParser(description='Uncertainty propagation')

parser.add_argument(
	'questions_file', type=argparse.FileType('r'), default='sample_questions.yaml', help='questions file', nargs='?')

command_line_arguments = parser.parse_args(sys.argv[1:])

with open('parameters.yaml') as yaml_data:

	parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

connection = remote.Connection(parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

with open(command_line_arguments.questions_file.name) as yaml_data:

	questions = yaml.load(yaml_data, Loader=yaml.FullLoader)

# i_question = 0
# i_question = 1
i_question = 2

question_class = getattr(question, questions[i_question]['class'])

# the class is removed from the dictionary so that it doesn't get passed to the initializer
del questions[i_question]['class']

# q = question.TexToSvg(question_class(**questions[i_question]))
q = question.SvgToHttp(
	question.TexToSvg(question_class(**questions[i_question])), connection,
	parameters['images hosting']['copy']['directory'], parameters['images hosting']['public URL'])

with open('out.txt', 'w') as f:

	f.write(q.gift)

# connection.copy('out.txt', parameters['images hosting']['copy']['directory'])

# res = image.compile_tex('pictures/constellation.tex')
# res = image.compile_tex('pictures/quixote.tex')
