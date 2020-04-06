import pathlib
import shutil
import subprocess
from typing import Union, Optional


def compile_tex(source_file: Union[str, pathlib.Path]) -> pathlib.Path:
	"""
	Compiles a TeX file.

	Parameters
	----------
	source_file : str or pathlib.Path
		Tex file.

	Returns
	-------
	out: str
		The path to the compiled pdf.

	"""

	source_file = pathlib.Path(source_file)

	path_to_compiler = shutil.which('pdflatex')

	assert path_to_compiler, 'cannot find pdflatex'

	command = [path_to_compiler, source_file.name]

	run_summary = subprocess.run(command, capture_output=True, cwd=source_file.parent)

	assert run_summary.returncode == 0, f"couldn't compile {source_file}"

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
	out: str
		The path to the svg file.

	"""

	input_file = pathlib.Path(input_file)
	output_file = input_file.with_suffix('.svg')

	path_to_pdf2svg = shutil.which('pdf2svg')

	assert path_to_pdf2svg, "couldn't find pdf2svg"

	command = [path_to_pdf2svg, input_file.name, output_file.name]

	run_summary = subprocess.run(command, capture_output=True, cwd=input_file.parent)

	assert run_summary.returncode == 0, f"couldn't convert {input_file} to svg"

	return output_file
