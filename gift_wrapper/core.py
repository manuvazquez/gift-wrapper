import argparse
import pathlib
import collections
import sys

import yaml
from tqdm.autonotebook import tqdm

from . import question
from . import remote
from . import gift
from . import colors
from . import transformer


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

	parser.add_argument(
		'-o', '--overwrite-existing-latex-files', default=False, action='store_true',
		help='overwrite existing latex files if necessary instead of exiting')

	parser.add_argument(
		'-e', '--embed-images', default=False, action='store_true',
		help='embed the images rather than link to them')

	command_line_arguments = parser.parse_args()

	wrap(
		parameters=command_line_arguments.parameters_file.name,
		questions_file=command_line_arguments.input_file.name, local_run=command_line_arguments.local,
		no_checks=command_line_arguments.no_checks,
		overwrite_existing_latex_files=command_line_arguments.overwrite_existing_latex_files,
		embed_images=command_line_arguments.embed_images)


def wrap(
		parameters: str, questions_file: str, local_run: bool, no_checks: bool,
		overwrite_existing_latex_files: bool, embed_images: bool):

	# ================================= parameters' reading

	# if a file name was passed, either as a string or wrapped in a `Pathlib`,...
	if (type(parameters) == str) or (type(parameters) == pathlib.Path):

		# ...it is read
		with open(parameters) as yaml_data:

			parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

	# if a file name was *not* passed...
	else:

		# ...then it should be a dictionary
		assert type(parameters) == dict

	input_file = pathlib.Path(questions_file)

	# ================================= questions' reading

	# the file containing the questions is read
	with open(input_file) as yaml_data:

		input_data = yaml.load(yaml_data, Loader=yaml.FullLoader)

	categories = input_data['categories']
	pictures_base_directory = input_data['pictures base directory']

	# ================================= behaviour

	# temporary file to try and compile latex files
	latex_auxiliary_file = pathlib.Path(parameters['latex']['auxiliary file'])

	# to keep track of files already compiled/transferred
	history = {'already compiled': set(), 'already transferred': set()}

	# lists of processing objects to be applied at the very beginning...
	pre_transforms = [transformer.TexToSvg(history)]

	# ...and at the end
	post_transforms = [
		gift.process_new_lines, transformer.LatexFormulas(latex_auxiliary_file, not no_checks),
		transformer.LatexCommandsWithinText()]

	# if images embedding was requested...
	if embed_images:

		# ...a connection is not needed
		connection = None

		# an object to embed svg files in the output file is added to the list of *post* processors
		post_transforms.append(transformer.SvgToInline())

	# if images are *not* to be embedded...
	else:

		# if "local" running was requested...
		if local_run:

			# ...a "fake" connections is instantiated
			connection = remote.FakeConnection(parameters['images hosting']['copy']['host'])

		# if NO local running was requested...
		else:

			# ...an actual connection with the requested host is opened
			connection = remote.Connection(
				parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

		# an object to copy svg files to a remote location is added to the list of *pre* processors
		pre_transforms.append(transformer.SvgToHttp(
			history, connection, parameters['images hosting']['copy']['public filesystem root'],
			pictures_base_directory, parameters['images hosting']['public URL']))

	# output file has the same name as the input with the ".gift.txt" suffix
	output_file = input_file.with_suffix('.gift.txt')

	# if overwriting files was not requested AND latex checks are enabled AND the given auxiliary file already exists...
	if (not overwrite_existing_latex_files) and (not no_checks) and latex_auxiliary_file.exists():

		print(
			f'{colors.error}latex auxiliary file {colors.reset}"{latex_auxiliary_file}"{colors.error} exists'
			f' and would be overwritten (pass "-o" to skip this check)')
		sys.exit(1)

	# ================================= processing

	with open(output_file, 'w') as f:

		# for every category...
		for cat in tqdm(categories, desc='category', leave=False):

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
			for q in tqdm(cat['questions'], desc='question', leave=False):

				# user settings are tidied up (`q` is modified) to serve as `__init__` parameters for the returned
				# class name...
				class_name = question.user_settings_to_class_init(q)

				# ...which should be available in the `question` module
				question_class = getattr(question, class_name)

				q = question_class(**q, pre_transforms=pre_transforms, post_transforms=post_transforms)

				f.write(f'{q.gift}\n\n')

	print(f'{colors.info}file "{colors.reset}{output_file}{colors.info}" created')

	# if images are *not* to be embedded...
	if not embed_images:

		# if this is a "fake" connection
		if type(connection) == remote.FakeConnection:

			# if there is any file to be copied...
			if connection.files_to_copy:

				print(f'{colors.info}you *should* copy:')

				for source, remote_directory in connection.files_to_copy:

					print(
						f'{source}{colors.info} to '
						f'{colors.reset}{remote_directory}{colors.info} in {colors.reset}{connection.host}')

	# if latex checks are enabled AND some formula was processed...
	if (not no_checks) and latex_auxiliary_file.exists():

		# latex auxiliary files are deleted
		for suffix in ['.tex', '.aux', '.log']:

			latex_auxiliary_file.with_suffix(suffix).unlink()
