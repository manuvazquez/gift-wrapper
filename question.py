import abc
import pathlib
from typing import Union

import gift


class HtmlQuestion(metaclass=abc.ABCMeta):

	def __init__(self, name: str, statement: str, images_settings: dict):

		self.name = name
		self.statement = statement.rstrip()

		assert ('width' in images_settings) and ('height' in images_settings), '"width" and/or "height" missing'

		self.images_width, self.images_height = images_settings['width'], images_settings['height']

	@property
	def gift(self):

		return gift.from_question_name(self.name) + gift.html + gift.process_url_images(
			gift.process_new_lines(self.statement), width=self.images_width, height=self.images_width)

	def __repr__(self):

		return f'Name: {self.name}\nStatement: {self.statement}'


class Numerical(HtmlQuestion):

	def __init__(self, name: str, statement: str, images_settings: dict, solution: float):

		super().__init__(name, statement, images_settings)

		self.solution = solution

	def __repr__(self):

		return super().__repr__() + f'Solution: {self.solution}'

	@property
	def gift(self):

		return super().gift + '{\n\t=%100%' + str(self.solution) + '#\n}'
