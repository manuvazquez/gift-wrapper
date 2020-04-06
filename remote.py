import pathlib
from typing import Union

import paramiko


class Connection:

	def __init__(self, host: str, user: str, public_key: Union[str, pathlib.Path]):

		# just in case "~" is in the given path
		public_key = pathlib.Path(public_key).expanduser()

		self.config = paramiko.SSHConfig()

		# ssh settings are parsed in
		with open(pathlib.Path.home() / '.ssh' / 'config') as f:

			self.config.parse(f)

		self.connection = paramiko.SSHClient()

		# so that it finds the key (no known_hosts error?)
		self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

		# connection is established
		self.connection.connect(host, username=user, key_filename=public_key.as_posix())

		# FTP component of the connection
		self.sftp = paramiko.SFTPClient.from_transport(self.connection.get_transport())

	def __del__(self):

		self.connection.close()

	def is_active(self):

		return self.connection.get_transport().is_active()

	def copy(self, source: Union[str, pathlib.Path], remote_directory: str):

		local = pathlib.Path(source)

		assert local.exists(), f'file {local} does not exist'

		remote = pathlib.Path(remote_directory) / local.name

		self.sftp.put(local.as_posix(), self.sftp.normalize(remote.as_posix()))
