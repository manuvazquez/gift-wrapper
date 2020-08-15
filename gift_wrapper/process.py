import re
import pathlib
import functools
from typing import Union, Callable, Optional

from . import image
from . import parsing
from . import remote


def process_paths(
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

	# breakpoint()

	# every one of them...
	for file in files:
		# ...is processed
		process_match(file)

	# replacement of matches
	return re.sub(pattern, replacement, text)


class Processor:

	def __init__(self) -> None:

		# subclasses are expected to set this up
		self.function: Optional[Callable] = None

	def __call__(self, text: str):

		assert self.function is not None, 'method "f" was not defined'

		return self.function(text)


class TexToSvg(Processor):
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


class SvgToHttp(Processor):
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


class SvgToInline(Processor):
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
