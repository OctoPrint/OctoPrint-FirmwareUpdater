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

import octoprint.plugin
import octoprint.settings

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin):

	#~~ Asset API

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"])

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

		hex_dir = os.path.join(self._settings._basedir, "plugins", "FirmwareUpdater")
		hex_path = os.path.join(hex_dir, hex_filename)

		if not os.path.exists(avrdude_path):
			self._logger.exception("Path to avrdude does not exist: {path}".format(path=avrdude_path))
			return flask.make_response("Error.", 500)  # TODO: Change this

		if not os.path.exists(hex_dir):
			try:
				os.mkdir(hex_dir, 0775)
				self._logger.info("Creating directory for FirmwareUpdater plugin at {path}".format(path=hex_dir))
			except Exception as e:
				self._logger.exception("Error when creating directory for FirmwareUpdater plugin: {error}".format(error=e))
				return flask.make_response("Error.", 500)  # TODO: Change this

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
		try:
			hex_url = flask.request.json['hex_url']
			avrdude_path = flask.request.json['avrdude_path']
			selected_port = flask.request.json['selected_port']
		except Exception as e:
			self._logger.exception("Error when parsing parameters sent to flash with URL: {error}".format(error=e))
			return flask.make_response("Error.", 500)  # TODO: Change this

		import urlparse
		hex_filename = os.path.split(urlparse.urlparse(hex_url).path)[-1] # A bit too much?
		hex_dir = os.path.join(self._settings._basedir, "plugins", "FirmwareUpdater")
		hex_path = os.path.join(hex_dir, hex_filename)

		if not os.path.exists(hex_dir):
			try:
				os.mkdir(hex_dir, 0775) # cross platform compatible?
				self._logger.info("Creating directory for FirmwareUpdater plugin at {path}".format(path=hex_dir))
			except Exception as e:
				self._logger.exception("Error when creating directory for FirmwareUpdater plugin: {error}".format(error=e))
				return flask.make_response("Error.", 500)  # TODO: Change this

		import urllib
		try:
			hex_path, _ = urllib.urlretrieve(hex_url, hex_path)
		except Exception as e:
			self._logger.exception("Error when retrieving hex file from URL: {error}".format(error=e))
			return flask.make_response("Error.", 500)  # TODO: Change this

		if not os.path.exists(avrdude_path):
			self._logger.exception("Path to avrdude does not exist: {path}".format(path=avrdude_path))
			return flask.make_response("Error.", 500)  # TODO: Change this

		# Create thread to flash firmware
		import threading
		flash_thread = threading.Thread(target=self._flash_worker, args=(avrdude_path, hex_path, selected_port))
		flash_thread.daemon = False
		flash_thread.start()

		return flask.make_response("Ok.", 200)

	def _flash_worker(self, avrdude_path, hex_path, selected_port):
		avrdude_args = ["-p m2560", "-c stk500", "-P", selected_port, "-U flash:w:" + hex_path]
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
				self._send_progress_stage_update("Writing memory...")
			elif "avrdude: verifying ..." in line:
				self._logger.info(u"Verifying memory...")
				self._send_progress_stage_update("Verifying memory...")

		if p.returncode == 0:
			self._logger.info(u"Flashing successful.")
		else:
			self._logger.info(u"Flashing failed with return code {returncode}.".format(returncode=p.returncode))

	def _send_progress_stage_update(self, result):
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="progress_stage", result=result))

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

	# Hooks

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/flashFirmwareWithPath", 1000 * 1024)]



__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	global __plugin_hooks__

	__plugin_implementation__ = FirmwareupdaterPlugin()
	__plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
    }