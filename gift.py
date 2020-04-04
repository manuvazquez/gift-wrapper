import re
import functools


html = '[html]'


def from_question_name(name: str) -> str:

	return f'::{name}::'


def process_latex(text: str) -> str:

	# it looks for strings between $'s (that do not include $ itself) and wraps them in \( and \)
	return re.sub('\$([^\$]*)\$', r'\(\1\)', text)


def from_image_url(url: str, width: int, height: int) -> str:

	res = (
		f'<img src="{url}" alt="" role="presentation" class="atto_image_button_text-bottom" '
		f'width="{width}" height="{height}">'
	)

	for to_escape in [':', '~', '=']:

		res = res.replace(to_escape, '\\' + to_escape)

	return res


def process_url_images_aux(match_object, width: int, height: int):

	return from_image_url(match_object.group(0), width, height)


def process_url_images(text: str, width: int, height: int) -> str:

	return re.sub(r'http(\S*)', functools.partial(process_url_images_aux, width=width, height=height), text)
