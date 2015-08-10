# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin.
#
# Take a look at the documentation on what other plugin mixins are available.

import flask
import os
import urllib
import urllib2
import urlparse
import serial
import json

import octoprint.plugin
import octoprint.settings
import octoprint.printer

from octoprint.events import eventManager, Events
from octoprint.settings import settings

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin,
							octoprint.plugin.StartupPlugin,
							octoprint.plugin.ShutdownPlugin):

	#~~ Asset API

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"])

	#~~ StartUp API

	def on_after_startup(self):
		self.update_pending = False

	#~~ Shutdown API

	def on_shutdown(self):
		if self._printer.is_operational():
			self._printer.commands("M117\n")

	#~~ BluePrint API

	@octoprint.plugin.BlueprintPlugin.route("/flashFirmwareWithPath", methods=["POST"])
	def flash_firmware_with_path(self):
		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		temp_path = flask.request.values[input_upload_path]
		hex_filename = flask.request.values[input_upload_name]
		avrdude_path = flask.request.values["avrdude_path"]
		selected_port = flask.request.values["selected_port"]

		hex_path = os.path.join(self.get_plugin_data_folder(), hex_filename)

		if not os.path.exists(avrdude_path):
			self._logger.exception("Path to avrdude does not exist: {path}".format(path=avrdude_path))
			return flask.make_response("Error.", 500)

		import shutil
		try:
			shutil.copyfile(os.path.abspath(temp_path), hex_path)
		except Exception as e:
			self._logger.exception("Error when copying uploaded temp hex file: {error}".format(error=e))

		# Create thread to flash firmware
		import threading
		flash_thread = threading.Thread(target=self._flash_worker, args=(avrdude_path, hex_path, selected_port))
		flash_thread.daemon = False
		flash_thread.start()

		return flask.make_response("Ok.", 200)

	@octoprint.plugin.BlueprintPlugin.route("/flashFirmwareWithURL", methods=["POST"])
	def flash_firmware_with_url(self):

		hex_url = flask.request.json['hex_url']
		self.avrdude_path = flask.request.json['avrdude_path']
		self.selected_port = flask.request.json['selected_port']

		ret = _flash_firmware_with_url(hex_url)

		if ret:
			return flask.make_response("Ok.", 200)
		else:
			return flask.make_response("Error.", 500)

	def _flash_firmware_with_url(self, hex_url):

		filename = os.path.basename(hex_url)
		dest_path = os.path.join(self.get_plugin_data_folder(), filename)

		try:
			hex_path, _ = urllib.urlretrieve(hex_url, dest_path)
		except Exception as e:
			self._logger.exception("Error when retrieving hex file from URL: {error}".format(error=e))
			return False

		if not self._check_avrdude():
			return False

		# Create thread to flash firmware
		import threading
		flash_thread = threading.Thread(target=self._flash_worker, args=(self.avrdude_path, hex_path, self.selected_port))
		flash_thread.daemon = False
		flash_thread.start()

		return True

	def _flash_worker(self, avrdude_path, hex_path, selected_port):
		avrdude_args = ["-p m2560", "-c wiring", "-P", selected_port, "-U flash:w:" + hex_path + ":i -D"]
		avrdude_command = avrdude_path + ' ' + ' '.join(avrdude_args)
		working_dir = os.path.dirname(avrdude_path)

		import sarge
		self._logger.info(u"Running %r in %s" % (avrdude_command, working_dir))
		p = sarge.run(avrdude_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
		p.wait_events()

		while p.returncode is None:
			line = p.stderr.readline(timeout=0.5)
			if not line:
				p.commands[0].poll()
				continue
			if "avrdude: writing" in line:
				self._logger.info(u"Writing memory...")
				self.send_plugin_message("Writing memory...", "warning")
			elif "avrdude: verifying ..." in line:
				self._logger.info(u"Verifying memory...")
				self.send_plugin_message("Verifying memory...", "warning")
			elif "timeout communicating with programmer" in line:
				self._logger.info(u"Flashing failed. Timeout communicating with programmer.")
				self.send_plugin_message("Flashing failed", "error", text="Timeout communicating with programmer")
				return

		if p.returncode == 0:
			self._logger.info(u"Flashing successful.")
			self.send_plugin_message("Flashing successful", "success")
		else:
			self._logger.info(u"Flashing failed with return code {returncode}.".format(returncode=p.returncode))
			self.send_plugin_message("Flashing failed", "error", text="Return code {returncode}".format(returncode=p.returncode))

	def _check_avrdude(self):
		if not os.path.exists(self.avrdude_path):
			self._logger.exception("Path to avrdude does not exist: {path}".format(path=self.avrdude_path))
			return False
		elif not os.path.isfile(self.avrdude_path):
			self._logger.exception("Path to avrdude is not a file: {path}".format(path=self.avrdude_path))
			return False
		elif not os.access(self.avrdude_path, os.X_OK):
			self._logger.exception("Path to avrdude is not executable: {path}".format(path=self.avrdude_path))
			return False
		else:
			return True

	@octoprint.plugin.BlueprintPlugin.route("/checkForUpdates", methods=["POST"])
	def check_for_updates(self):

		self.avrdude_path = flask.request.json['avrdude_path']
		self.selected_port = flask.request.json['selected_port']

		self.send_plugin_message("Connecting to printer...", "warning")
		self._logger.info("Connecting to printer at %s to get printer info" % self.selected_port)

		self._printer.connect(port=self.selected_port) # If a connection is already established, that connection will be closed prior to connecting anew with the provided parameters.

		self.update_pending = True

		return flask.make_response("Ok.", 200)

	#~~ SettingsPlugin API

	def get_settings_defaults(self):
		return {
			"path_avrdude": None,
			"path_avrdudeconfig": None
		}

	def on_settings_save(self, data):
		for key in self.get_settings_defaults():
			if key in data:
				self._settings.set([key], data[key])

	#~~ EventHandler API

	def on_event(self, event, payload):
		if event == "Connected":

			if not hasattr(self, "printer_info"):
				self._logger.warn("Connected but no printer_info found.")
				return

			# Check if new update available

			self.ws_baseurl = "http://localhost:8080/api/checkUpdate/"
			self.language = "en" # TODO: We should get this from printer_info

			ws_args = "%s/%s/%s" % (self.printer_info["printer_model"], self.printer_info["fw_version"], self.language)

			try:
				ws_response = urllib2.urlopen(self.ws_baseurl + urllib.quote(ws_args)).read()
			except urllib2.URLError:
				self.send_plugin_message("Unable to connect to updates web server", "error")
				return

			ws_response_dict = json.loads(ws_response)
			if ws_response_dict["available"]:

				self.send_plugin_message("Firmware update available", "warning")

				if self.update_pending:
					self._flash_firmware_with_url(ws_response_dict["ota"]["url"])
					self.update_pending = False

				return

			else:
				self.send_plugin_message("Firmware is up to date", "success")
				return

		elif event == "Disconnected":
			if hasattr(self, "printer_info"):
				del self.printer_info

	#~~ Hooks

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/flashFirmwareWithPath", 1000 * 1024)]

	def serial_comm_hook(self, comm_instance, port, baudrate, read_timeout, *args, **kwargs):

		serial_obj = self._default(comm_instance, port, baudrate, read_timeout)

		if serial_obj == None:
			self.send_plugin_message("Unable to connect to printer", "error")
			self._logger.info("Unable to connect to printer")
			return

		# Flush the init messages after connection
		while serial_obj.readline().strip() != "":
			pass

		self.send_plugin_message("Retrieving current FW version from printer", "warning")
		self._logger.info("Retrieving current FW version from printer")
		serial_obj.write("M115\n")

		line = serial_obj.readline()
		while line.strip() != "":	# TODO: Improve this
			if "MACHINE_TYPE" in line:
				break
			line = serial_obj.readline()

		fwn_s = "FIRMWARE_NAME:"
		fwv_s = "FIRMWARE_VERSION:"
		scu_s = "SOURCE_CODE_URL:"
		pv_s = "PROTOCOL_VERSION:"
		mt_s = "MACHINE_TYPE:"
		ec_s = "EXTRUDER_COUNT:"

		self.printer_info = dict()
		self.printer_info["fw_name"] = line[line.index(fwn_s)+len(fwn_s):line.index(fwv_s)].strip()
		self.printer_info["fw_version"] = line[line.index(fwv_s)+len(fwv_s):line.index(scu_s)].strip()
		self.printer_info["source_code_url"] = line[line.index(scu_s)+len(scu_s):line.index(pv_s)].strip()
		self.printer_info["protocol_version"] = line[line.index(pv_s)+len(pv_s):line.index(mt_s)].strip()
		self.printer_info["printer_model"] = line[line.index(mt_s)+len(mt_s):line.index(ec_s)].strip()
		self.printer_info["extruder_count"] = line[line.index(ec_s)+len(ec_s):].strip()

		self._logger.info("Current printer: %s (FW version: %s)" % (self.printer_info["printer_model"], self.printer_info["fw_version"]))

		# TODO: Decide if this should be done with all printers or just with BQ printers
		serial_obj.write("M117 " + "Connected via OctoPrint" + "\n") # TODO: Use _() to translate string

		return serial_obj

	def _default(self, comm_instance, port, baudrate, read_timeout):
		if port is None or port == 'AUTO':
			# no known port, try auto detection
			comm_instance._changeState(comm_instance.STATE_DETECT_SERIAL)
			serial_obj = comm_instance._detectPort(True)
			if serial_obj is None:
				comm_instance._errorValue = 'Failed to autodetect serial port, please set it manually.'
				comm_instance._changeState(comm_instance.STATE_ERROR)
				eventManager().fire(Events.ERROR, {"error": comm_instance.getErrorString()})
				self._logger.exception("Error when detecting port: %s" % comm_instance.getErrorString())
				return None

			port = serial_obj.port

		# connect to regular serial port
		if baudrate == 0:
			baudrates = self._baudrateList()
			serial_obj = serial.Serial(str(port), 115200 if 115200 in baudrates else baudrates[0], timeout=read_timeout, writeTimeout=10000, parity=serial.PARITY_ODD)
		else:
			serial_obj = serial.Serial(str(port), baudrate, timeout=read_timeout, writeTimeout=10000, parity=serial.PARITY_ODD)
		serial_obj.close()
		serial_obj.parity = serial.PARITY_NONE
		serial_obj.open()

		return serial_obj

	def _baudrateList(self):
		ret = [250000, 230400, 115200, 57600, 38400, 19200, 9600]
		prev = settings().getInt(["serial", "baudrate"])
		if prev in ret:
			ret.remove(prev)
			ret.insert(0, prev)
		return ret

	#~~ Extra functions

	def send_plugin_message(self, title, message_type, text=""):
		self._plugin_manager.send_plugin_message(self._identifier, dict(title=title, type=message_type, text=text))


__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	global __plugin_hooks__

	__plugin_implementation__ = FirmwareupdaterPlugin()

	__plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
        "octoprint.comm.transport.serial.factory": __plugin_implementation__.serial_comm_hook
    }