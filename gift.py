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

	res = (
		f'<img src="{url}" alt="" role="presentation" class="atto_image_button_text-bottom" '
		f'width="{width}" height="{height}">'
	)

	for to_be_escaped in [':', '~', '=']:

		res = res.replace(to_be_escaped, '\\' + to_be_escaped)

	return res


def process_latex(text: str) -> str:
	"""
	Adapts every occurrence of $$ to GIT.

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
	Adapts every to GIT every URL in a given text.

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
		r'http(\S*)',
		lambda m: '<p>' + from_image_url(m.group(0), width=width, height=height) + '<br></p>',
		text)


def process_new_lines(text: str) -> str:
	"""
	Adapts every to GIT every new line.

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
