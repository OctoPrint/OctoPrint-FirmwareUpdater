# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import logging.handlers
import os
import requests
import tempfile
import threading

import octoprint.plugin

import octoprint.server.util.flask
from octoprint.server import admin_permission, NO_CONTENT

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.SettingsPlugin):

	AVRDUDE_WRITING = "writing flash"
	AVRDUDE_VERIFYING = "verifying ..."
	AVRDUDE_TIMEOUT = "timeout communicating with programmer"
	AVRDUDE_ERROR = "ERROR:"

	def __init__(self):
		self._flash_thread = None

		self._flash_prechecks = dict()
		self._flash_methods = dict()

		self._console_logger = None

	def initialize(self):
		# TODO: make method configurable via new plugin hook "octoprint.plugin.firmwareupdater.flash_methods",
		# also include prechecks
		self._flash_prechecks = dict(avrdude=self._check_avrdude)
		self._flash_methods = dict(avrdude=self._flash_avrdude)

		console_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="console"), maxBytes=2*1024*1024)
		console_logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
		console_logging_handler.setLevel(logging.DEBUG)

		self._console_logger = logging.getLogger("octoprint.plugins.softwareupdate.console")
		self._console_logger.addHandler(console_logging_handler)
		self._console_logger.setLevel(logging.DEBUG)
		self._console_logger.propagate = False

	#~~ BluePrint API

	@octoprint.plugin.BlueprintPlugin.route("/status", methods=["GET"])
	@octoprint.server.util.flask.restricted_access
	def status(self):
		return flask.jsonify(flashing=self._flash_thread is not None)

	@octoprint.plugin.BlueprintPlugin.route("/flash", methods=["POST"])
	@octoprint.server.util.flask.restricted_access
	@octoprint.server.admin_permission.require(403)
	def flash_firmware(self):
		if self._printer.is_printing():
			error_message = "Cannot flash firmware, printer is busy"
			self._send_status("flasherror", subtype="busy", message=error_message)
			return flask.make_response(error_message, 409)

		value_source = flask.request.json if flask.request.json else flask.request.values

		if not "port" in value_source:
			error_message = "Cannot flash firmware, printer port is not specified"
			self._send_status("flasherror", subtype="port", message=error_message)
			return flask.make_response(error_message, 400)

		method = value_source.get("method", "avrdude")
		if method in self._flash_prechecks:
			if not self._flash_prechecks[method]():
				error_message = "Cannot flash firmware, flash method {} is not fully configured".format(method)
				self._send_status("flasherror", subtype="method", message=error_message)
				return flask.make_response(error_message, 400)

		file_to_flash = None
		printer_port = value_source["port"]

		input_name = "file"
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		if input_upload_path in flask.request.values:
			# flash from uploaded file
			uploaded_hex_path = flask.request.values[input_upload_path]

			# create a temporary
			import shutil
			try:
				file_to_flash = tempfile.NamedTemporaryFile(mode='r+b', delete=False)
				file_to_flash.close()
				shutil.move(os.path.abspath(uploaded_hex_path), file_to_flash.name)
			except:
				if file_to_flash:
					try:
						os.remove(file_to_flash.name)
					except:
						self._logger.exception("Error while trying to delete the temporary hex file")

				error_message = "Error while copying the uploaded hex file"
				self._send_status("flasherror", subtype="hexfile", message=error_message)
				self._logger.exception(error_message)
				return flask.make_response(error_message, 500)

		elif "url" in value_source:
			# flash from provided URL
			url = value_source["url"]

			try:
				file_to_flash = tempfile.NamedTemporaryFile(mode='r+b', delete=False)
				file_to_flash.close()

				r = requests.get(url, stream=True, timeout=30)
				r.raise_for_status()
				with open(file_to_flash.name, "wb") as f:
					for chunk in r.iter_content(chunk_size=1024):
						if chunk:
							f.write(chunk)
							f.flush()

			except:
				if file_to_flash:
					try:
						os.remove(file_to_flash.name)
					except:
						self._logger.exception("Error while trying to delete the temporary hex file")

				error_message = "Error while retrieving the hex file from {}".format(url)
				self._send_status("flasherror", subtype="hexfile", message=error_message)
				self._logger.exception(error_message)
				return flask.make_response(error_message, 500)

		else:
			return flask.make_response("Neither file nor URL to flash from provided, cannot flash", 400)

		if self._start_flash_process(method, file_to_flash.name, printer_port):
			return flask.make_response(NO_CONTENT)
		else:
			error_message = "Cannot flash firmware, already flashing"
			self._send_status("flasherror", subtype="already_flashing")
			self._logger.debug(error_message)
			return flask.make_response(error_message, 409)

	def _start_flash_process(self, method, hex_file, printer_port):
		if self._flash_thread is not None:
			return False

		self._flash_thread = threading.Thread(target=self._flash_worker, args=(method, hex_file, printer_port))
		self._flash_thread.daemon = True
		self._flash_thread.start()

		return True

	def _flash_worker(self, method, firmware, printer_port):
		try:
			if not method in self._flash_methods:
				self._logger.error("Unsupported flashing method: {}".format(method))
				return

			flash_callable = self._flash_methods[method]
			if not callable(flash_callable):
				self._logger.error("Don't have a callable for flashing method {}: {!r}".format(method, flash_callable))
				return

			reconnect = None
			if self._printer.is_operational():
				_, current_port, current_baudrate, current_profile = self._printer.get_current_connection()

				if current_port == printer_port:
					reconnect = (current_port, current_baudrate, current_profile)
					self._logger.info("Disconnecting from printer")
					self._send_status("progress", subtype="disconnecting")
					self._printer.disconnect()

			self._send_status("progress", subtype="startingflash")

			try:
				if flash_callable(firmware=firmware, printer_port=printer_port):
					message = u"Flashing successful."
					self._logger.info(message)
					self._console_logger.info(message)
					self._send_status("success")
			except:
				self._logger.exception(u"Error while attempting to flash")
				self._send_status("flasherror")
			finally:
				try:
					os.remove(firmware)
				except:
					self._logger.exception(u"Could not delete temporary hex file at {}".format(firmware))

			if reconnect is not None:
				port, baudrate, profile = reconnect
				self._logger.info("Reconnecting to printer: port={}, baudrate={}, profile={}".format(port, baudrate, profile))
				self._send_status("progress", subtype="reconnecting")
				self._printer.connect(port=port, baudrate=baudrate, profile=profile)

		finally:
			self._flash_thread = None

	def _flash_avrdude(self, firmware=None, printer_port=None):
		assert(firmware is not None)
		assert(printer_port is not None)

		avrdude_path = self._settings.get(["avrdude_path"])
		avrdude_conf = self._settings.get(["avrdude_conf"])
		avrdude_avrmcu = self._settings.get(["avrdude_avrmcu"])
		avrdude_programmer = self._settings.get(["avrdude_programmer"])

		working_dir = os.path.dirname(avrdude_path)

		avrdude_command = [avrdude_path, "-v", "-p", avrdude_avrmcu, "-c", avrdude_programmer, "-P", printer_port, "-U", "flash:w:" + firmware + ":i", "-D"]
		if avrdude_conf is not None:
			avrdude_command += ["-C", avrdude_conf]

		import sarge
		self._logger.info(u"Running %r in %s" % (' '.join(avrdude_command), working_dir))
		self._console_logger.info(" ".join(avrdude_command))
		try:
			p = sarge.run(avrdude_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
			p.wait_events()

			while p.returncode is None:
				output = p.stderr.read(timeout=0.5)
				if not output:
					p.commands[0].poll()
					continue

				for line in output.split("\n"):
					if line.endswith("\r"):
						line = line[:-1]
					self._console_logger.info(u"> {}".format(line))

				if self.AVRDUDE_WRITING in output:
					self._logger.info(u"Writing memory...")
					self._send_status("progress", subtype="writing")
				elif self.AVRDUDE_VERIFYING in output:
					self._logger.info(u"Verifying memory...")
					self._send_status("progress", subtype="verifying")
				elif self.AVRDUDE_TIMEOUT in output:
					raise FlashException("Timeout communicating with programmer")
				elif self.AVRDUDE_ERROR in output:
					raise FlashException("Avrdude error: " + output[output.find(self.AVRDUDE_ERROR) + len(self.AVRDUDE_ERROR):].strip())

			if p.returncode == 0:
				return True
			else:
				raise FlashException("Avrdude returned code {returncode}".format(returncode=p.returncode))

		except FlashException as ex:
			self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
			self._send_status("flasherror", message=ex.reason)
			return False
		except:
			self._logger.exception(u"Flashing failed. Unexpected error.")
			self._send_status("flasherror")
			return False

	def _check_avrdude(self):
		avrdude_path = self._settings.get(["avrdude_path"])
		avrdude_avrmcu = self._settings.get(["avrdude_avrmcu"])
		avrdude_programmer = self._settings.get(["avrdude_programmer"])

		if not os.path.exists(avrdude_path):
			self._logger.error(u"Path to avrdude does not exist: {path}".format(path=avrdude_path))
			return False
		elif not os.path.isfile(avrdude_path):
			self._logger.error(u"Path to avrdude is not a file: {path}".format(path=avrdude_path))
			return False
		elif not os.access(avrdude_path, os.X_OK):
			self._logger.error(u"Path to avrdude is not executable: {path}".format(path=avrdude_path))
			return False
		elif not avrdude_avrmcu:
			self._logger.error(u"AVR MCU type has not been selected.")
			return False
		elif not avrdude_programmer:
			self._logger.error(u"AVR programmer has not been selected.")
			return False
		else:
			return True

	#~~ SettingsPlugin API

	def get_settings_defaults(self):
		return {
			"avrdude_path": None,
			"avrdude_conf": None,
			"avrdude_avrmcu": None,
			"avrdude_programmer": None
		}

	#~~ Asset API

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"])

	#~~ Extra methods

	def _send_status(self, status, subtype=None, message=None):
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="status",
		                                                                status=status,
		                                                                subtype=subtype,
		                                                                message=message))

	#~~ Hooks

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/flash", 1000 * 1024)]

	def update_hook(self):
		return dict(
			firmwareupdater=dict(
				displayName="Firmware Updater",
				displayVersion=self._plugin_version,

				# version check: github repository
				type="github_release",
				user="OctoPrint",
				repo="OctoPrint-FirmwareUpdater",
				current=self._plugin_version,

				# update method: pip
				pip="https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/{target_version}.zip"
			)
		)


class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason


__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	global __plugin_hooks__

	__plugin_implementation__ = FirmwareupdaterPlugin()

	__plugin_hooks__ = {
		"octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.update_hook
	}
