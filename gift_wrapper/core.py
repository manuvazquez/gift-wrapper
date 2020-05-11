import argparse
import pathlib
import collections
import sys

import yaml
# import tqdm
from tqdm.autonotebook import tqdm

from . import question
from . import remote
from . import gift
from . import colors


def main():

	parser = argparse.ArgumentParser(description='Build GIFT files (Moodle) from a simple specification')

	parser.add_argument(
		'-p', '--parameters_file', type=argparse.FileType('r'), default='parameters.yaml', help='parameters file',
		nargs='?')

	parser.add_argument(
		'-i', '--input_file', type=argparse.FileType('r'), default='bank.yaml', help='questions file', nargs='?')

	parser.add_argument(
		'-l', '--local', default=False, action='store_true', help="don't try to copy the images to the server")

	parser.add_argument(
		'-n', '--no-checks', default=False, action='store_true', help="don't check latex formulas (much faster)")

	command_line_arguments = parser.parse_args()

	wrap(
		parameters_file=command_line_arguments.parameters_file.name,
		questions_file=command_line_arguments.input_file.name, local_run=command_line_arguments.local,
		no_checks=command_line_arguments.no_checks)


def wrap(parameters_file: str, questions_file: str, local_run: bool, no_checks: bool):

	# ================================= parameters' reading

	# the file with the parameters is read
	with open(parameters_file) as yaml_data:

		parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

	input_file = pathlib.Path(questions_file)

	# ================================= questions' reading

	# the file containing the questions is read
	with open(input_file) as yaml_data:

		input_data = yaml.load(yaml_data, Loader=yaml.FullLoader)

	categories = input_data['categories']
	pictures_base_directory = input_data['pictures base directory']

	# =================================

	# if "local" running was requested...
	if local_run:

		# ...a "fake" connections is instantiated
		connection = remote.FakeConnection(parameters['images hosting']['copy']['host'])

	# if NO local running was requested...
	else:

		# ...an actual connection with the requested host is opened
		connection = remote.Connection(
			parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

	# output file has the same name as the input with the ".gift.txt" suffix
	output_file = input_file.with_suffix('.gift.txt')

	# to keep track of files already compiled/transferred
	history = {'already compiled': set(), 'already transferred': set()}

	latex_auxiliary_file = pathlib.Path(parameters['latex']['auxiliary file'])

	# if latex checks are enabled and the given auxiliary file already exists...
	if (not no_checks) and latex_auxiliary_file.exists():

		print(
			f'{colors.error}latex auxiliary file {colors.reset}"{latex_auxiliary_file}"{colors.error} exists'
			f' (and would be overwritten)')
		sys.exit(1)

	with open(output_file, 'w') as f:

		# for every category...
		for cat in tqdm(categories, desc='category'):

			# if "something" was actually provided...
			if cat['name']:

				# ...if it's *not* a list...
				if type(cat['name']) != list:

					# ...it is turned into one
					cat['name'] = [cat['name']]

				for c in cat['name']:

					f.write(gift.from_category(c))

			# the names of *all* the questions
			all_names = [q['name'] for q in cat['questions']]

			# list with names that show up more than once
			duplicates = [name for name, count in collections.Counter(all_names).items() if count > 1]

			# all the names should be different
			assert not duplicates, f'{colors.error}duplicates in category {colors.reset}{cat["name"]}: {duplicates}'

			# for every question in the category...
			for q in tqdm(cat['questions'], desc='question', leave=True):

				# the class that will be instantiated for this particular question
				question_class = getattr(question, q['class'])

				# if field `images_settings` is not present...
				if 'images_settings' not in q:

					# `None` values for width and height are assumed (meaning automatic size adjustment)
					q['images_settings'] = {'width': None, 'height': None}

				# the class is removed from the dictionary so that it doesn't get passed to the initializer
				del q['class']

				# whether or not latex formulas should be checked...
				q['check_latex_formulas'] = not no_checks

				# ...if so, this auxiliary file will be used (created)
				q['latex_auxiliary_file'] = latex_auxiliary_file

				# "history" is passed
				q['history'] = history

				# question is instantiated and "decorated"
				q = question.SvgToHttp(
					question.TexToSvg(
						question_class(**q)
					), connection, parameters['images hosting']['copy']['public filesystem root'],
					pictures_base_directory, parameters['images hosting']['public URL'])

				f.write(f'{q.gift}\n\n')

	print(f'{colors.info}file "{colors.reset}{output_file}{colors.info}" created')

	# if this is a "fake" connection
	if type(connection) == remote.FakeConnection:

		# if there is any file to be copied...
		if connection.files_to_copy:

			print(f'{colors.info}you *should* copy:')

			for source, remote_directory in connection.files_to_copy:

				print(
					f'{source}{colors.info} to '
					f'{colors.reset}{remote_directory}{colors.info} in {colors.reset}{connection.host}')

	# if latex checks are enabled *and* some formula was processed...
	if (not no_checks) and latex_auxiliary_file.exists():

		# latex auxiliary files are deleted
		for suffix in ['.tex', '.aux', '.log']:

			latex_auxiliary_file.with_suffix(suffix).unlink()
