# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import logging.handlers
import os
import requests
import tempfile
import threading
import time
import re
import serial
from serial import SerialException

import octoprint.plugin

import octoprint.server.util.flask
from octoprint.server import admin_permission, NO_CONTENT
from octoprint.events import Events

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin):

	AVRDUDE_WRITING = "writing flash"
	AVRDUDE_VERIFYING = "reading on-chip flash data"
	AVRDUDE_TIMEOUT = "timeout communicating with programmer"
	AVRDUDE_ERROR = "ERROR:"
	AVRDUDE_ERROR_SYNC = "not in sync"
	AVRDUDE_ERROR_VERIFICATION = "verification error"
	AVRDUDE_ERROR_DEVICE = "can't open device"

	BOSSAC_ERASING = "Erase flash"
	BOSSAC_WRITING = "bytes to flash"
	BOSSAC_VERIFYING = "bytes of flash"
	BOSSAC_NODEVICE = "No device found on"

	def __init__(self):
		self._flash_thread = None

		self._flash_prechecks = dict()
		self._flash_methods = dict()

		self._console_logger = None

	def initialize(self):
		# TODO: make method configurable via new plugin hook "octoprint.plugin.firmwareupdater.flash_methods",
		# also include prechecks
		self._flash_prechecks = dict(avrdude=self._check_avrdude, bossac=self._check_bossac)
		self._flash_methods = dict(avrdude=self._flash_avrdude, bossac=self._flash_bossac)

		console_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="console"), maxBytes=2*1024*1024)
		console_logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
		console_logging_handler.setLevel(logging.DEBUG)

		self._console_logger = logging.getLogger("octoprint.plugins.softwareupdate.console")
		self._console_logger.addHandler(console_logging_handler)
		self._console_logger.setLevel(logging.DEBUG)
		self._console_logger.propagate = False


	# Event handler
	def on_event(self, event, payload):
		#self._logger.info("Got event: {}".format(event))
		if event == Events.CONNECTED:
			self._logger.info("Got CONNECTED event")
			if self._settings.get_boolean(["run_postflash_gcode"]):
				self._logger.info("Run postflash flag is set")
				postflash_gcode = self._settings.get(["postflash_gcode"])

				if postflash_gcode is not None:
					# Run post-flash commands
					self._logger.info("Sending post-flash commands:{}".format(postflash_gcode))
					self._printer.commands(postflash_gcode.split(";"))

				self._logger.info("Clearing postflash flag")
				self._settings.set_boolean(["run_postflash_gcode"], False)
				self._settings.save()

			else:
				self._logger.info("Run postflash flag is not set")


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

		method = self._settings.get(["flash_method"])

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
			self._logger.info("Firmware update started")

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

					postflash_gcode = self._settings.get(["postflash_gcode"])
					if postflash_gcode is not None and self._settings.get_boolean(["enable_postflash_gcode"]):
						self._logger.info(u"Setting run_postflash_gcode flag to true")
						self._settings.set_boolean (["run_postflash_gcode"], True)
					else:
						self._logger.info(u"No postflash gcode or postflash is disabled, setting run_postflash_gcode to false")
						self._settings.set_boolean(["run_postflash_gcode"], False)

					self._settings.save()

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

			postflash_gcode = self._settings.get(["postflash_gcode"])

		finally:
			self._flash_thread = None

	def _flash_avrdude(self, firmware=None, printer_port=None):
		assert(firmware is not None)
		assert(printer_port is not None)

		avrdude_path = self._settings.get(["avrdude_path"])
		avrdude_conf = self._settings.get(["avrdude_conf"])
		avrdude_avrmcu = self._settings.get(["avrdude_avrmcu"])
		avrdude_programmer = self._settings.get(["avrdude_programmer"])
		avrdude_baudrate = self._settings.get(["avrdude_baudrate"])
		avrdude_disableverify = self._settings.get(["avrdude_disableverify"])

		working_dir = os.path.dirname(avrdude_path)

		avrdude_command = [avrdude_path, "-v", "-q", "-p", avrdude_avrmcu, "-c", avrdude_programmer, "-P", printer_port, "-D"]
		if avrdude_conf is not None and avrdude_conf != "":
			avrdude_command += ["-C", avrdude_conf]
		if avrdude_baudrate is not None and avrdude_baudrate != "":
			avrdude_command += ["-b", avrdude_baudrate]
		if avrdude_disableverify:
			avrdude_command += ["-V"]

		avrdude_command += ["-U", "flash:w:" + firmware + ":i"]

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
					p.commands[0].kill()
					p.close()
					raise FlashException("Timeout communicating with programmer")
				elif self.AVRDUDE_ERROR_DEVICE in output:
					p.commands[0].kill()
					p.close()
					raise FlashException("Error opening serial device")
				elif self.AVRDUDE_ERROR_VERIFICATION in output:
					p.commands[0].kill()
					p.close()
					raise FlashException("Error verifying flash")
				elif self.AVRDUDE_ERROR_SYNC in output:
					p.commands[0].kill()
					p.close()
					raise FlashException("Avrdude says: 'not in sync" + output[output.find(self.AVRDUDE_ERROR_SYNC) + len(self.AVRDUDE_ERROR_SYNC):].strip() + "'")
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
		pattern = re.compile("^(\/[^\0/]+)+$")

		if not pattern.match(avrdude_path):
			self._logger.error(u"Path to avrdude is not valid: {path}".format(path=avrdude_path))
			return False
		elif not os.path.exists(avrdude_path):
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

	def _flash_bossac(self, firmware=None, printer_port=None):
		assert(firmware is not None)
		assert(printer_port is not None)

		bossac_path = self._settings.get(["bossac_path"])
		bossac_disableverify = self._settings.get(["bossac_disableverify"])

		working_dir = os.path.dirname(bossac_path)

		bossac_command = [bossac_path, "-i", "-p", printer_port, "-e", "-w"]
		if not bossac_disableverify:
			bossac_command += ["-v"]
		bossac_command += ["-b", firmware, "-R"]

		self._logger.info(u"Attempting to reset the board to SAM-BA")
		if not self._reset_1200(printer_port):
			self._logger.error(u"Reset failed")
			return False

		import sarge
		self._logger.info(u"Running %r in %s" % (' '.join(bossac_command), working_dir))
		self._console_logger.info(" ".join(bossac_command))
		try:
			p = sarge.run(bossac_command, cwd=working_dir, async=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
			p.wait_events()

			while p.returncode is None:
				output = p.stdout.read(timeout=0.5)
				if not output:
					p.commands[0].poll()
					continue

				for line in output.split("\n"):
					if line.endswith("\r"):
						line = line[:-1]
					self._console_logger.info(u"> {}".format(line))

					if self.BOSSAC_ERASING in line:
						self._logger.info(u"Erasing memory...")
						self._send_status("progress", subtype="erasing")
					elif self.BOSSAC_WRITING in line:
						self._logger.info(u"Writing memory...")
						self._send_status("progress", subtype="writing")
					elif self.BOSSAC_VERIFYING in line:
						self._logger.info(u"Verifying memory...")
						self._send_status("progress", subtype="verifying")
					elif self.AVRDUDE_TIMEOUT in line:
						p.close()
						raise FlashException("Timeout communicating with programmer")
					elif self.BOSSAC_NODEVICE in line:
						raise FlashException("No device found")
					elif self.AVRDUDE_ERROR_VERIFICATION in line:
						raise FlashException("Error verifying flash")
					elif self.AVRDUDE_ERROR in line:
						raise FlashException("bossac error: " + output[output.find(self.AVRDUDE_ERROR) + len(self.AVRDUDE_ERROR):].strip())

			if p.returncode == 0:
				self._send_status("progress", subtype="wait_at_end")
				time.sleep(10) # wait for serial port to wake up
				return True
			else:
				raise FlashException("bossac returned code {returncode}".format(returncode=p.returncode))

		except FlashException as ex:
			self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
			self._send_status("flasherror", message=ex.reason)
			return False
		except:
			self._logger.exception(u"Flashing failed. Unexpected error.")
			self._send_status("flasherror")
			return False

	def _check_bossac(self):
		bossac_path = self._settings.get(["bossac_path"])
		pattern = re.compile("^(\/[^\0/]+)+$")

		if not pattern.match(bossac_path):
			self._logger.error(u"Path to bossac is not valid: {path}".format(path=bossac_path))
			return False
		elif bossac_path is None:
			self._logger.error(u"Path to bossac is not set.")
			return False
		if not os.path.exists(bossac_path):
			self._logger.error(u"Path to bossac does not exist: {path}".format(path=bossac_path))
			return False
		elif not os.path.isfile(bossac_path):
			self._logger.error(u"Path to bossac is not a file: {path}".format(path=bossac_path))
			return False
		elif not os.access(bossac_path, os.X_OK):
			self._logger.error(u"Path to bossac is not executable: {path}".format(path=bossac_path))
			return False
		else:
			return True

	def _reset_1200(self, printer_port=None):
		assert(printer_port is not None)
		self._logger.info(u"Toggling '{port}' at 1200bps".format(port=printer_port))
		try:
			os.system("stty -F "+printer_port+" speed 1200")
			time.sleep(5)
		except:
			self._logger.exception(u"Board reset failed: {error}".format(error=str(ex)))
			self._send_status("flasherror", message="Board reset failed")
			return False

		return True

	#~~ SettingsPlugin API

	def get_settings_defaults(self):
		return {
			"flash_method": None,
			"avrdude_path": None,
			"avrdude_conf": None,
			"avrdude_avrmcu": None,
			"avrdude_programmer": None,
			"avrdude_baudrate": None,
			"avrdude_disableverify": None,
			"bossac_path": None,
			"bossac_disableverify": None,
			"postflash_gcode": None,
			"run_postflash_gcode": False,
			"enable_postflash_gcode": None,
			"disable_bootloadercheck": None
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
