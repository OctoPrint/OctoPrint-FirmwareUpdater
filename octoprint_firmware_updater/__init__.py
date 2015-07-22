# coding=utf-8
from __future__ import absolute_import

### (Don't forget to remove me)
# This is a basic skeleton for your plugin's __init__.py. You probably want to adjust the class name of your plugin
# as well as the plugin mixins it's subclassing from. This is really just a basic skeleton to get you started,
# defining your plugin as a template plugin.
#
# Take a look at the documentation on what other plugin mixins are available.

import octoprint.plugin

class Firmware_updaterPlugin(octoprint.plugin.TemplatePlugin):
	# TODO Implement me!
	pass

# If you want your plugin to be registered within OctoPrint under a different name than what you defined in setup.py
# ("OctoPrint-PluginSkeleton"), you may define that here. Same goes for the other metadata derived from setup.py that
# can be overwritten via __plugin_xyz__ control properties. See the documentation for that.
__plugin_name__ = "Firmware_updater Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = Firmware_updaterPlugin()

	# global __plugin_hooks__
	# __plugin_hooks__ = {
	#    "some.octoprint.hook": __plugin_implementation__.some_hook_handler
	# }

