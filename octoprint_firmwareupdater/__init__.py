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

from octoprint.settings import settings

class FirmwareupdaterPlugin(octoprint.plugin.BlueprintPlugin,
							octoprint.plugin.TemplatePlugin,
							octoprint.plugin.AssetPlugin,
							octoprint.plugin.SettingsPlugin):

	def get_assets(self):
		return dict(js=["js/firmwareupdater.js"])

	@octoprint.plugin.BlueprintPlugin.route("/uploadHexFile", methods=["POST"])
	def flash_firmware(self):
		input_name = "file"
		input_upload_name = input_name + "." + self._settings.global_get(["server", "uploads", "nameSuffix"])
		input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

		temp_path = flask.request.values[input_upload_path]
		dest_path = os.path.join(self._basefolder, "uploads", "hexFile.hex")
		shutil.copyfile(os.path.abspath(temp_path), dest_path)

		# Create thread to flash firmware

		import threading

		flash_thread = threading.Thread(target=self._flash_worker, args=(dest_path,))
		flash_thread.daemon = False
		flash_thread.start()

		return flask.make_response("Ok.", 200)

	def _flash_worker(self, hex_path):
		avrdude_path = "/usr/bin/avrdude"
		avrdude_args = ["-p m2560", "-c stk500", "-P /dev/ttyUSB0", "-U flash:w:" + hex_path]
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
		print "Progress stage = ", result
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="progress_stage", result=result))

	def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
		return [("POST", r"/uploadHexFile", 1000 * 1024)]



__plugin_name__ = "Firmware Updater"

def __plugin_load__():
	global __plugin_implementation__
	global __plugin_hooks__

	__plugin_implementation__ = FirmwareupdaterPlugin()
	__plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook
    }