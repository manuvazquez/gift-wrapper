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

i_question = 0

q = question.Numerical(**questions[i_question])

res = gift.from_image_url('http://www.tsc.uc3m.es/~mvazquez/foo.svg', 200, 300)

test = 'http://www.tsc.uc3m.es/~mvazquez/foo.svg' + ' bla bla ' + 'http://www.tsc.uc3m.es/~mvazquez/foo.svg'
res2 = gift.process_url_images(test, 20, 10)

with open('out.txt', 'w') as f:

	f.write(res)
