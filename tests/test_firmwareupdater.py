
# -*- coding: utf-8 -*-
import unittest
import mock
import octoprint_firmwareupdater


class MyTestCase(unittest.TestCase):

	def setUp(self):
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_ok(self, mock_os):
		mock_os.path.exists.return_value = True
		mock_os.path.isFile.return_value = True
		mock_os.access.return_value = True

		self.assertTrue(self.plugin._check_avrdude())

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_not_exists(self, mock_os):
		mock_os.path.exists.return_value = False
		mock_os.path.isFile.return_value = True
		mock_os.access.return_value = True

		self.assertFalse(self.plugin._check_avrdude())

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_not_file(self, mock_os):
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = False
		mock_os.access.return_value = True

		self.assertFalse(self.plugin._check_avrdude())

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_not_executable(self, mock_os):
		mock_os.path.exists.return_value = True
		mock_os.path.isFile.return_value = True
		mock_os.access.return_value = False

		self.assertFalse(self.plugin._check_avrdude())

class settings_mock():
	def get(self, *argc, **argv):
		return ""

class logger_mock():
	def error(self, *argc, **argv):
		return






if __name__ == '__main__':
	unittest.main(verbosity=2)
        