import re
import pathlib
from typing import Union

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


def process_latex(text: str, latex_auxiliary_file: Union[str, pathlib.Path], check_compliance: bool = True) -> str:
	"""
	Adapts every occurrence of $$ to GIFT.

	Parameters
	----------
	text : str
		Input text.
	latex_auxiliary_file: str or pathlib.Path
		(Auxiliary) TeX file that is created to check the formula.
	check_compliance: bool
		Whether or not to check if the formula can be compiled.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	# TODO: when minimum Python version is forwarded to 3.8, `re.Match` should be the type hinting for "m"
	def replacement(m) -> str:

		latex_source = m.group(1)

		if check_compliance:

			if not latex.formula_can_be_compiled(latex_source, auxiliary_file=latex_auxiliary_file):

				raise NotCompliantLatexFormula(latex_source)

		for to_be_escaped in ['\\', '{', '}', '=']:

			latex_source = latex_source.replace(to_be_escaped, '\\' + to_be_escaped)

		latex_source = latex_source.replace('&', '&amp;')

		return r'\\(' + latex_source + r'\\)'

	# it looks for strings between $'s (that do not include $ itself) and wraps them in \( and \)
	return re.sub(r'\$([^\$]*)\$', replacement, text)


def process_url_images(text: str, width: int, height: int) -> str:
	"""
	Adapts to GIFT every URL in a given text.

	Parameters
	----------
	text : str
		Input text.
	width : int
		Desired width of the image.
	height : int
		Desired height of the image.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	return re.sub(
		'http(\S+)(?!\S)',
		lambda m: '<p>' + from_image_url(m.group(0), width=width, height=height) + '<br></p>',
		text)


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

	return text.replace('\n', '<br>')
