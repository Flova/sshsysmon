from driver import *
import os
from paramiko import SSHClient, RSAKey, AutoAddPolicy
from StringIO import StringIO

class Ssh(Driver):
	DEFAULT_KEY_PATH = "~/.ssh/id_rsa"

	def __init__(self, host, username='root', password = None, key = None, port = 22, path = "/proc"):
		Driver.__init__(self)
		self._host = host
		self._username = username
		self._password = password
		self._port = port
		self._path = path

		self._key = RSAKey.from_private_key_file(os.path.expanduser(key or Ssh.DEFAULT_KEY_PATH))

	def readFile(self, path):
		client = self._connect()
		try:
			sftp = client.open_sftp()

			o = StringIO()
			for line in sftp.open(os.path.join(self._path, path)):
				o.write(line)

			return o.getvalue()

		finally:
			client.close()

	def sh(self, cmd):
		client = self._connect()
		stdin, stdout, stderr = client.exec_command(cmd)
		return stdout.read()

	def _connect(self):
		client = SSHClient()
		client.set_missing_host_key_policy(AutoAddPolicy())
		client.connect(hostname = self._host, username=self._username, password=self._password, pkey=self._key, port=self._port)
		return client