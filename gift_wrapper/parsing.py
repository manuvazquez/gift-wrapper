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

re_svg_id = re.compile(r'id="([\w-]+)"')

# ---------- latex

latex_formula_with_no_capturing = r'\$[^\$]*\$'
