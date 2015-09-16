
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


class TestCheckForUpdates(unittest.TestCase):

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	def test_check_for_updates_ok(self, mock_route, mock_flask, mock_send_status):
		# Set Up
		mock_flask.request.json = {"selected_port":""}
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer.connect = mock.MagicMock(name='connect')

		# Call test subject
		self.plugin.check_for_updates()

		# Assert
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="progress", status_description="Connecting to Printer...")
		self.plugin._printer.connect.assert_called_once_with(port=mock_flask.request.json["selected_port"])
		mock_flask.make_response.assert_called_once_with('Ok.', 200)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	@mock.patch('octoprint_firmwareupdater.flask')
	@mock.patch('octoprint.plugin.BlueprintPlugin.route')
	def test_check_for_updates_printing(self, mock_route, mock_flask, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer._is_printing = True
		self.plugin._printer.connect = mock.MagicMock(name='connect')

		# Call test subject
		self.plugin.check_for_updates()

		# Assert
		mock_send_status.assert_called_once_with(status_type="flashing_status", status_value="error", status_description="Printer is busy")
		self.assertFalse(self.plugin._printer.connect.called)
		mock_flask.make_response.assert_called_once_with('Error.', 500)


class TestOnEvent(unittest.TestCase):

	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_connected(self, mock_send_status, mock_printer_callback, mock_time):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.force_check_updates = True
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["check_after_connect"] = True
		self.plugin._printer = printer_mock()
		self.plugin._printer.commands = mock.MagicMock(name='commands')
		self.plugin._logger = logger_mock()

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.CONNECTED, None)

		# Assert
		self.assertFalse(self.plugin.force_check_updates)
		self.assertIsNone(self.plugin.printer_info)
		self.assertIsNone(self.plugin.update_info)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="progress", status_description="Retrieving current firmware version from printer...")
		self.plugin._printer.commands.assert_called_once_with("M115\n")
		self.assertTrue(self.plugin._checking)

	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_connected_check(self, mock_send_status, mock_printer_callback, mock_time):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.force_check_updates = False
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["check_after_connect"] = True
		self.plugin._printer = printer_mock()
		self.plugin._printer.commands = mock.MagicMock(name='commands')
		self.plugin._logger = logger_mock()

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.CONNECTED, None)

		# Assert
		self.assertFalse(self.plugin.force_check_updates)
		self.assertIsNone(self.plugin.printer_info)
		self.assertIsNone(self.plugin.update_info)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="progress", status_description="Retrieving current firmware version from printer...")
		self.plugin._printer.commands.assert_called_once_with("M115\n")
		self.assertTrue(self.plugin._checking)

	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_connected_force(self, mock_send_status, mock_printer_callback, mock_time):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.force_check_updates = True
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["check_after_connect"] = False
		self.plugin._printer = printer_mock()
		self.plugin._printer.commands = mock.MagicMock(name='commands')
		self.plugin._logger = logger_mock()

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.CONNECTED, None)

		# Assert
		self.assertFalse(self.plugin.force_check_updates)
		self.assertIsNone(self.plugin.printer_info)
		self.assertIsNone(self.plugin.update_info)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="progress", status_description="Retrieving current firmware version from printer...")
		self.plugin._printer.commands.assert_called_once_with("M115\n")
		self.assertTrue(self.plugin._checking)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_connected_notcheck(self, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.force_check_updates = False
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["check_after_connect"] = False
		self.plugin._printer = printer_mock()
		self.plugin._printer.commands = mock.MagicMock(name='commands')
		self.plugin._logger = logger_mock()

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.CONNECTED, None)

		# Assert
		self.assertFalse(mock_send_status.called)
		self.assertFalse(self.plugin._printer.commands.called)

	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_disconnected(self, mock_send_status, mock_printer_callback):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._checking = False
		self.plugin.default_on_printer_add_message = None

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.DISCONNECTED, None)

		# Assert
		self.assertIsNone(self.plugin.printer_info)

	@mock.patch('octoprint.printer')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_disconnected_checking(self, mock_send_status, mock_printer_callback):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._checking = True
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback

		# Call test subject
		from octoprint.events import Events
		self.plugin.on_event(Events.DISCONNECTED, None)

		# Assert
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Printer was disconnected")
		self.assertFalse(self.plugin._checking)
		self.assertIsNone(self.plugin.printer_info)

	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_event_other(self, mock_send_status):
		# Set Up
		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin._printer = printer_mock()
		self.plugin._printer.commands = mock.MagicMock(name='commands')

		# Call test subject
		self.plugin.on_event(None, None)

		# Assert
		self.assertFalse(mock_send_status.called)
		self.assertFalse(self.plugin._printer.commands.called)


class TestOnPrinterAddMessage(unittest.TestCase):

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_ok_update_available(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 200
		ws_response._json = {'available':True, 'ota':{'url':'http://localhost:8080/builds/witbox2-fw/248/Marlin_witbox_2_octoprintsupport.hex', 'fw_version':'2.0.1'}}
		mock_requests_get.return_value = ws_response

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/en")
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="update_available", status_description=ws_response._json["ota"]["fw_version"])

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_ok_up_to_date(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 200
		ws_response._json = {'available':False}
		mock_requests_get.return_value = ws_response

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/en")
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="up_to_date")

	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_timeout(self, mock_send_status, mock_printer_callback, mock_time):
		# Set Up
		mock_time.return_value = 31

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._logger = logger_mock()

		# Call test subject
		self.plugin.on_printer_add_message('')

		# Assert
		self.assertIsNone(self.plugin.printer_info)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Unable to get FW version from printer")
		self.assertFalse(self.plugin._checking)

	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_time_error(self, mock_send_status, mock_printer_callback, mock_time):
		# Set Up
		mock_time.return_value = 0

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 1
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._logger = logger_mock()

		# Call test subject
		self.plugin.on_printer_add_message('')

		# Assert
		self.assertIsNone(self.plugin.printer_info)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Unable to get FW version from printer")
		self.assertFalse(self.plugin._checking)

	@mock.patch('time.time')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_no_machine_type(self, mock_send_status, mock_time):
		# Set Up
		mock_time.return_value = 0

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(mock_send_status.called)

	@mock.patch('time.time')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_no_firmware_version(self, mock_send_status, mock_time):
		# Set Up
		mock_time.return_value = 0

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(mock_send_status.called)

	@mock.patch('re.compile')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_re_exception(self, mock_send_status, mock_printer_callback, mock_time, mock_re_compile):
		# Set Up
		mock_time.return_value = 0
		mock_re_compile.side_effect = Exception()

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Unable to parse M115 response")

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_re_error(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:MarlinFIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Wrong format in M115 response")

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_no_language(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 200
		ws_response._json = {'available':True, 'ota':{'url':'http://localhost:8080/builds/witbox2-fw/248/Marlin_witbox_2_octoprintsupport.hex', 'fw_version':'2.0.1'}}
		mock_requests_get.return_value = ws_response

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()
		_default_firmware_language = "test_language"
		self.plugin._default_firmware_language = _default_firmware_language

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		self.assertEqual(self.plugin.printer_info["X-FIRMWARE_LANGUAGE"], _default_firmware_language)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/{test_language}".format(test_language=_default_firmware_language))
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="update_available", status_description=ws_response._json["ota"]["fw_version"])

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_empty_language(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 200
		ws_response._json = {'available':True, 'ota':{'url':'http://localhost:8080/builds/witbox2-fw/248/Marlin_witbox_2_octoprintsupport.hex', 'fw_version':'2.0.1'}}
		mock_requests_get.return_value = ws_response

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()
		_default_firmware_language = "test_language"
		self.plugin._default_firmware_language = _default_firmware_language

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE: X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		self.assertEqual(self.plugin.printer_info["X-FIRMWARE_LANGUAGE"], _default_firmware_language)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/{test_language}".format(test_language=_default_firmware_language))
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="update_available", status_description=ws_response._json["ota"]["fw_version"])

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_requests_exception(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 200
		ws_response._json = {'available':True, 'ota':{'url':'http://localhost:8080/builds/witbox2-fw/248/Marlin_witbox_2_octoprintsupport.hex', 'fw_version':'2.0.1'}}
		mock_requests_get.side_effect = Exception()

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/en")
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Unable to connect to update server")

	@mock.patch('requests.get')
	@mock.patch('time.time')
	@mock.patch.object(octoprint.printer.PrinterCallback, 'on_printer_add_message')
	@mock.patch.object(octoprint_firmwareupdater.FirmwareupdaterPlugin, '_send_status')
	def test_on_printer_add_message_status_code(self, mock_send_status, mock_printer_callback, mock_time, mock_requests_get):
		# Set Up
		mock_time.return_value = 0
		ws_response = requests_response_mock()
		ws_response.status_code = 0
		ws_response._json = {'available':True, 'ota':{'url':'http://localhost:8080/builds/witbox2-fw/248/Marlin_witbox_2_octoprintsupport.hex', 'fw_version':'2.0.1'}}
		mock_requests_get.return_value = ws_response

		self.plugin = octoprint_firmwareupdater.FirmwareupdaterPlugin()
		self.plugin.start_time = 0
		self.plugin.default_on_printer_add_message = None
		self.plugin.printer_callback = mock_printer_callback.PrinterCallback
		self.plugin._settings = settings_mock()
		self.plugin._settings._settings["update_service_url"] = "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		self.plugin._logger = logger_mock()

		# Call test subject
		data = 'FIRMWARE_NAME:Marlin FIRMWARE_VERSION:2.0.0 SOURCE_CODE_URL:http%3A//github.com/bq/Marlin PROTOCOL_VERSION:1.0 MACHINE_TYPE:Witbox_2 EXTRUDER_COUNT:1 X-FIRMWARE_LANGUAGE:en X-BUILD_VERSION:""'
		self.plugin.on_printer_add_message(data)

		# Assert
		self.assertFalse(self.plugin._checking)
		mock_requests_get.assert_called_once_with("http://localhost:8080/api/checkUpdate/Witbox_2/2.0.0/en")
		mock_send_status.assert_called_once_with(status_type="check_update_status", status_value="error", status_description="Unable to connect to update server: Got status code {sc}".format(sc=ws_response.status_code))




# Helper classes

class named_temporary_file_mock():
	def __init__(self):
		self.name = "filepath"
	def close(self):
		pass

class settings_mock():
	def __init__(self):
		self._settings = dict()
	def get(self, key_list):
		key = key_list[0]
		if key in self._settings.keys():
			return self._settings[key]
		else:
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
	def connect(self, *argc, **kwargs):
		pass
	def register_callback(self, *argc, **kwargs):
		pass
	def commands(self, *argc, **kwargs):
		pass

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

class requests_response_mock():
	def __init__(self):
		self.status_code = None
		self._json = None
	def json(self):
		return self._json


if __name__ == '__main__':
	unittest.main(verbosity=2)
        