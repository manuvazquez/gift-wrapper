#! /usr/bin/env python3

import argparse
import sys
import re
import pathlib
import logging.config

import yaml

import gift
import question

# ================================= command line arguments

parser = argparse.ArgumentParser(description='Uncertainty propagation')

parser.add_argument(
	'questions_file', type=argparse.FileType('r'), default='sample_questions.yaml', help='questions file', nargs='?')

command_line_arguments = parser.parse_args(sys.argv[1:])

with open(command_line_arguments.questions_file.name) as yaml_data:

	questions = yaml.load(yaml_data, Loader=yaml.FullLoader)

# i_question = 0
i_question = 1

question_class = getattr(question, questions[i_question]['class'])

# the class is removed from the dictionary so that it doesn't get passed to the initializer
del questions[i_question]['class']

q = question_class(**questions[i_question])

with open('out.txt', 'w') as f:

	f.write(q.gift)
