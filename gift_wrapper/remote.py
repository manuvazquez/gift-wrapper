import sys
import pathlib
from typing import Union

import paramiko

from . import colors


class Connection:

	connection_not_available_help = (
		r'(you can try running the program in local mode, by passing "-l", or embedding the images, with "-e")')

	def __init__(self, host: str, user: str, password: str, public_key: Union[str, pathlib.Path]):

		self.host = host
		self.user = user
		self.password = password
		self.public_key = public_key

		# to be set in `connect`
		self.sftp = None

		# useful in `__del__` in the case the connection never gets established
		self.connection = None

		# self.connect()

	def connect(self):

		if (self.password is not None) and (self.public_key is not None):

			print(f'\n{colors.error}either "password" or "public_key" must be passed, but not both')

			sys.exit(1)

		if self.public_key is not None:

			# just in case "~" is in the given path
			public_key = pathlib.Path(self.public_key).expanduser()

			if not public_key.exists():

				print(f'\n{colors.error}public key file, {colors.reset}{public_key}{colors.error}, does not exist')

				sys.exit(1)

			# below, an actual string is needed
			public_key = public_key.as_posix()

		else:

			# local variable `public_key` (rather than attribute `self.public_key`) is used below, so it must be
			# initialized anyway (even though it is to `None`)
			public_key = None

		self.connection = paramiko.SSHClient()

		# so that it finds the key (no known_hosts error?)
		self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		try:

			# print(f'{self.user=}, {self.password=}, {self.public_key=}')

			# connection is established
			self.connection.connect(self.host, username=self.user, password=self.password, key_filename=public_key)

		except paramiko.ssh_exception.AuthenticationException:

			# first character is not visible due to tqdm
			print(
				f'\n{colors.error}provided username {colors.reset}({self.user}){colors.error}'
				f' and/or password are not valid {self.connection_not_available_help}')

			sys.exit(1)

		except paramiko.ssh_exception.SSHException:

			# first character is not visible due to tqdm
			print(
				f'\n{colors.error}the provided public key {colors.reset}({self.public_key}){colors.error}'
				f' is not valid or has not been decrypted {self.connection_not_available_help}')

			sys.exit(1)

		# FTP component of the connection
		self.sftp = paramiko.SFTPClient.from_transport(self.connection.get_transport())

	def __del__(self):

		if self.connection is not None:

			self.connection.close()

	def is_active(self):

		if self.connection is None:

			return False

		else:

			return self.connection.get_transport().is_active()

	def copy(self, source: Union[str, pathlib.Path], remote_directory: str):

		if self.connection is None:

			self.connect()

		local = pathlib.Path(source)
		remote_directory = pathlib.Path(remote_directory)

		if not local.exists():

			# first character is not visible due to tqdm
			print(f'\n{colors.reset}file {colors.reset}{local}{colors.error} does not exist')

			sys.exit(1)

		self.make_directory_at(remote_directory.relative_to(remote_directory.parts[0]), remote_directory.parts[0])

		remote = remote_directory / local.name

		self.sftp.put(local.as_posix(), self.sftp.normalize(remote.as_posix()))

	def make_directory_at(self, new: Union[str, pathlib.Path], at: str):

		if self.connection is None:

			self.connect()

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
	For offline runs.
	"""

	def __init__(self, host: str) -> None:

		self.host = host
		self.already_copied = set()
		self.files_to_copy = []

	@staticmethod
	def is_active():

		return False

	def copy(self, source: Union[str, pathlib.Path], remote_directory: str):

		source = pathlib.Path(source)

		if source.as_posix() not in self.already_copied:

			self.already_copied.add(source.as_posix())
			self.files_to_copy.append((source, remote_directory))

	@staticmethod
	def make_directory_at(new: str, at: str):

		pass
