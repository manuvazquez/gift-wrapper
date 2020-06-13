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
