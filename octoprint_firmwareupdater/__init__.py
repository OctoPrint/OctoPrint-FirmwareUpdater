# coding=utf-8
from __future__ import absolute_import

import flask
import logging
import logging.handlers
import os
import requests
import tempfile
import threading
import shutil
import time
import octoprint.plugin

import octoprint.server.util.flask
from octoprint.server import admin_permission, NO_CONTENT
from octoprint.events import Events

# import the flash methods
from octoprint_firmwareupdater.methods import avrdude
from octoprint_firmwareupdater.methods import bossac
from octoprint_firmwareupdater.methods import dfuprog
from octoprint_firmwareupdater.methods import lpc1768
from octoprint_firmwareupdater.methods import stm32flash

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
                            octoprint.plugin.TemplatePlugin,
                            octoprint.plugin.AssetPlugin,
                            octoprint.plugin.SettingsPlugin,
							octoprint.plugin.EventHandlerPlugin):

	def __init__(self):
		self._flash_thread = None

		self._flash_prechecks = dict()
		self._flash_methods = dict()

		self._console_logger = None

	def initialize(self):
		# TODO: make method configurable via new plugin hook "octoprint.plugin.firmwareupdater.flash_methods",
		# also include prechecks
		self._flash_prechecks = dict(avrdude=avrdude._check_avrdude, bossac=bossac._check_bossac, dfuprogrammer=dfuprog._check_dfuprog, lpc1768=lpc1768._check_lpc1768, stm32flash=stm32flash._check_stm32flash)
		self._flash_methods = dict(avrdude=avrdude._flash_avrdude, bossac=bossac._flash_bossac, dfuprogrammer=dfuprog._flash_dfuprog, lpc1768=lpc1768._flash_lpc1768, stm32flash=stm32flash._flash_stm32flash)

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
			if not self._flash_prechecks[method](self):
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
		# Run pre-flash commandline here
		preflash_command = self._settings.get(["preflash_commandline"])
		if preflash_command is not None and self._settings.get_boolean(["enable_preflash_commandline"]):
			self._logger.info("Executing pre-flash commandline '{}'".format(preflash_command))
			try:
				r = os.system(preflash_command)
			except:
				e = sys.exc_info()[0]
				self._logger.error("Error executing pre-flash commandline '{}'".format(preflash_command))
			
			self._logger.info("Pre-flash command '{}' returned: {}".format(preflash_command, r))

		try:
			self._logger.info("Firmware update started")

			if not method in self._flash_methods:
				error_message = "Unsupported flashing method: {}".format(method)
				self._logger.error(error_message)
				self._send_status("flasherror", message=error_message)
				return

			flash_callable = self._flash_methods[method]
			if not callable(flash_callable):
				error_message = "Don't have a callable for flashing method {}: {!r}".format(method, flash_callable)
				self._logger.error(error_message)
				self._send_status("flasherror", message=error_message)
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
				if flash_callable(self, firmware=firmware, printer_port=printer_port):

					postflash_delay = self._settings.get(["postflash_delay"]) or 0
					if float(postflash_delay) > 0 and self._settings.get(["enable_postflash_delay"]):
						self._logger.info("Post-flash delay: {}s".format(postflash_delay))
						self._send_status("progress", subtype="postflashdelay")
						time.sleep(float(postflash_delay))

					message = u"Flashing successful."
					self._logger.info(message)
					self._console_logger.info(message)
					self._send_status("success")

					# Run post-flash commandline here
					postflash_command = self._settings.get(["postflash_commandline"])
					if postflash_command is not None and self._settings.get_boolean(["enable_postflash_commandline"]):
						self._logger.info("Executing post-flash commandline '{}'".format(postflash_command))
						try:
							r = os.system(postflash_command)
						except:
							e = sys.exc_info()[0]
							self._logger.error("Error executing post-flash commandline '{}'".format(postflash_command))
						
						self._logger.info("Post-flash command '{}' returned: {}".format(postflash_command, r))

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
			"avrdude_commandline": "{avrdude} -v -q -p {mcu} -c {programmer} -P {port} -D -C {conffile} -b {baudrate} {disableverify} -U flash:w:{firmware}:i",
			"bossac_path": None,
			"bossac_commandline": "{bossac} -i -p {port} -U true -e -w {disableverify} -b {firmware} -R",
			"bossac_disableverify": None,
			"dfuprog_path": None,
			"dfuprog_avrmcu": None,
			"dfuprog_commandline": "sudo {dfuprogrammer} {mcu} flash {firmware} --debug-level 10",
			"dfuprog_erasecommandline": "sudo {dfuprogrammer} {mcu} erase --debug-level 10 --force",
			"stm32flash_path": None,
			"stm32flash_verify": True,
			"stm32flash_boot0pin": "rts",
			"stm32flash_boot0low": False,
			"stm32flash_resetpin": "dtr",
			"stm32flash_resetlow": True,
			"stm32flash_execute": True,
			"stm32flash_executeaddress": "0x8000000",
			"stm32flash_reset": False,
			"lpc1768_path": None,
			"lpc1768_preflashreset": True,
			"postflash_delay": "0",
			"postflash_gcode": None,
			"run_postflash_gcode": False,
			"preflash_commandline": None,
			"postflash_commandline": None,
			"enable_preflash_commandline": None,
			"enable_postflash_commandline": None,
			"enable_postflash_delay": None,
			"enable_postflash_gcode": None,
			"disable_bootloadercheck": None,
			"enabledTab": True
		}

	#~~ Asset API

	def get_assets(self):
		return dict(
		js=["js/firmwareupdater.js"],
		css=["css/firmwareupdater.css"])

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
