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
import json
import time

import octoprint.plugin

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin,
							octoprint.plugin.StartupPlugin,
							octoprint.plugin.ShutdownPlugin):

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

		ret = self._flash_firmware_with_url(hex_url)

		if ret:
			return flask.make_response("Ok.", 200)
		else:
			return flask.make_response("Error.", 500)

	@octoprint.plugin.BlueprintPlugin.route("/flashUpdate", methods=["POST"])
	def flash_update(self):
		self.avrdude_path = flask.request.json['avrdude_path']
		self.selected_port = flask.request.json['selected_port']

		if hasattr(self, "update_info"):
			self._flash_firmware_with_url(self.update_info["ota"]["url"])
			return flask.make_response("Ok.", 200)
		else:
			self._logger.info(u"No update info found")
			self.send_plugin_message("No update info found", "error")
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

	@octoprint.plugin.BlueprintPlugin.route("/checkForUpdates", methods=["GET"])
	def check_for_updates(self):
		self.send_plugin_message("Connecting to printer...", "warning")

		self._printer.connect() # If a connection is already established, that connection will be closed prior to connecting anew with the provided parameters.

		return flask.make_response("Ok.", 200)

	#~~ EventHandler API

	def on_event(self, event, payload):
		if event == "Connected":

			if hasattr(self, "printer_info"):
				del self.printer_info
			if hasattr(self, "update_info"):
				del self.printer_info

			self.callback = octoprint.printer.PrinterCallback()
			self.default_on_printer_add_message = self.callback.on_printer_add_message
			self.callback.on_printer_add_message = self.on_printer_add_message
			self._printer.register_callback(self.callback)

			self.send_plugin_message("Retrieving current FW version from printer", "warning")
			self._logger.info("Retrieving current FW version from printer")
			self._printer.commands("M115\n")

			self.start_time = time.time()

			return

		elif event == "Disconnected":
			if hasattr(self, "printer_info"):
				del self.printer_info

	def on_printer_add_message(self, data):

		# TODO: Contemplate the case where time is very very old
		if time.time() - self.start_time > 60:

			if hasattr(self, "printer_info"):
				del self.printer_info
			# Unregister callback
			self.callback.on_printer_add_message = self.default_on_printer_add_message

			self.send_plugin_message("Unable to get FW version from printer", "error")
			self._logger.info("Unable to get FW version from printer")
			return

		elif not ("MACHINE_TYPE" in data and "FIRMWARE_VERSION" in data):
			return

		# Unregister callback
		self.callback.on_printer_add_message = self.default_on_printer_add_message

		self.printer_info = self._process_M115_response(data)
		self._logger.info("Current printer: %s (FW version: %s)" % (self.printer_info["printer_model"], self.printer_info["fw_version"]))

		self.ws_baseurl = "http://localhost:8080/api/checkUpdate/"
		self.printer_info["language"] = "en" # TODO: We should get this from printer's M117 response (probably within FIRMWARE_NAME)
		ws_args = "%s/%s/%s" % (self.printer_info["printer_model"], self.printer_info["fw_version"], self.printer_info["language"])

		try:
			ws_response = urllib2.urlopen(self.ws_baseurl + urllib.quote(ws_args)).read()
		except urllib2.URLError:
			self.send_plugin_message("Unable to connect to update server", "error")
			self._logger.info("Unable to connect to update server")
			return

		self.update_info = json.loads(ws_response)
		if self.update_info["available"]:
			self.send_plugin_message("Firmware update available", "warning", text="Version %s" % self.update_info["ota"]["fw_version"])
			self._logger.info("Firmware update available (Version %s)" % self.update_info["ota"]["fw_version"])
			self._plugin_manager.send_plugin_message(self._identifier, dict(type="update_available", value=True))
			return
		else:
			self.send_plugin_message("Firmware is up to date", "success")
			self._logger.info("Firmware is up to date")
			self._plugin_manager.send_plugin_message(self._identifier, dict(type="update_available", value=False))
			return

	def _process_M115_response(self, line):
		fwn_s = "FIRMWARE_NAME:"
		fwv_s = "FIRMWARE_VERSION:"
		scu_s = "SOURCE_CODE_URL:"
		pv_s = "PROTOCOL_VERSION:"
		mt_s = "MACHINE_TYPE:"
		ec_s = "EXTRUDER_COUNT:"

		printer_info = dict()
		printer_info["fw_name"] = line[line.index(fwn_s)+len(fwn_s):line.index(fwv_s)].strip()
		printer_info["fw_version"] = line[line.index(fwv_s)+len(fwv_s):line.index(scu_s)].strip()
		printer_info["source_code_url"] = line[line.index(scu_s)+len(scu_s):line.index(pv_s)].strip()
		printer_info["protocol_version"] = line[line.index(pv_s)+len(pv_s):line.index(mt_s)].strip()
		printer_info["printer_model"] = line[line.index(mt_s)+len(mt_s):line.index(ec_s)].strip()
		printer_info["extruder_count"] = line[line.index(ec_s)+len(ec_s):].strip()

		return printer_info

	#~~ Hooks

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/flashFirmwareWithPath", 1000 * 1024)]

	def serial_connection_message(self, comm_instance, script_type, script_name, *args, **kwargs):
		if not script_type == "gcode":
			return None

		if script_name == "afterPrinterConnected":
			prefix = None
			postfix = "M117 " + "Connected via OctoPrint" + "\n" # TODO: Translate this
			return prefix, postfix
		elif script_name == "beforePrinterDisconnected":
			prefix = None
			postfix = "M117\n"
			return prefix, postfix
		else:
			return None


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

	#~~ Asset API

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"])

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
        "octoprint.comm.protocol.scripts":__plugin_implementation__.serial_connection_message
    }