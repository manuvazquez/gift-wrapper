import pathlib
from typing import Union

import paramiko


class Connection:

	def __init__(self, host: str, user: str, password: str, public_key: Union[str, pathlib.Path]):

		# useful in `__del__` if the assertion below fails
		self.connection = None

		assert (password is not None) ^ (public_key is not None),\
			f'either "password" or "public_key" must be passed, but not both'

		if public_key is not None:

			# just in case "~" is in the given path
			public_key = pathlib.Path(public_key).expanduser().as_posix()

		self.config = paramiko.SSHConfig()

		# ssh settings are parsed in
		with open(pathlib.Path.home() / '.ssh' / 'config') as f:

			self.config.parse(f)

		self.connection = paramiko.SSHClient()

		# so that it finds the key (no known_hosts error?)
		self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		# connection is established
		self.connection.connect(host, username=user, password=password, key_filename=public_key)

		# FTP component of the connection
		self.sftp = paramiko.SFTPClient.from_transport(self.connection.get_transport())

	def __del__(self):

		if self.connection is not None:

			self.connection.close()

	def is_active(self):

		return self.connection.get_transport().is_active()

	def copy(self, source: Union[str, pathlib.Path], remote_directory: str):

		local = pathlib.Path(source)
		remote_directory = pathlib.Path(remote_directory)

		assert local.exists(), f'file {local} does not exist'

		self.make_directory_at(remote_directory.relative_to(remote_directory.parts[0]), remote_directory.parts[0])

		remote = remote_directory / local.name

		self.sftp.put(local.as_posix(), self.sftp.normalize(remote.as_posix()))

	def make_directory_at(self, new: Union[str, pathlib.Path], at: str):

		self.sftp.chdir(at)

		# for every path component in the `new` directory...
		for subdirectory in pathlib.Path(new).parts:

			# if the subdirectory does not exist...
			if subdirectory not in self.sftp.listdir('.'):

				# ...it is made...
				self.sftp.mkdir(subdirectory)

				# ...and becomes the current working directory
			self.sftp.chdir(subdirectory)

		# the "current working directory" in unset
		self.sftp.chdir(None)


class FakeConnection:
	"""
	For debugging purposes.
	"""

	def __init__(self):

		pass

	def __del__(self):

		pass

	@staticmethod
	def is_active():

		return False

	@staticmethod
	def copy(source: Union[str, pathlib.Path], remote_directory: str):

		print(f'you *should* copy {source} to {remote_directory}')

	@staticmethod
	def make_directory_at(new: str, at: str):

		print(f'you *should* make directory {new} at {at}')