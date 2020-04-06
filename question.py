import abc
import functools
import re
import pathlib
from typing import Union, Callable

import gift
import image
import remote


class HtmlQuestion(metaclass=abc.ABCMeta):

	def __init__(self, name: str, statement: str, images_settings: dict):

		self.name = name
		self.statement = statement.rstrip()

		assert ('width' in images_settings) and ('height' in images_settings),\
			'"width" and/or "height" missing in "image_settings"'

		self.images_width, self.images_height = images_settings['width'], images_settings['height']

		self.processing_functions = [
			functools.partial(gift.process_url_images, width=self.images_width, height=self.images_width),
			gift.process_new_lines, gift.process_latex
		]

	@property
	def gift(self):

		# for the sake of convenience (easily reordering the steps below)
		processed_statement = self.statement

		for function in self.processing_functions:

			processed_statement = function(processed_statement)

		return gift.from_question_name(self.name) + gift.html + processed_statement + self.answer

	def __repr__(self):

		return f'Name: {self.name}\nStatement: {self.statement}'

	@property
	@abc.abstractmethod
	def answer(self):

		pass


class Numerical(HtmlQuestion):

	def __init__(self, name: str, statement: str, images_settings: dict, solution: dict):

		super().__init__(name, statement, images_settings)

		assert ('value' in solution), '"value" missing in "solution"'

		self.solution_value = str(solution['value'])
		self.solution_error = ':' + str(solution['error']) if 'error' in solution else ''

	def __repr__(self):

		error = f' (error: {self.solution_error[1:]})' if self.solution_error != '' else ''

		return super().__repr__() + '\n' + f'Solution: {self.solution_value}' + error

	@property
	def answer(self):

		return '{\n\t=%100%' + self.solution_value + self.solution_error + '#\n}'


class MultipleChoice(HtmlQuestion):

	def __init__(self, name: str, statement: str, images_settings: dict, answers: dict):

		super().__init__(name, statement, images_settings)

		self.processed_answers = ['=' + answers['perfect']]

		for a in answers['wrong']:

			# if it is a list
			if isinstance(a, list):

				self.processed_answers.append(f'~%{a[1]}%{a[0]}')

			# if it is a scalar
			else:

				self.processed_answers.append(f'~{a}')

	@property
	def answer(self):

		return '{\n\t' + '\n\t'.join(self.processed_answers) + '\n}'


# ========================================== Decorators

class QuestionDecorator:

	def __init__(self, decorated: HtmlQuestion):

		self._decorated = decorated

	# any method/attribute not implemented here...
	def __getattr__(self, item):

		# ...is relayed to the *decorated* object
		return getattr(self._decorated, item)

	def __setattr__(self, key, value):

		# except for the `_decorated` attribute...
		if key == '_decorated':
			object.__setattr__(self, key, value)
		# ...everything else...
		else:
			# ...is relayed to the decorated object
			setattr(self._decorated, key, value)

	def transform_files(
			self, pattern: str, process_match: Callable[[str], None],
			replacement: Union[str, Callable[[re.Match], str]]):

		# all the matching files in the statement of the problem
		files = re.findall(pattern, self._decorated.statement)

		# every one of them...
		for file in files:

			# ...is processed
			process_match(file)

		# extension of TeX files is changed to pdf
		self._decorated.statement = re.sub(pattern, replacement, self._decorated.statement)


class TexToSvg(QuestionDecorator):

	def __init__(self, decorated: HtmlQuestion):

		super().__init__(decorated)

		self.transform_files('(\S*)\.tex', lambda x: image.pdf_to_svg(image.compile_tex(x)), r'\1.svg')


class SvgToHttp(QuestionDecorator):

	def __init__(self, decorated: HtmlQuestion, connection: remote.Connection, remote_directory: dict, public_url: str):

		super().__init__(decorated)

		assert ('base' in remote_directory) and ('subdirectory' in remote_directory)

		# make a new directory if necessary
		connection.make_directory_at(remote_directory['subdirectory'], remote_directory['base'])

		assert pathlib.Path(remote_directory['subdirectory']).parent.as_posix() == '.',\
			f'subdirectory, "{remote_directory["subdirectory"]}" ,should have a single component'

		# assembled remote path
		assembled_path = pathlib.Path(remote_directory['base']).joinpath(remote_directory['subdirectory'])

		# when replacing the file in the text, we need `public_url`/`remote_directory['subdirectory']`/<file name>
		# meaning that the local directory in which the files are stored corresponds to remote directory
		# `remote_directory['subdirectory']`
		self.transform_files(
			'(\S*\.svg)', functools.partial(connection.copy, remote_directory=assembled_path.as_posix()),
			lambda m: public_url + (
					assembled_path.relative_to(remote_directory['base']) / pathlib.Path(m.group(0)).name).as_posix())
