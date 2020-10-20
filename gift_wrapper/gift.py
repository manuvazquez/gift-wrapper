from typing import Union, Optional

from . import latex


class NotCompliantLatexFormula(Exception):

	def __init__(self, formula: str) -> None:

		self.formula = formula

	def __str__(self) -> str:

		return self.formula


html = '[html]'


def from_question_name(name: str) -> str:
	"""
	Generates GIFT text for a question name.

	Parameters
	----------
	name : str
		Name of a question.

	Returns
	-------
	out: str
		GIFT-ready question name.

	"""

	return f'::{name}::'


def from_image_url(url: str, width: int, height: int) -> str:
	"""
	Generates GIFT text for a URL.

	Parameters
	----------
	url : str
		Input URL.
	width : int
		Desired width of the image.
	height : int
		Desired height of the image.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	# either both are set or none
	assert not ((width is not None) ^ (height is not None)), 'both "width" and "height" should be set or none of them'

	# `width` is checked, but `height` could be as well used (at this point either both are set or none)
	if width is not None:

		# notice the space at the beginning
		width_height = f' width="{width}" height="{height}"'

	else:

		width_height = ''

	res = f'<img src="{url}" alt="" role="presentation" class="atto_image_button_text-bottom"{width_height}>'

	for to_be_escaped in [':', '~', '=']:

		res = res.replace(to_be_escaped, '\\' + to_be_escaped)

	return res


def from_category(name: str, within_the_course: bool = True) -> str:
	"""
	Generates GIFT text for a category.

	Parameters
	----------
	name : str
		Category name.
	within_the_course: bool
		If True, the category will belong to the course in which the questions are imported.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	return '$CATEGORY: ' + (r'$course$/' if within_the_course else '') + name + '\n\n'


def from_feedback(text: str) -> str:
	"""
	Generates GIFT-ready text from a feedback string.

	Parameters
	----------
	text : str
		Input text.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	return '#'*4 + text


def from_latex_formula(text: str) -> str:
	"""
	Adapts a LaTeX formula to GIFT.

	Parameters
	----------
	text: str
		Naked (no $'s) LaTeX formula.

	Returns
	-------
	res: str
		GIFT-ready text.

	"""

	res = text

	for to_be_escaped in ['\\', '{', '}', '=']:

		res = res.replace(to_be_escaped, '\\' + to_be_escaped)

	res = res.replace('&', '&amp;')

	return r'\\(' + res + r'\\)'


def process_new_lines(text: str) -> str:
	"""
	Adapts every new line to GIFT.

	Parameters
	----------
	text : str
		Input text.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	# new lines are replaced everywhere *except* inside latex formulas
	return latex.replace_and_replace_only_in_formulas('\n', r'<br>', r'<br>', ' ', text)


def from_numerical_solution(solution: [float, int], error: Optional[Union[float, int, str]] = None) -> str:
	"""
	Generates GIFT-ready text from the solution and, optionally, error of a numerical question.

	Parameters
	----------
	solution : int or float
		Value of the solution.
	error : int or float or str, optional
		Value of the error.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	error = ':' + str(error) if error else ''

	return f'#\t=%100%{solution}{error}#'
