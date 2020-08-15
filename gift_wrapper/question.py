import sys
import abc
import functools
import pathlib
import string
from typing import Union, Optional

from . import gift
from . import colors
from . import latex
from . import parsing


def user_settings_to_class_init(
		settings: dict, name: Optional[str] = None, check_latex_formulas: bool = False,
		latex_auxiliary_file: str = '__latex__.tex') -> str:
	"""
	Turns a user settings dictionary into one that can be passed to a question's  `__init__`.

	Parameters
	----------
	settings : dict
		User settings.
	name : str, optional
		The name of the question.
	check_latex_formulas : bool
		If True latex formulas will be checked.
	latex_auxiliary_file : str
		The name of the auxiliary latex file to be used for checks.

	Returns
	-------
	out: str
		The name of the class to be instantiated.

	"""

	# the input dictionary is modified in-place
	settings['check_latex_formulas'] = check_latex_formulas
	settings['latex_auxiliary_file'] = latex_auxiliary_file

	if name:
		settings['name'] = name

	return settings.pop('class')


class HtmlQuestion(metaclass=abc.ABCMeta):
	"""
	Abstract class implementing an html-based question.
	"""

	def __init__(
			self, name: str, statement: str, check_latex_formulas: bool, latex_auxiliary_file: Union[str, pathlib.Path],
			images_settings: Optional[dict] = None, feedback: Optional[str] = None, time: Optional[int] = None,
			pre_processors: list = [], post_processors: list = []):
		"""
		Initializer.

		Parameters
		----------
		name : str
			Name of the question.
		statement : str
			Statement of the question.
		check_latex_formulas: bool
			Whether or not an attempt should be made to compile every latex formula to detect errors.
		latex_auxiliary_file: str or Pathlib
			The latex file that will be created to check the formulas.
		images_settings : dict, optional
			width and height of *all* the images in the question.
		feedback : str, optional
			Feedback for the question.
		time: int, optional
			The number of minutes deemed necessary to answer the question.
		pre_processors: list
			Processors to apply before everything else.
		post_processors: list
			Processors to apply in the end.
		"""

		self.name = name
		self.statement = statement.rstrip()
		self.feedback = feedback
		self.time = time
		self.pre_processors = pre_processors
		self.post_processors = post_processors

		if images_settings is None:

			self.images_width, self.images_height = None, None

		else:

			assert ('width' in images_settings) and ('height' in images_settings), \
				'"width" and/or "height" missing in "image_settings"'

			self.images_width, self.images_height = images_settings['width'], images_settings['height']

		self.processing_functions = [
			functools.partial(gift.process_url_images, width=self.images_width, height=self.images_height),
			gift.process_new_lines, functools.partial(
				gift.process_latex, latex_auxiliary_file=latex_auxiliary_file, check_compliance=check_latex_formulas)
		]

		# functions to process LaTeX commands *in text* (ignoring occurrences in formulas)...
		latex_text_processing_functions = [functools.partial(
			latex.replace_and_replace_only_in_formulas, *l) for l in parsing.latex_in_text_substitutions]

		# ...are added to the pool
		self.processing_functions += latex_text_processing_functions

		# these might be tampered with by subclasses/decorators
		self.pre_processing_functions = []
		self.post_processing_functions = []

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

		for function in (self.pre_processors + self.processing_functions + self.post_processors):

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

		# so that the original statement is not modified
		statement = self.statement

		# feedback part of the answer if any
		feedback = ("\n\t" + gift.from_feedback(self.process_text(self.feedback.rstrip()))) if self.feedback else ""

		# the full answer
		answer = f'{{\n{self.answer + feedback}\n}}'

		# if a `time` estimate was passed...
		if self.time:

			# ...it is appended at the end of the statement
			statement += '\n\n\n' + r'<i>Estimated time\: ' + str(self.time) + r' minutes</i>' + '\n'

		return gift.from_question_name(self.name) + gift.html + self.process_text(statement) + answer

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
			self, name: str, statement: str, check_latex_formulas: bool, latex_auxiliary_file: Union[str, pathlib.Path],
			solution: dict, images_settings: Optional[dict] = None, feedback: Optional[str] = None,
			time: Optional[int] = None, pre_processors: list = [], post_processors: list = []):
		"""
		Initializer.

		Parameters
		----------
		solution : dict
			Value and, optionally, tolerated error of the solution.
		"""

		super().__init__(
			name, statement, check_latex_formulas, latex_auxiliary_file, images_settings, feedback, time,
			pre_processors, post_processors)

		assert ('value' in solution), '"value" missing in "solution"'

		self.solution_value = solution['value']

		if 'error' in solution:

			# try to match a percentage
			m = parsing.re_percentage.match(str(solution['error']))

			# if so...
			if m:

				self.solution_error = str(solution['value'] * float(m.group(1)) / 100.)

			else:

				self.solution_error = str(solution['error'])

		# an error was NOT provided
		else:

			self.solution_error = None

	def __repr__(self):

		error = f' (error: {self.solution_error[1:]})' if self.solution_error != '' else ''

		return super().__repr__() + '\n' + f'Solution: {self.solution_value}' + error

	@property
	def answer(self):

		return gift.from_numerical_solution(self.solution_value, self.solution_error)


class MultipleChoice(HtmlQuestion):
	"""
	Class implementing a multiple-choice question.
	"""

	template_wrong_answers = string.Template(r"**<font color='$color'>$text</font>**")

	def __init__(
			self, name: str, statement: str, check_latex_formulas: bool, latex_auxiliary_file: Union[str, pathlib.Path],
			answers: dict, images_settings: Optional[dict] = None, feedback: Optional[str] = None,
			time: Optional[int] = None, pre_processors: list = [], post_processors: list = []):
		"""
		Initializer.

		Parameters
		----------
		answers : dict
			Right answer and a list with the wrong ones.
		"""

		super().__init__(
			name, statement, check_latex_formulas, latex_auxiliary_file, images_settings, feedback, time,
			pre_processors, post_processors)

		self.answers = answers

	@property
	def answer(self):

		processed_answers = []

		# the maximum grade allowed by partially correct answers
		max_grade = 0.

		for a in self.answers['wrong']:

			# if it is a list
			if isinstance(a, list):

				processed_answers.append(f'~%{a[1]}%{self.process_text(a[0])}')

				# if the grade is positive...
				if a[1] > 0:

					# ...it is accounted when computing the maximum
					max_grade += float(a[1])

			# if it is a scalar
			else:

				processed_answers.append(f'~{self.process_text(a)}')

		# if a "perfect" (100% credit) was provided...
		if 'perfect' in self.answers:

			# ...it is added in a special way
			processed_answers.insert(0, '=' + self.process_text(self.answers['perfect']))

		else:

			# if it's not possible to get full credit...
			if max_grade < 100.:
				print(
					f"{colors.extra_info}question{colors.reset} \"{self.name}\" {colors.extra_info} won't allow "
					f"full credit {colors.reset}{max_grade}")

		return '\t' + '\n\t'.join(processed_answers)
