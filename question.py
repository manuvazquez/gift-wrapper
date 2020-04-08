import abc
import functools
import re
import pathlib
from typing import Union, Callable, Optional

import gift
import image
import remote


class HtmlQuestion(metaclass=abc.ABCMeta):
	"""
	Abstract class implementing an html-based question.
	"""

	def __init__(self, name: str, statement: str, images_settings: dict, feedback: Optional[str] = None):
		"""
		Initializer.

		Parameters
		----------
		name : str
			Name of the question.
		statement : str
			Statement of the question.
		images_settings : dict
			width and height of *all* the images in the question.
		feedback : str
			Feedback for the question.
		"""

		self.name = name
		self.statement = statement.rstrip()
		self.feedback = feedback

		assert ('width' in images_settings) and ('height' in images_settings),\
			'"width" and/or "height" missing in "image_settings"'

		self.images_width, self.images_height = images_settings['width'], images_settings['height']

		self.processing_functions = [
			functools.partial(gift.process_url_images, width=self.images_width, height=self.images_width),
			gift.process_new_lines, gift.process_latex
		]

		# this might be tampered with by subclasses/decorator
		self.pre_processing_functions = []

	def process_text(self, text: str) -> str:
		"""
		Functions in `self.processing_functions` are applied on the given input.

		Parameters
		----------
		text : str
			Input text.

		Returns
		-------
		out: str
			Text processed with the previously defined functions.

		"""

		for function in (self.pre_processing_functions + self.processing_functions):

			text = function(text)

		return text

	@property
	def gift(self):
		"""
		Builds the question in the GIFT format.

		Returns
		-------
		out: str
			GIFT-ready text.

		"""

		# feedback part of the answer if any
		feedback = ("\n\t" + gift.from_feedback(self.process_text(self.feedback.rstrip()))) if self.feedback else ""

		# the full answer
		answer = f'{{\n{self.answer + feedback}\n}}'

		return gift.from_question_name(self.name) + gift.html + self.process_text(self.statement) + answer

	def __repr__(self):

		return f'Name: {self.name}\nStatement: {self.statement}'

	@property
	@abc.abstractmethod
	def answer(self):
		"""
		Abstract method yielding the GIFT-ready answer to the question.

		Returns
		-------
		out: str
			GIFT-ready text with the answer.

		"""

		pass


class Numerical(HtmlQuestion):
	"""
	Class implementing a numerical question.
	"""

	def __init__(
			self, name: str, statement: str, images_settings: dict, solution: dict, feedback: Optional[str] = None):

		super().__init__(name, statement, images_settings, feedback)

		assert ('value' in solution), '"value" missing in "solution"'

		self.solution_value = str(solution['value'])
		self.solution_error = ':' + str(solution['error']) if 'error' in solution else ''

	def __repr__(self):

		error = f' (error: {self.solution_error[1:]})' if self.solution_error != '' else ''

		return super().__repr__() + '\n' + f'Solution: {self.solution_value}' + error

	@property
	def answer(self):

		return '\t=%100%' + self.solution_value + self.solution_error + '#'


class MultipleChoice(HtmlQuestion):
	"""
	Class implementing a multiple-choice question.
	"""

	def __init__(self, name: str, statement: str, images_settings: dict, answers: dict, feedback: Optional[str] = None):

		super().__init__(name, statement, images_settings, feedback)

		self.answers = answers

	@property
	def answer(self):

		processed_answers = ['=' + self.answers['perfect']]

		for a in self.answers['wrong']:

			# if it is a list
			if isinstance(a, list):

				processed_answers.append(f'~%{a[1]}%{self.process_text(a[0])}')

			# if it is a scalar
			else:

				processed_answers.append(f'~{self.process_text(a)}')

		return '\t' + '\n\t'.join(processed_answers)


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

	@staticmethod
	def transform_files(
			text: str, pattern: str, process_match: Callable[[str], None],
			replacement: Union[str, Callable[[re.Match], str]]):

		# all the matching files in the given text
		files = re.findall(pattern, text)

		# breakpoint()

		# every one of them...
		for file in files:

			# ...is processed
			process_match(file)

		# replacement of matches
		return re.sub(pattern, replacement, text)


class TexToSvg(QuestionDecorator):

	def __init__(self, decorated: HtmlQuestion):

		super().__init__(decorated)

		# a new pre-processing function is appended (the "\1" in `replacement` refers to matches in `pattern`)
		self.pre_processing_functions.append(functools.partial(
			self.transform_files, pattern='(\S+)\.tex', process_match=lambda x: image.pdf_to_svg(image.compile_tex(x)),
			replacement=r'\1.svg'))


class SvgToHttp(QuestionDecorator):

	def __init__(self, decorated: HtmlQuestion, connection: remote.Connection, directories: dict, public_url: str):

		super().__init__(decorated)

		assert ('public filesystem root' in directories) and ('subdirectory' in directories)

		# make a new directory if necessary
		connection.make_directory_at(directories['subdirectory'], directories['public filesystem root'])

		# assembled remote path
		remote_subdirectory = pathlib.Path(directories['public filesystem root']).joinpath(directories['subdirectory'])

		def replacement_function(m: re.Match) -> str:

			file = pathlib.Path(m.group(0))

			return public_url + directories['subdirectory'] + '/' + file.as_posix()

		# a new pre-processing function is appended
		self.pre_processing_functions.append(functools.partial(
			self.transform_files, pattern='(?<!\S)(?!http)(\S+\.svg)\??(?!\S)',
			process_match=lambda f: connection.copy(f, remote_directory=remote_subdirectory / pathlib.Path(f).parent),
			replacement=replacement_function))
