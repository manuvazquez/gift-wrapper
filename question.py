import abc
import pathlib
from typing import Union

import gift


class HtmlQuestion(metaclass=abc.ABCMeta):

	def __init__(self, name: str, statement: str, images_settings: dict):

		self.name = name
		self.statement = statement
		self.images_settings = images_settings

	@property
	def gift(self):

		return gift.from_question_name(self.name) + gift.html

	def __repr__(self):

		return f'Name: {self.name}\nStatement: {self.statement}'


class Numerical(HtmlQuestion):

	pass
