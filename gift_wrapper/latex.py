import pathlib
import shutil
import subprocess
import string
from typing import Union, List, Optional


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

	assert path_to_compiler, 'cannot find pdflatex'

	command = [path_to_compiler] + [f'-{o}' for o in options] + [source_file.name]

	run_summary = subprocess.run(command, capture_output=True, cwd=source_file.parent, timeout=timeout)

	return run_summary.returncode


latex_template = string.Template(r'''
\documentclass{standalone}

\usepackage{amsmath}

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
