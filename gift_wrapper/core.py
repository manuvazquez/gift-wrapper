import argparse
import pathlib
import collections

import yaml
from tqdm.autonotebook import tqdm

from . import question
from . import remote
from . import gift
from . import colors
from . import transformer

def main():
	"""Processes command-line arguments and feeds them to `wrap`.
	"""

	parser = argparse.ArgumentParser(description='Build GIFT files (Moodle) from a simple specification')

	parser.add_argument(
		'-p', '--parameters_file', default='parameters.yaml', help='parameters file',
		nargs='?')

	parser.add_argument(
		'-i', '--input_file', default='bank.yaml', help='questions file', nargs='?')

	parser.add_argument(
		'-l', '--local', default=False, action='store_true', help="don't try to copy the images to the server")

	parser.add_argument(
		'-n', '--no-checks', default=False, action='store_true', help="don't check LaTeX formulas (much faster)")

	parser.add_argument(
		'-e', '--embed-images', default=False, action='store_true',
		help='embed the images rather than link to them')

	command_line_arguments = parser.parse_args()
	
	wrap(
		parameters=command_line_arguments.parameters_file,
		questions_file=command_line_arguments.input_file, local_run=command_line_arguments.local,
		no_checks=command_line_arguments.no_checks,
		embed_images=command_line_arguments.embed_images)


def wrap(parameters: str, questions_file: str, local_run: bool, no_checks: bool, embed_images: bool):
	"""Builds a gift file.

	Parameters
	----------
	parameters : str
		Parameters
	questions_file : str
		Input file encompassing the questions
	local_run : bool
		If `True`, images are not copied over to a server
	no_checks : bool
		If `True`, LaTeX formulas are not checked
	embed_images : bool
		If `True`, images are embedded
	"""

	# ================================= parameters' reading

	# if a file name was passed, either as a string or wrapped in a `Pathlib`,...
	if isinstance(parameters, (str, pathlib.Path)):

		# so that we can assume it is a `pathlib.Path`
		parameters = pathlib.Path(parameters)

		# if a parameters file is NOT present...
		if not parameters.exists():
			
			# ...images are embedded
			embed_images = True

			print(
				f'"{parameters}"{colors.info} not found: embedding the images (`-e`). If you\'d like to host your images in a remote server you can download the sample parameters file{colors.reset} '
				r'https://raw.githubusercontent.com/manuvazquez/gift-wrapper/master/parameters.yaml'
				' and tweak it to your needs'
				)

			# it shouldn't be used anywhere, but just in case...
			parameters = None
		
		# if a parameters file IS present...
		else:

			# ...it is read
			with parameters.open() as yaml_data:

				parameters = yaml.load(yaml_data, Loader=yaml.FullLoader)

	# if a file name was *not* passed...
	else:

		# ...then it should be a dictionary
		assert isinstance(parameters, dict), 'passed `parameters` is not a file nor a dictionary'

	input_file = pathlib.Path(questions_file)

	# if the questions file doesn't exist...
	if not input_file.exists():

		raise SystemExit(
			f'"{input_file}" {colors.error}cannot be found: you can download a sample from{colors.reset} '
			r'https://raw.githubusercontent.com/manuvazquez/gift-wrapper/master/bank.yaml'
			)

	# ================================= questions' reading

	# the file containing the questions is read
	with open(input_file) as yaml_data:

		input_data = yaml.load(yaml_data, Loader=yaml.FullLoader)

	categories = input_data['categories']
	pictures_base_directory = input_data['pictures base directory']

	# ================================= behavior

	# to keep track of files already compiled/transferred
	history = {'already compiled': set(), 'already transferred': set()}

	# lists of processing objects to be applied at the very beginning...
	pre_transforms = [transformer.TexToSvg(history)]

	# ...and at the end
	post_transforms = [
		gift.process_new_lines, transformer.LatexFormulas(not no_checks),
		transformer.LatexCommandsWithinText()]

	# if images are *not* to be embedded, and this is *not* a local run (i.e., if images are supposed to be hosted remotely)...
	if (not embed_images) and (not local_run):

		# an object to handle the connection with the requested host is instantiated
		connection = remote.Connection(
				parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

		# an attempt is made...
		try:

			# ...to connect
			connection.connect()

		except remote.CannotConnectException:
		
			print(f'{colors.info}cannot establish a connection: embedding the images (`-e`){colors.reset}')

			embed_images = True

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

			# ...a "fake" connection is instantiated
			connection = remote.FakeConnection(parameters['images hosting']['copy']['host'])

		# # if *no* local running was requested...
		# else:

		# 	# ...an actual connection with the requested host is opened
		# 	connection = remote.Connection(
		# 		parameters['images hosting']['copy']['host'], **parameters['images hosting']['ssh'])

		# an object to copy svg files to a remote location is added to the list of *pre* processors
		pre_transforms.append(transformer.SvgToHttp(
			history, connection, parameters['images hosting']['copy']['public filesystem root'],
			pictures_base_directory, parameters['images hosting']['public URL']))

	# output file has the same name as the input with the ".gift.txt" suffix
	output_file = input_file.with_suffix('.gift.txt')

	# ================================= processing

	with open(output_file, 'w') as f:

		# for every category...
		for cat in tqdm(categories, desc='category', leave=False):

			# if "something" was actually provided...
			if cat['name']:

				# ...if it's *not* a list...
				if not isinstance(cat['name'], list):

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

	# if images are *not* to be embedded, this is a "local" run (fake connection), and there are files to be copied...
	if (not embed_images) and local_run and connection.files_to_copy:

		print(f'{colors.info}you *should* copy:')

		for source, remote_directory in connection.files_to_copy:

			print(
				f'{source}{colors.info} to '
				f'{colors.reset}{remote_directory}{colors.info} in {colors.reset}{connection.host}')
