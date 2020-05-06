import sys
import abc
import functools
import re
import pathlib
from typing import Union, Callable, Optional

from . import gift
from . import image
from . import remote
from . import colors

# regular expression to extract a percentage
re_percentage = re.compile('(\d*\.\d+|\d+)\s*%')


class HtmlQuestion(metaclass=abc.ABCMeta):
	"""
	Abstract class implementing an html-based question.
	"""

	def __init__(
			self, name: str, statement: str, images_settings: dict, history: dict, check_latex_formulas: bool,
			latex_auxiliary_file: Union[str, pathlib.Path], feedback: Optional[str] = None):
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
		self.history = history

		assert ('width' in images_settings) and ('height' in images_settings),\
			'"width" and/or "height" missing in "image_settings"'

		self.images_width, self.images_height = images_settings['width'], images_settings['height']

		self.processing_functions = [
			functools.partial(gift.process_url_images, width=self.images_width, height=self.images_height),
			gift.process_new_lines, functools.partial(
				gift.process_latex, latex_auxiliary_file=latex_auxiliary_file, check_compliance=check_latex_formulas)
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

			try:

				text = function(text)

			except gift.NotCompliantLatexFormula as e:

				print(
					f'\n{colors.error}cannot compile latex formula\n {colors.extra_info}{e.formula}{colors.reset} in '
					f'{colors.info}{self.name}')

				sys.exit(1)

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

	def to_jupyter(self):

		feedback = ('# Feedback\n' + self.feedback.rstrip()) if self.feedback else ''

		return f'# Statement\n{self.statement}\n{feedback}\n'


class Numerical(HtmlQuestion):
	"""
	Class implementing a numerical question.
	"""

	def __init__(
			self, name: str, statement: str, images_settings: dict, history: dict, check_latex_formulas: bool,
			latex_auxiliary_file: Union[str, pathlib.Path], solution: dict, feedback: Optional[str] = None):

		super().__init__(
			name, statement, images_settings, history, check_latex_formulas, latex_auxiliary_file, feedback)

		assert ('value' in solution), '"value" missing in "solution"'

		self.solution_value = str(solution['value'])

		if 'error' in solution:

			self.solution_error = ':'

			# try to match a percentage
			m = re_percentage.match(str(solution['error']))

			# if so...
			if m:

				self.solution_error += str(solution['value'] * float(m.group(1)) / 100.)

			else:

				self.solution_error += str(solution['error'])

		# an error was NOT provided
		else:

			self.solution_error = ''

	def __repr__(self):

		error = f' (error: {self.solution_error[1:]})' if self.solution_error != '' else ''

		return super().__repr__() + '\n' + f'Solution: {self.solution_value}' + error

	@property
	def answer(self):

		return '#\t=%100%' + self.solution_value + self.solution_error + '#'

	def to_jupyter(self):

		res = super().to_jupyter()

		return res + f'# Solution\n {self.solution_value} (error: {self.solution_error[1:]})\n'


class MultipleChoice(HtmlQuestion):
	"""
	Class implementing a multiple-choice question.
	"""

	def __init__(
			self, name: str, statement: str, images_settings: dict, history: dict, check_latex_formulas: bool,
			latex_auxiliary_file: Union[str, pathlib.Path], answers: dict, feedback: Optional[str] = None):

		super().__init__(
			name, statement, images_settings, history, check_latex_formulas, latex_auxiliary_file, feedback)

		self.answers = answers

	@property
	def answer(self):

		processed_answers = ['=' + self.process_text(self.answers['perfect'])]

		for a in self.answers['wrong']:

			# if it is a list
			if isinstance(a, list):

				processed_answers.append(f'~%{a[1]}%{self.process_text(a[0])}')

			# if it is a scalar
			else:

				processed_answers.append(f'~{self.process_text(a)}')

		return '\t' + '\n\t'.join(processed_answers)

	def to_jupyter(self):

		res = super().to_jupyter()

		res += '# Choices\n'

		res += f'* {self.answers["perfect"]}\n'

		for a in self.answers['wrong']:

			if isinstance(a, list):

				res += f'* {a[0]}\n'

			else:

				res += f'* {a}\n'

		return res


# ========================================== Decorators

class QuestionDecorator:
	"""
	Abstract class to implement a question decorator.
	"""

	def __init__(self, decorated: Union[HtmlQuestion, 'QuestionDecorator']):

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

	# TODO: when minimum Python version is forwarded to 3.8, `[re.Match]` should replace `...` as the the signature
	#  of the `Callable` in the type hinting for `replacement`
	@staticmethod
	def transform_files(
			text: str, pattern: str, process_match: Callable[[str], None],
			replacement: Union[str, Callable[..., str]]):
		"""
		It searches in a text for strings corresponding to files (maybe including a path), replaces them by another
		string according to some function and, additionally, processes each file according to another function.

		Parameters
		----------
		text : str
			Input text.
		pattern : str
			Regular expression including a capturing group that yields the file.
		process_match : Callable[[str], None]
			Function that will *process* each file.
		replacement : str or Callable[[re.Match], str]
			Regular expression making use of the capturing group or function processing the match delivered by `pattern`

		Returns
		-------
		out: str
			Output text with the replacements performed, after having processed all the files.

		"""

		# all the matching files in the given text
		files = re.findall(pattern, text)

		# every one of them...
		for file in files:

			# ...is processed
			process_match(file)

		# replacement of matches
		return re.sub(pattern, replacement, text)


class TexToSvg(QuestionDecorator):
	"""
	Decorator to converts TeX files into svg files.
	"""

	def __init__(self, decorated: Union[HtmlQuestion, QuestionDecorator]):

		super().__init__(decorated)

		def process_match(f):

			# if this file has not been already compiled-converted...
			if f not in self.history['already compiled']:

				# ...it is...
				image.pdf_to_svg(image.tex_to_pdf(f))

				# ...and a note is made of it
				self.history['already compiled'].add(f)

			# else:
			#
			# 	print(f'{f} already compiled-converted...')

		# a new pre-processing function is attached to the corresponding list
		# (the "\1" in `replacement` refers to matches in `pattern`)
		self.pre_processing_functions.append(functools.partial(
			self.transform_files, pattern='(\S+)\.tex', process_match=process_match, replacement=r'\1.svg'))


class SvgToHttp(QuestionDecorator):
	"""
	Decorator to transfer svg files to a remote location.
	"""

	def __init__(
			self, decorated: Union[HtmlQuestion, QuestionDecorator], connection: remote.Connection,
			public_filesystem_root: str, pictures_base_directory: str, public_url: str):

		super().__init__(decorated)

		# make a new directory if necessary
		connection.make_directory_at(pictures_base_directory, public_filesystem_root)

		# assembled remote path
		remote_subdirectory = pathlib.Path(public_filesystem_root).joinpath(pictures_base_directory)

		# TODO: when minimum Python version is forwarded to 3.8, `re.Match` should be the type hinting for `m`
		def replacement_function(m) -> str:

			file = pathlib.Path(m.group(0))

			return public_url + pictures_base_directory + '/' + file.as_posix()

		def process_match(f):

			# if this file has not been already transferred...
			if f not in self.history['already transferred']:

				# ...it is...
				connection.copy(f, remote_directory=remote_subdirectory / pathlib.Path(f).parent)

				# ...and a note is made of it
				self.history['already transferred'].add(f)

			# else:
			#
			# 	print(f'{f} already transferred...')

		# a new pre-processing function is attached to the corresponding list
		self.pre_processing_functions.append(functools.partial(
			self.transform_files, pattern='(?<!\S)(?!http)(\S+\.svg)\??(?!\S)',
			process_match=process_match, replacement=replacement_function))


class SvgToMarkdown(QuestionDecorator):
	"""
	Decorator to reformat svg files for including them in markdown strings.
	"""

	def __init__(self, decorated: Union[HtmlQuestion, QuestionDecorator]):

		super().__init__(decorated)

		def process_match(f):

			pass

		# a new pre-processing function is attached to the corresponding list
		self.pre_processing_functions.append(functools.partial(
			self.transform_files, pattern='(\S+)\.svg',
			process_match=process_match, replacement=r'![](' + r'\1' + '.svg)'))
