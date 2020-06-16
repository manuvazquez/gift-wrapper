import re

# regular expression to extract a percentage
re_percentage = re.compile(r'(\d*\.\d+|\d+)\s*%')

regex_filename_valid_character = r'[\\/\w_\-]'
regex_url_valid_character = regex_filename_valid_character[:-1] + r'\:\.~]'

# ---------- tex files

tex_file_name = r'(\S+)\.tex'

# ---------- svg files

# svg_file = r'(\S+\.svg)'
svg_file = f'({regex_filename_valid_character}+\.svg)'

url_less_svg_file = (
		f'(?<!{regex_filename_valid_character})(?!http)'
		f'({regex_filename_valid_character}+\.svg)(?!{regex_filename_valid_character})')

# ---------- URLs

# url = r'http(\S+)(?!\S)'
url = f'http({regex_url_valid_character}+)(?!{regex_url_valid_character})'

# ---------- latex

latex_formula = r'\$([^\$]*)\$'

# in every list, the first pair of elements are the search pattern and replacement to be applied *globally* whereas
# the second one will only be applied inside LaTeX formulas
# NOTE: "\" is duplicated because it is assumed it has been escaped previously by `gift.process_latex`
latex_in_text_substitutions = [
	# \textbf
	[r'\\textbf{([^}]+)}', r'<b>\1</b>', r'<b>([^<]*)</b>', r'\\textbf{\1}'],
	# \textit
	[r'\\textit{([^}]+)}', r'<i>\1</i>', r'<i>([^<]*)</i>', r'\\textit{\1}']
]