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
import shutil

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

	@octoprint.plugin.BlueprintPlugin.route("/uploadHexFile", methods=["POST"])
	def flash_firmware(self):

		print "Values = ", flask.request.values

		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		temp_path = flask.request.values[input_upload_path]
		dest_path = os.path.join(self._settings._basedir, "plugins", "FirmwareUpdater")

		if not os.path.exists(dest_path):
			try:
				os.mkdir(dest_path, 0775)
				self._logger.info("Creating directory for FirmwareUpdater plugin at {path}".format(path=dest_path))
			except Exception as e:
				self._logger.exception("Error when creating directory for FirmwareUpdater plugin: {error}".format(error=e))
				return flask.make_response("Error.", 500)  # TODO: Change this

		try:
			shutil.copyfile(os.path.abspath(temp_path), os.path.join(dest_path, "tempHexFile.hex"))
		except Exception as e:
			self._logger.exception("Error when copying uploaded temp hex file: {error}".format(error=e))

		return flask.make_response("Ok.", 200)  # TODO: Change this

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

__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = FirmwareupdaterPlugin()
