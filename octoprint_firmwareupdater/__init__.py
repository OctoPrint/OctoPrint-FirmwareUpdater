# coding=utf-8
from __future__ import absolute_import

import flask
import json
import os
import requests
import tempfile
import time
import urllib
import urllib2
import urlparse

import octoprint.plugin

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin):

	#~~ Template API

	def get_template_configs(self):
		return [dict(type="sidebar",
					div="sidebar_plugin_firmwareupdater",
					name="Firmware Updater",
					custom_bindings=True,
					icon="bolt")]

	#~~ BluePrint API

	@octoprint.plugin.BlueprintPlugin.route("/flashFirmwareWithPath", methods=["POST"])
	def flash_firmware_with_path(self):

		if not self._check_avrdude():
			return flask.make_response("Error.", 500)

		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		uploaded_hex_path = flask.request.values[input_upload_path]
		selected_port = flask.request.values["selected_port"]

		import shutil
		try:
			temp_hex_file = tempfile.NamedTemporaryFile(mode='r+b')
			with open(os.path.abspath(uploaded_hex_path),'r+b') as f:
				shutil.copyfileobj(f, temp_hex_file)
		except Exception as e:
			self._logger.exception(u"Error when copying uploaded temp hex file: {error}".format(error=e))
		else:
			temp_hex_file.seek(0)

		# Create thread to flash firmware
		import threading
		flash_thread = threading.Thread(target=self._flash_worker, args=(temp_hex_file, selected_port))
		flash_thread.daemon = False
		flash_thread.start()

		return flask.make_response("Ok.", 200)

	@octoprint.plugin.BlueprintPlugin.route("/flashFirmwareWithURL", methods=["POST"])
	def flash_firmware_with_url(self):

		if not self._check_avrdude():
			return flask.make_response("Error.", 500)

		hex_url = flask.request.json['hex_url']
		self.selected_port = flask.request.json['selected_port']

		ret = self._flash_firmware_with_url(hex_url)

		if ret:
			return flask.make_response("Ok.", 200)
		else:
			return flask.make_response("Error.", 500)

	@octoprint.plugin.BlueprintPlugin.route("/flashUpdate", methods=["POST"])
	def flash_update(self):

		if not self._check_avrdude():
			return flask.make_response("Error.", 500)

		self.selected_port = flask.request.json['selected_port']

		if hasattr(self, "update_info"):
			ret = self._flash_firmware_with_url(self.update_info["ota"]["url"])

			if ret:
				return flask.make_response("Ok.", 200)
			else:
				return flask.make_response("Error.", 500)
		else:
			self._logger.exception(u"No update info found")
			self.send_message(message_title="No update info found", message_type="error")
			return flask.make_response("Error.", 500)

	def _flash_firmware_with_url(self, hex_url):

		temp_hex_file = tempfile.NamedTemporaryFile(mode='r+b')

		try:
			urllib.urlretrieve(hex_url, temp_hex_file.name)
		except Exception as e:
			self._logger.exception(u"Error when retrieving hex file from URL: {error}".format(error=e))
			return False

		# Create thread to flash firmware
		import threading
		flash_thread = threading.Thread(target=self._flash_worker, args=(temp_hex_file, self.selected_port))
		flash_thread.daemon = False
		flash_thread.start()

		return True

	def _flash_worker(self, hex_file, selected_port):

		avrdude_path = self._settings.get(["avrdude_path"])
		working_dir = os.path.dirname(avrdude_path)
		hex_path = hex_file.name
		avrdude_command = [avrdude_path, "-v", "-p", "m2560", "-c", "wiring", "-P", selected_port, "-U", "flash:w:" + hex_path + ":i", "-D"]

		import sarge
		self._logger.info(u"Running %r in %s" % (' '.join(avrdude_command), working_dir))
		try:
			p = sarge.run(avrdude_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
			p.wait_events()

			while p.returncode is None:
				line = p.stderr.read(timeout=0.5)
				if not line:
					p.commands[0].poll()
					continue
				print line
				if "avrdude: writing" in line:
					self._logger.info(u"Writing memory...")
					self.send_message("Writing memory...", "warning")
				elif "avrdude: verifying ..." in line:
					self._logger.info(u"Verifying memory...")
					self.send_message(message_title="Verifying memory...", message_type="warning")

				elif "timeout communicating with programmer" in line:
					e_msg = "Timeout communicating with programmer"
					raise AvrdudeException
				elif "avrdude: ERROR:" in line:
					e_msg = "Avrdude error: " + line[line.find("avrdude: ERROR:")+len("avrdude: ERROR"):].strip()
					raise AvrdudeException

			if p.returncode == 0:
				self._logger.info(u"Flashing successful.")
				self.send_message(message_title="Flashing successful", message_type="success")
				self.send_status(status_type="update_available", status_value=False) # TODO: Should be handled by the frontend
			else:
				e_msg = "Avrdude returned code {returncode}".format(returncode=p.returncode)
				raise AvrdudeException

		except AvrdudeException:
			self._logger.exception(u"Flashing failed. {error}.".format(error=e_msg))
			self.send_message(message_title="Flashing failed", message_type="error", message_text=e_msg)
		except Exception as e:
			self._logger.exception(u"Flashing failed. Unexpected error: {error}.".format(error=e))
			self.send_message(message_title="Flashing failed", message_type="error", message_text="Unexpected error")
		finally:
			hex_file.close()

	def _check_avrdude(self):
		avrdude_path = self._settings.get(["avrdude_path"])
		if not os.path.exists(avrdude_path):
			self._logger.exception(u"Path to avrdude does not exist: {path}".format(path=avrdude_path))
			return False
		elif not os.path.isfile(avrdude_path):
			self._logger.exception(u"Path to avrdude is not a file: {path}".format(path=avrdude_path))
			return False
		elif not os.access(avrdude_path, os.X_OK):
			self._logger.exception(u"Path to avrdude is not executable: {path}".format(path=avrdude_path))
			return False
		else:
			return True

	@octoprint.plugin.BlueprintPlugin.route("/checkForUpdates", methods=["GET"])
	def check_for_updates(self):
		self.send_message(message_title="Connecting to printer...", message_type="warning")

		self._printer.connect()

		return flask.make_response("Ok.", 200)

	#~~ EventHandler API

	def on_event(self, event, payload):
		if event == "Connected":

			if hasattr(self, "printer_info"):
				del self.printer_info
			if hasattr(self, "update_info"):
				del self.update_info

			self.callback = octoprint.printer.PrinterCallback()
			self.default_on_printer_add_message = self.callback.on_printer_add_message
			self.callback.on_printer_add_message = self.on_printer_add_message
			self._printer.register_callback(self.callback)

			self.send_message(message_title="Retrieving current FW version from printer...", message_type="warning")
			self._logger.info(u"Retrieving current FW version from printer...")
			self._printer.commands("M115\n")

			self.start_time = time.time()

			return

		elif event == "Disconnected":
			if hasattr(self, "printer_info"):
				del self.printer_info

	def on_printer_add_message(self, data):
		if time.time() - self.start_time > 60 or time.time() < self.start_time:
			if hasattr(self, "printer_info"):
				del self.printer_info
			# Unregister callback
			self.callback.on_printer_add_message = self.default_on_printer_add_message

			self.send_message(message_title="Unable to get FW version from printer", message_type="error")
			self._logger.exception(u"Unable to get FW version from printer")
			return

		elif not ("MACHINE_TYPE" in data and "FIRMWARE_VERSION" in data):
			return

		# Unregister callback
		self.callback.on_printer_add_message = self.default_on_printer_add_message

		self.printer_info = dict([pair.split(":") for pair in data.strip().split(" ")])

		self._logger.info(u"Current printer: %s (FW version: %s)" % (self.printer_info["MACHINE_TYPE"], self.printer_info["FIRMWARE_VERSION"]))

		printer_model = urllib.quote(self.printer_info["MACHINE_TYPE"])
		fw_version = urllib.quote(self.printer_info["FIRMWARE_VERSION"])
		fw_language = urllib.quote(self.printer_info["X-FIRMWARE_LANGUAGE"])
		ws_url = self._settings.get(["update_service_url"]).format(model=printer_model, fw_version=fw_version, language=fw_language)

		try:
			ws_response = requests.get(ws_url)
		except Exception as e:
			self.send_message(message_title="Unable to connect to update server", message_type="error")
			self._logger.exception(u"Unable to connect to update server: {error}".format(error=e))
			return

		if ws_response.status_code != 200:
			self.send_message(message_title="Unable to connect to update server", message_type="error", message_text="Got status code {sc}".format(sc=ws_response.status_code))
			self._logger.exception(u"Unable to connect to update server: Got status code {sc}".format(sc=ws_response.status_code))
			return

		self.update_info = ws_response.json()
		if self.update_info["available"]:
			self.send_message(message_title="Firmware update available", message_type="info", message_text="Version %s" % self.update_info["ota"]["fw_version"], replaceable=False)
			self._logger.info(u"Firmware update available (FW version: %s)" % self.update_info["ota"]["fw_version"])
			self.send_status(status_type="update_available", status_value=True)
			return
		else:
			self.send_message(message_title="Firmware is up to date", message_type="success")
			self._logger.info(u"Firmware is up to date")
			self.send_status(status_type="update_available", status_value=False)
			return

	#~~ Hooks

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/flashFirmwareWithPath", 1000 * 1024)]

	#~~ SettingsPlugin API

	def get_settings_defaults(self):
		return {
			"avrdude_path": None,
			"avrdude_config_path": None,
			"update_service_url": "http://localhost:8080/api/checkUpdate/{model}/{fw_version}/{language}"
		}

	def on_settings_save(self, data):
		for key in self.get_settings_defaults():
			if key in data:
				self._settings.set([key], data[key])

	#~~ Asset API

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"],
					css=["css/firmwareupdater.css"])

	#~~ Extra functions

	def send_message(self, message_title, message_type, message_text="", replaceable=True):
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="message", title=message_title, text=message_text, message_type=message_type, replaceable=replaceable))

	def send_status(self, status_type, status_value):
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="status", status_type=status_type, status_value=status_value))

	def send_progress(self, progress_percentage, progress_string, progress_ok=True):
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="progress", progress_percentage=progress_percentage, progress_string=progress_string, progress_ok=progress_ok))


class AvrdudeException(Exception):
	pass

__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	global __plugin_hooks__

	__plugin_implementation__ = FirmwareupdaterPlugin()

	__plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
    }