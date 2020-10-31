import re
import pathlib
import functools
from typing import Union, Callable, Optional

from . import image
from . import parsing
from . import remote
from . import gift
from . import latex


def process_paths(
		text: str, pattern: str, process_match: Callable[[str], None], replacement: Union[str, Callable[..., str]]):
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

	# breakpoint()

	# every one of them...
	for file in files:
		# ...is processed
		process_match(file)

	# replacement of matches
	return re.sub(pattern, replacement, text)


class Transformer:

	def __init__(self) -> None:

		# subclasses are expected to set this up
		self.function: Optional[Callable] = None

	def __call__(self, text: str):

		assert self.function is not None, 'method "function" was not defined'

		return self.function(text)


class TexToSvg(Transformer):
	"""
	Processor to convert TeX files into svg files.
	"""

	def __init__(self, history: dict) -> None:

		super().__init__()

		self.history = history

		def process_match(f):

			# if this file has not been already compiled-converted...
			if f not in self.history['already compiled']:

				# ...it is...
				image.pdf_to_svg(image.tex_to_pdf(f))

				# ...and a note is made of it
				self.history['already compiled'].add(f)

		# (the "\1" in `replacement` refers to matches in `pattern`)
		self.function = functools.partial(
			process_paths, pattern=parsing.tex_file_name, process_match=process_match, replacement=r'\1.svg')


class SvgToHttp(Transformer):
	"""
	Processor to transfer svg files to a remote location.
	"""

	def __init__(
			self, history: dict, connection: remote.Connection, public_filesystem_root: str,
			pictures_base_directory: str, public_url: str):

		super().__init__()

		self.history = history

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

				# ...and a note is made of the fact
				self.history['already transferred'].add(f)

		self.function = functools.partial(
			process_paths, pattern=parsing.url_less_svg_file, process_match=process_match,
			replacement=replacement_function)


class SvgToInline(Transformer):
	"""
	Processor to directly include svg files into a question.
	"""

	def __init__(self):

		super().__init__()

		# TODO: when minimum Python version is forwarded to 3.8, `re.Match` should be the type hinting for `m`
		def replacement_function(m) -> str:

			file = pathlib.Path(m.group(1))

			return image.svg_to_html(file)

		self.function = functools.partial(
			process_paths, pattern=parsing.svg_file, process_match=lambda x: None, replacement=replacement_function)


class URLs(Transformer):
	"""
	Processor to arrange URLs into a GIFT-appropriate format.
	"""

	url = f'http({parsing.regex_url_valid_character}+)(?!{parsing.regex_url_valid_character})'

	def __init__(self, images_settings: Optional[dict] = None):

		super().__init__()

		if images_settings is None:

			self.images_width, self.images_height = None, None

		else:

			assert ('width' in images_settings) and ('height' in images_settings), \
				'"width" and/or "height" missing in "image_settings"'

			self.images_width, self.images_height = images_settings['width'], images_settings['height']

		self.function = lambda text: re.sub(self.url, self.replacement, text)

	# TODO: when minimum Python version is forwarded to 3.8, `re.Match` should be the type hinting for "m"
	def replacement(self, m) -> str:

		return '<p>' + gift.from_image_url(m.group(0), width=self.images_width, height=self.images_height) + '<br></p>'


class LatexCommandsWithinText(Transformer):

	# in every list, the first pair of elements are the search pattern and replacement to be applied *globally* whereas
	# the second one will only be applied inside LaTeX formulas
	# NOTE: "\" is duplicated because it is assumed it has been escaped previously by `gift.process_latex`
	patterns = [
		# \textbf
		[r'\\textbf{([^}]+)}', r'<b>\1</b>', r'<b>([^<]*)</b>', r'\\textbf{\1}'],
		# \textit
		[r'\\textit{([^}]+)}', r'<i>\1</i>', r'<i>([^<]*)</i>', r'\\textit{\1}']
	]

	def __init__(self) -> None:

		super().__init__()

		def f(text: str) -> str:

			res = text

			for pat in self.patterns:

				res = latex.replace_and_replace_only_in_formulas(*pat, res)

			return res

		self.function = f


class LatexFormulas(Transformer):

	latex_formula = r'\$([^\$]*)\$'

	def __init__(self, latex_auxiliary_file: Union[str, pathlib.Path], check_compliance: bool) -> None:

		super().__init__()

		self.latex_auxiliary_file = latex_auxiliary_file
		self.check_compliance = check_compliance

		self.function = lambda text: re.sub(self.latex_formula, self.replacement, text)

	# TODO: when minimum Python version is forwarded to 3.8, `re.Match` should be the type hinting for "m"
	def replacement(self, m) -> str:

		latex_source = m.group(1)

		if self.check_compliance:

			if not latex.formula_can_be_compiled(latex_source, auxiliary_file=self.latex_auxiliary_file):
				raise gift.NotCompliantLatexFormula(latex_source)

		return gift.from_latex_formula(latex_source)
