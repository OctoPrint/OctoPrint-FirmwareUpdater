
# -*- coding: utf-8 -*-
import unittest
import mock

import octoprint.server.util.flask
def _restricted_access(func):
	return func
octoprint.server.util.flask.restricted_access = _restricted_access

import octoprint.server
def _require(v):
	def __require(func):
		return func
	return __require
octoprint.server.admin_permission.require = _require

import sarge
import octoprint_firmwareupdater


class TestAvrdude(unittest.TestCase):
	def setUp(self):
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_ok(self, mock_os):
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = True
		mock_os.access.return_value = True

		self.assertTrue(self.plugin._check_avrdude())

	@mock.patch('octoprint_firmwareupdater.os')
	def test_check_avrdude_not_exists(self, mock_os):
		mock_os.path.exists.return_value = False
		mock_os.path.isfile.return_value = True
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
		mock_os.path.isfile.return_value = True
		mock_os.access.return_value = False

		self.assertFalse(self.plugin._check_avrdude())


class TestFlashWithPath(unittest.TestCase):

	@mock.patch('shutil.copyfileobj')
	@mock.patch('__builtin__.open')
	@mock.patch('tempfile.NamedTemporaryFile')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('shutil.copyfileobj')
	@mock.patch('threading.Thread.start')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os.path.exists')
	@mock.patch('octoprint_firmwareupdater.os.path.isfile')
	@mock.patch('octoprint_firmwareupdater.os.access')
	def test_flash_with_path_ok(self, mock_os_exists, mock_os_isfile, mock_os_access, mock_send_status, mock_flask, mock_route,
								mock_thread_start, mock_shutil_copyfileobj, mock_check_avrdude, mock_tempfile, mock_open, mock_copyfileobj):
		# Set Up
		mock_os_exists.return_value = True
		mock_os_isfile.return_value = True
		mock_os_access.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		mock_check_avrdude.return_value = True

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		self.assertFalse(mock_send_status.called)
		mock_flask.make_response.assert_called_once_with('Ok.', 200)

	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_path_printing(self, mock_send_status, mock_flask):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer._is_printing = True

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Printer is busy")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_path_avrdude_error(self, mock_send_status, mock_flask, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = False
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Avrdude error")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_path_request_path_error(self, mock_send_status, mock_flask, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"selected_port":""}
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Parameters are missing")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_path_request_port_error(self, mock_send_status, mock_flask, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"selected_port":""}
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Parameters are missing")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os')
	def test_flash_with_path_hex_path_error(self, mock_os, mock_send_status, mock_flask, mock_check_avrdude):
		# Set Up
		mock_os.path.exists.return_value = False
		mock_os.path.isfile.return_value = True
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Uploaded file error")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os')
	def test_flash_with_path_hex_path_error(self, mock_os, mock_send_status, mock_flask, mock_check_avrdude):
		# Set Up
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = False
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Uploaded file error")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch('tempfile.NamedTemporaryFile')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os')
	def test_flash_with_path_tempfile_error(self, mock_os, mock_send_status, mock_flask, mock_check_avrdude, mock_tempfile):
		# Set Up
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = True
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		mock_tempfile.side_effect = Exception()
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Error when copying uploaded file")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch('__builtin__.open')
	@mock.patch('tempfile.NamedTemporaryFile')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os')
	def test_flash_with_path_open_error(self, mock_os, mock_send_status, mock_flask, mock_check_avrdude, mock_tempfile, mock_open):
		# Set Up
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = True
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		mock_open.side_effect = Exception()
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Error when copying uploaded file")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch('shutil.copyfileobj')
	@mock.patch('__builtin__.open')
	@mock.patch('tempfile.NamedTemporaryFile')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.os')
	def test_flash_with_path_copyfileobj_error(self, mock_os, mock_send_status, mock_flask, mock_check_avrdude, mock_tempfile, mock_open, mock_copyfileobj):
		# Set Up
		mock_os.path.exists.return_value = True
		mock_os.path.isfile.return_value = True
		mock_check_avrdude.return_value = True
		mock_flask.request.values = {"file.path":"", "selected_port":""}
		mock_copyfileobj.side_effect = Exception()
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._settings = settings_mock()

		# Call test subject
		self.plugin.flash_firmware_with_path()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Error when copying uploaded file")
		mock_flask.make_response.assert_called_once_with('Error.', 500)


class TestFlashWithURL(unittest.TestCase):

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_flash_firmware_with_url')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_ok(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude, mock_flash_with_url):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flash_with_url.return_value = True
		mock_flask.request.json = {"hex_url":"", "selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_flash_with_url.assert_called_once_with(mock_flask.request.json["hex_url"], mock_flask.request.json["selected_port"])
		self.assertFalse(mock_send_status.called)
		mock_flask.make_response.assert_called_once_with('Ok.', 200)

	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_printing(self, mock_send_status, mock_flask, mock_route):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer._is_printing = True

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Printer is busy")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_avrdude_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = False

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Avrdude error")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_hex_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.json = {"selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Parameters are missing")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_port_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.json = {"hex_url":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Parameters are missing")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_flash_firmware_with_url')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_with_url_flash_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude, mock_flash_with_url):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flash_with_url.return_value = False
		mock_flask.request.json = {"hex_url":"", "selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_firmware_with_url()

		# Assert
		mock_flash_with_url.assert_called_once_with(mock_flask.request.json["hex_url"], mock_flask.request.json["selected_port"])
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Error when retrieving hex file from URL")
		mock_flask.make_response.assert_called_once_with('Error.', 500)


class TestFlashUpdate(unittest.TestCase):

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_flash_firmware_with_url')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_ok(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude, mock_flash_with_url):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flash_with_url.return_value = True
		mock_flask.request.json = {"selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin.update_info = {"ota": {"url":""}}

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_flash_with_url.assert_called_once_with("", mock_flask.request.json["selected_port"])
		self.assertFalse(mock_send_status.called)
		mock_flask.make_response.assert_called_once_with('Ok.', 200)

	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_printing(self, mock_send_status, mock_flask, mock_route):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer._is_printing = True

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Printer is busy")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_avrdude_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = False

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Avrdude error")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_port_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.json = {}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Parameters are missing")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_no_update_info(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flask.request.json = {"selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin.update_info = None

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="No update info found")
		mock_flask.make_response.assert_called_once_with('Error.', 500)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_flash_firmware_with_url')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_check_avrdude')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_flash_update_flash_error(self, mock_send_status, mock_flask, mock_route, mock_check_avrdude, mock_flash_with_url):
		# Set Up
		mock_check_avrdude.return_value = True
		mock_flash_with_url.return_value = False
		mock_flask.request.json = {"selected_port":""}

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin.update_info = {"ota": {"url":""}}

		# Call test subject
		self.plugin.flash_update()

		# Assert
		mock_flash_with_url.assert_called_once_with("", mock_flask.request.json["selected_port"])
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Error when retrieving hex file from URL")
		mock_flask.make_response.assert_called_once_with('Error.', 500)


class Test_FlashWithURL(unittest.TestCase):

	@mock.patch('threading.Thread.start')
	@mock.patch('urllib.urlretrieve')
	@mock.patch('tempfile.NamedTemporaryFile')
	def test_flash_with_url_ok(self, mock_tempfile, mock_urlretrieve, mock_thread_start):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()

		# Call test subject
		ret = self.plugin._flash_firmware_with_url("url", "port")

		# Assert
		self.assertTrue(mock_tempfile.called)
		self.assertTrue(mock_urlretrieve.called)
		self.assertTrue(mock_thread_start.called)
		self.assertTrue(ret)

	@mock.patch('threading.Thread.start')
	@mock.patch('tempfile.NamedTemporaryFile')
	def test_flash_with_url_tempfile_error(self, mock_tempfile, mock_thread_start):
		# Set Up
		mock_tempfile.side_effect = Exception()
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()

		# Call test subject
		ret = self.plugin._flash_firmware_with_url("url", "port")

		# Assert
		self.assertTrue(mock_tempfile.called)
		self.assertFalse(mock_thread_start.called)
		self.assertFalse(ret)

	@mock.patch('threading.Thread.start')
	@mock.patch('urllib.urlretrieve')
	@mock.patch('tempfile.NamedTemporaryFile')
	def test_flash_with_url_urlretrieve_error(self, mock_tempfile, mock_urlretrieve, mock_thread_start):
		# Set Up
		mock_urlretrieve.side_effect = Exception()
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()

		# Call test subject
		ret = self.plugin._flash_firmware_with_url("url", "port")

		# Assert
		self.assertTrue(mock_tempfile.called)
		self.assertTrue(mock_urlretrieve.called)
		self.assertFalse(mock_thread_start.called)
		self.assertFalse(ret)


class TestFlashWorker(unittest.TestCase):

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch.object(sarge.Pipeline, 'wait_events')
	@mock.patch('sarge.run')
	@mock.patch('octoprint_firmwareupdater.os.path.dirname')
	def test_flash_worker_ok(self, mock_dirname, mock_sarge_run, mock_wait_events, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()
		p = pipeline_mock()
		mock_sarge_run.return_value = p

		hex_file = named_temporary_file_mock()
		hex_file.close = mock.MagicMock(name='close')

		# Call test subject
		self.plugin._flash_worker(hex_file, "port")

		# Assert
		self.assertTrue(mock_sarge_run.called)
		mock_send_status.assert_any_call(status_type="flashing_status", status_value="successful")
		mock_send_status.assert_any_call(status_type="check_update_status", status_value="up_to_date")
		self.assertTrue(hex_file.close.called)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('sarge.run')
	@mock.patch('octoprint_firmwareupdater.os.path.dirname')
	def test_flash_worker_sarge_error(self, mock_dirname, mock_sarge_run, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()
		mock_sarge_run.side_effect = Exception()

		hex_file = named_temporary_file_mock()
		hex_file.close = mock.MagicMock(name='close')

		# Call test subject
		self.plugin._flash_worker(hex_file, "port")

		# Assert
		self.assertTrue(mock_sarge_run.called)
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Unexpected error")
		self.assertTrue(hex_file.close.called)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('sarge.run')
	@mock.patch('octoprint_firmwareupdater.os.path.dirname')
	def test_flash_worker_avrdude_timeout(self, mock_dirname, mock_sarge_run, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()
		p = pipeline_mock()
		p.returncode = None
		p.stderr.line = "timeout communicating with programmer"
		mock_sarge_run.return_value = p

		hex_file = named_temporary_file_mock()
		hex_file.close = mock.MagicMock(name='close')

		# Call test subject
		self.plugin._flash_worker(hex_file, "port")

		# Assert
		self.assertTrue(mock_sarge_run.called)
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Timeout communicating with programmer")
		self.assertTrue(hex_file.close.called)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('sarge.run')
	@mock.patch('octoprint_firmwareupdater.os.path.dirname')
	def test_flash_worker_avrdude_error(self, mock_dirname, mock_sarge_run, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()
		p = pipeline_mock()
		p.returncode = None
		p.stderr.line = "avrdude: ERROR: Error Description"
		mock_sarge_run.return_value = p

		hex_file = named_temporary_file_mock()
		hex_file.close = mock.MagicMock(name='close')

		# Call test subject
		self.plugin._flash_worker(hex_file, "port")

		# Assert
		self.assertTrue(mock_sarge_run.called)
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Avrdude error: Error Description")
		self.assertTrue(hex_file.close.called)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('sarge.run')
	@mock.patch('octoprint_firmwareupdater.os.path.dirname')
	def test_flash_worker_avrdude_exception(self, mock_dirname, mock_sarge_run, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._settings = settings_mock()
		self.plugin._logger = logger_mock()
		p = pipeline_mock()
		p.returncode = 1
		mock_sarge_run.return_value = p

		hex_file = named_temporary_file_mock()
		hex_file.close = mock.MagicMock(name='close')

		# Call test subject
		self.plugin._flash_worker(hex_file, "port")

		# Assert
		self.assertTrue(mock_sarge_run.called)
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Avrdude returned code {returncode}".format(returncode=p.returncode))
		self.assertTrue(hex_file.close.called)








# Helper classes

class named_temporary_file_mock():
	def __init__(self):
		self.name = "filepath"
	def close(self):
		pass

class settings_mock():
	def get(self, *argc, **kwargs):
		return ""

	def global_get(self, params):
		if params == ["server", "uploads", "nameSuffix"]:
			return "name"
		if params == ["server", "uploads", "pathSuffix"]:
			return "path"

class logger_mock():
	def error(self, *argc, **kwargs):
		return
	def exception(self, *argc, **kwargs):
		return
	def info(self, *argc, **kwargs):
		return

class printer_mock():
	def __init__(self):
		self._is_printing = False
	def is_printing(self, *argc, **kwargs):
		return self._is_printing

class pipeline_mock():
	def __init__(self):
		self.returncode = 0
		self.stderr = stderr_mock()
		self.commands = [command_mock()]
	def wait_events(self):
		pass

class stderr_mock():
	def __init__(self):
		self.line = ""
	def read(self, timeout):
		return self.line

class command_mock():
	def __init__(self):
		pass
	def poll(self):
		return

if __name__ == '__main__':
	unittest.main(verbosity=2)
        