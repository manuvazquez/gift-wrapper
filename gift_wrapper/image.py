import sys
import pathlib
import shutil
import subprocess
import uuid
from typing import Union

from . import colors
from . import latex
from . import parsing


def tex_to_pdf(source_file: Union[str, pathlib.Path], timeout: int = 10) -> pathlib.Path:
	"""
	Turns a TeX file into a pdf.

	Parameters
	----------
	source_file : str or pathlib.Path
		TeX file.
	timeout: int
		Seconds that are given to compile the source.

	Returns
	-------
	out: pathlib.Path
		The path to the compiled pdf.

	"""

	source_file = pathlib.Path(source_file).with_suffix('.tex')

	if not source_file.exists():

		# first character is not visible due to tqdm
		print(f'\n{source_file} {colors.error}does not exist')

		sys.exit(1)

	try:

		exit_status = latex.compile_tex(source_file, timeout=timeout)

	except subprocess.TimeoutExpired:

		print(
			f'{colors.error}could not compile {colors.reset}{source_file}'
			f' {colors.error}in {colors.reset}{timeout}{colors.error} seconds'
		)

		sys.exit(1)

	if exit_status != 0:

		# first character is not visible due to tqdm
		print(f'\n{colors.error}errors were found while compiling {colors.reset}{source_file}')

		sys.exit(1)

	return source_file.with_suffix('.pdf')


def pdf_to_svg(input_file: Union[str, pathlib.Path]) -> pathlib.Path:
	"""
	Converts a pdf file into an svg.

	Parameters
	----------
	input_file : str or pathlib.Path
		pdf file.

	Returns
	-------
	out: pathlib.Path
		The path to the svg file.

	"""

	input_file = pathlib.Path(input_file)
	output_file = input_file.with_suffix('.svg')

	path_to_pdf2svg = shutil.which('pdf2svg')

	if path_to_pdf2svg is None:

		# first character is not visible due to tqdm
		print(f"\n{colors.error}couldn't find pdf2svg")

		sys.exit(1)

	command = [path_to_pdf2svg, input_file.name, output_file.name]

	run_summary = subprocess.run(command, capture_output=True, cwd=input_file.parent)

	assert run_summary.returncode == 0,\
		f"{colors.error}could not convert {colors.reset}{input_file}{colors.error} to svg"

	return output_file


def svg_to_html(input_file: Union[str, pathlib.Path]) -> str:
	"""

	Parameters
	----------
	input_file : str or pathlib.Path
		svg file.

	Returns
	-------

	"""

	# input file is read
	with open(input_file) as f:

		file_content = f.read()

	# since all the svg's are going to be put together, a unique "uuid" is appended to every id in the file
	for svg_id in parsing.re_svg_id.findall(file_content):

		file_content = file_content.replace(svg_id, f'{uuid.uuid1()}-{svg_id}')

	for to_be_escaped in [':', '~', '=', '#', '{', '}']:

		file_content = file_content.replace(to_be_escaped, '\\' + to_be_escaped)

	return r'<body>' + '\n' + file_content + r'</body>'
