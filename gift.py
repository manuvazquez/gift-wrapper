import re


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

	if (width is not None) ^ (height is not None):

		raise Exception('both width and height should be passed or none')

	else:

		# `width` is checked, but `height` could be as well used: either both are set or both are `None`
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


def process_latex(text: str) -> str:
	"""
	Adapts every occurrence of $$ to GIFT.

	Parameters
	----------
	text : str
		Input text.

	Returns
	-------
	out: str
		GIFT-ready text.

	"""

	# it looks for strings between $'s (that do not include $ itself) and wraps them in \( and \)
	return re.sub('\$([^\$]*)\$', r'\(\1\)', text)


def process_url_images(text: str, width: int, height: int) -> str:
	"""
	Adapts every to GIFT every URL in a given text.

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
	Adapts every to GIFT every new line.

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
