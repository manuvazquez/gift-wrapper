import pathlib
import shutil
import subprocess
import string
import re
import sys
from typing import Union, List, Optional

from . import parsing


def compile_tex(
		source_file: Union[str, pathlib.Path], timeout: Optional[int], options: List[str] = ['halt-on-error']) -> int:
	"""
	Compiles a TeX file.

	Parameters
	----------
	source_file : str or pathlib.Path
		TeX file.
	timeout: int
		Seconds that are given to compile the source.
	options: list of str
		Options to be passed to `pdflatex`.

	Returns
	-------
	out: int
		The exit status of the call to `pdflatex`.

	"""

	source_file = pathlib.Path(source_file)

	path_to_compiler = shutil.which('pdflatex')

	if path_to_compiler is None:

		print('cannot find pdflatex')

		sys.exit(1)

	command = [path_to_compiler] + [f'-{o}' for o in options] + [source_file.name]

	run_summary = subprocess.run(command, capture_output=True, cwd=source_file.parent, timeout=timeout)

	return run_summary.returncode


latex_template = string.Template(r'''
\documentclass{standalone}

\usepackage{amsmath, amsfonts}

\begin{document}

$$
$formula
$$

\end{document}
''')


def formula_can_be_compiled(formula: str, auxiliary_file: Union[str, pathlib.Path]) -> bool:
	"""
	Checks whether a latex formula can be compiled with the above template, `latex_template`.

	Parameters
	----------
	formula : str
		Latex formula.
	auxiliary_file : str or pathlib.Path
		(Auxiliary) TeX file that is created to check the formula.

	Returns
	-------
	out: bool
		`True` if the compilation finished with no errors.

	"""

	tex_source_code = latex_template.substitute(formula=formula)

	with open(auxiliary_file, 'w') as f:

		f.write(tex_source_code)

	exit_status = compile_tex(auxiliary_file, timeout=10, options=['halt-on-error', 'draftmode'])

	return exit_status == 0


def replace_and_replace_only_in_formulas(
		pattern: str, replacement: str, formula_pattern: str, formula_replacement: str, text: str) -> str:
	"""
	Replaces a matched expression but only if the match occurs *outside* a LaTeX formula.

	Notice that arguments `pattern` and `replacement`, on one hand, and `formula_pattern` and `formula_replacement`,
	on the other, are to be passed to Python's `re.sub`.

	Parameters
	----------
	pattern : str
		Regular expression to be matched globally.
	replacement : str
		Replacement string for `pattern`
	formula_pattern : str
		Regular expression to be matched in formulas.
	formula_replacement : str
		Replacement string for `formula_pattern`
	text : str
		String to be processed

	Returns
	-------
	out: str
		String with replacements.

	"""

	def process_formula(m) -> str:

		return re.sub(formula_pattern, formula_replacement, m.group(0))

	res = re.sub(pattern, replacement, text)
	res = re.sub(parsing.latex_formula_with_no_capturing, process_formula, res)

	return res
