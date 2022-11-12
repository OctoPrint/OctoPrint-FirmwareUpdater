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
from octoprint.util import CaseInsensitiveSet, dict_merge

from past.builtins import basestring

# import the flash methods
from octoprint_firmwareupdater.methods import avrdude
from octoprint_firmwareupdater.methods import bootcmdr
from octoprint_firmwareupdater.methods import bossac
from octoprint_firmwareupdater.methods import dfuprog
from octoprint_firmwareupdater.methods import dfuutil
from octoprint_firmwareupdater.methods import esptool
from octoprint_firmwareupdater.methods import lpc1768
from octoprint_firmwareupdater.methods import stm32flash
from octoprint_firmwareupdater.methods import marlinbft

valid_boolean_trues = CaseInsensitiveSet(True, "true", "yes", "y", "1", 1)

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
        self._flash_prechecks = dict(
            avrdude=avrdude._check_avrdude,
            bootcmdr=bootcmdr._check_bootcmdr,
            bossac=bossac._check_bossac,
            dfuprogrammer=dfuprog._check_dfuprog,
            dfuutil=dfuutil._check_dfuutil,
            esptool=esptool._check_esptool,
            lpc1768=lpc1768._check_lpc1768,
            stm32flash=stm32flash._check_stm32flash,
            marlinbft=marlinbft._check_marlinbft
        )
        self._flash_methods = dict(
            avrdude=avrdude._flash_avrdude,
            bootcmdr=bootcmdr._flash_bootcmdr,
            bossac=bossac._flash_bossac,
            dfuprogrammer=dfuprog._flash_dfuprog,
            dfuutil=dfuutil._flash_dfuutil,
            esptool=esptool._flash_esptool,
            lpc1768=lpc1768._flash_lpc1768,
            stm32flash=stm32flash._flash_stm32flash,
            marlinbft=marlinbft._flash_marlinbft
        )

        console_logging_handler = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(postfix="console"), maxBytes=2*1024*1024)
        console_logging_handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
        console_logging_handler.setLevel(logging.DEBUG)

        self._console_logger = logging.getLogger("octoprint.plugins." + __name__ + ".console")
        self._console_logger.addHandler(console_logging_handler)
        self._console_logger.setLevel(logging.DEBUG)
        self._console_logger.propagate = False

        self._logger.info("Python binproto2 package installed: {}".format(marlinbft._check_binproto2(self)))

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
            error_message = "Cannot flash firmware, printer port was not specified"
            self._send_status("flasherror", subtype="port", message=error_message)
            return flask.make_response(error_message, 400)

        printer_port = value_source["port"]

        if not "profile" in value_source:
            error_message = "Cannot flash firmware, profile index was not specified"
            self._send_status("flasherror", subtype="profile", message=error_message)
            return flask.make_response(error_message, 400)

        profile_index = value_source["profile"]

        # Save the selected profile
        self._logger.info("Firmware update profile index: {}".format(profile_index))
        self._settings.set_int(['_selected_profile'], profile_index)
        self._logger.info("Firmware update profile name: {}".format(self.get_profile_setting("_name")))

        # Save the printer port
        self._logger.info("Printer port: {}".format(printer_port))
        if printer_port != "undefined":
            self.set_profile_setting("serial_port", printer_port)

        method = self.get_profile_setting("flash_method")
        self._logger.info("Flash method: {}".format(method))

        self._settings.save()

        if method in self._flash_prechecks:
            if not self._flash_prechecks[method](self):
                if method == "marlinbft":
                    error_message = "Marlin BINARY_FILE_TRANSFER capability is not supported"
                else:
                    error_message = "Cannot flash firmware, flash method {} is not fully configured".format(method)
                    self._send_status("flasherror", subtype="method", message=error_message)
                return flask.make_response(error_message, 400)

        file_to_flash = None

        input_name = "file"
        input_upload_path = input_name + "." + self._settings.global_get(["server", "uploads", "pathSuffix"])

        if input_upload_path in flask.request.values:
            # flash from uploaded file
            uploaded_hex_path = flask.request.values[input_upload_path]

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
        # Run pre-flash system command
        preflash_command = self.get_profile_setting("preflash_commandline")
        if preflash_command is not None and self.get_profile_setting_boolean("enable_preflash_commandline"):
            self._logger.info("Executing pre-flash commandline '{}'".format(preflash_command))
            try:
                r = os.system(preflash_command)
            except:
                e = sys.exc_info()[0]
                self._logger.error("Error executing pre-flash commandline '{}'".format(preflash_command))

            self._logger.info("Pre-flash command '{}' returned: {}".format(preflash_command, r))

        # Run pre-flash gcode
        preflash_gcode = self.get_profile_setting("preflash_gcode")
        if preflash_gcode is not None and self.get_profile_setting_boolean("enable_preflash_gcode"):
            if self._printer.is_operational():
                self._logger.info("Sending pre-flash gcode commands: {}".format(preflash_gcode))
                self._printer.commands(preflash_gcode.split(";"))

                preflash_delay = self.get_profile_setting_int("preflash_delay") or 3
                if float(preflash_delay) > 0 and self.get_profile_setting_boolean("enable_preflash_delay"):
                    self._logger.info("Pre-flash delay: {}s".format(preflash_delay))
                    time.sleep(float(preflash_delay))

            else:
                self._logger.info("Printer not connected, not sending pre-flash gcode commands")

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
                    postflash_delay = self.get_profile_setting_int("postflash_delay") or 0
                    if float(postflash_delay) > 0 and self.get_profile_setting_boolean("enable_postflash_delay"):
                        self._logger.info("Post-flash delay: {}s".format(postflash_delay))
                        self._send_status("progress", subtype="postflashdelay")
                        time.sleep(float(postflash_delay))

                    message = u"Flashing successful."
                    self._logger.info(message)
                    self._console_logger.info(message)
                    self._send_status("success")

                    # Run post-flash commandline
                    postflash_command = self.get_profile_setting("postflash_commandline")
                    if postflash_command is not None and self.get_profile_setting_boolean("enable_postflash_commandline"):
                        self._logger.info("Executing post-flash commandline '{}'".format(postflash_command))
                        try:
                            r = os.system(postflash_command)
                        except:
                            e = sys.exc_info()[0]
                            self._logger.error("Error executing post-flash commandline '{}'".format(postflash_command))

                        self._logger.info("Post-flash command '{}' returned: {}".format(postflash_command, r))

                    # Set run post-flash gcode flag
                    postflash_gcode = self.get_profile_setting("postflash_gcode")
                    if postflash_gcode is not None and self.get_profile_setting_boolean("enable_postflash_gcode"):
                        self._logger.info(u"Setting run_postflash_gcode flag to true")
                        self.set_profile_setting_boolean("run_postflash_gcode", True)

                    else:
                        self._logger.info(u"No postflash gcode or postflash is disabled, setting run_postflash_gcode to false")
                        self.set_profile_setting_boolean("run_postflash_gcode", False)

                    self._settings.save()

            except:
                self._logger.exception(u"Error while attempting to flash")
                self._send_status("flasherror")
            finally:
                try:
                    os.remove(firmware)
                except:
                    self._logger.exception(u"Could not delete temporary hex file at {}".format(firmware))

        finally:
            self._flash_thread = None

            if self.get_profile_setting_boolean("no_reconnect_after_flash"):
                self._logger.info("Automatic reconnection is disabled")
            else:
                if reconnect is not None:
                    port, baudrate, profile = reconnect
                    self._logger.info("Reconnecting to printer: port={}, baudrate={}, profile={}".format(port, baudrate, profile))
                    self._send_status("progress", subtype="reconnecting")
                    self._printer.connect(port=port, baudrate=baudrate, profile=profile)

    # Checks for a valid profile in the plugin's settings
    #   Returns True if the settings contain one or more profiles, otherwise false
    def check_for_profile(self):
        # Get all the profiles from the settings
        profiles = self._settings.get(["profiles"])

        # If the profiles aren't an array, make them one
        # Catches case when there are no profiles and the defaults are returned
        if not isinstance(profiles, list):
            profiles = [profiles]

        # If there is only one profile and the name is None there were no real profiles and we have the defaults
        if len(profiles) == 1 and profiles[0]["_name"] == None:
            return False
        else:
            return True

    # Gets the settings for the currently-selected profile
    #  Returns the configured profile settings if one is found at the index, otherwise None
    def get_selected_profile(self, **kwargs):
        # Get the currently-selected profile index
        index = kwargs.pop("index", self._settings.get_int(["_selected_profile"]))

        # Check that the index is valid
        if not isinstance(index, int) or index < 0:
            self._logger.warn("Invalid profile index '{}' specified".format(index))
            return None

        # Check that there is a valid profile in the settings
        if not self.check_for_profile():
            self._logger.warn("No profiles configured")
            return None

        # Get all the profiles from the settings
        profiles = self._settings.get(["profiles"])

        # If the profiles aren't an array, make them one
        if not isinstance(profiles, list):
            profiles = [profiles]

        # Check if the index is within the set of profiles; return the profile if it is, otherwise return None
        if len(profiles) >= index:
            return profiles[index]
        else:
            self._logger.warn("Profile with index {} not found. {} profiles are configured.".format(index, len(profiles)))
            return None

    # Gets all the settings for a profile - specified values and default values
    #  Merges the profile settings with the default settings and returns the complete set
    def get_profile_settings(self):
        # Get the selected profile's configured settings
        profile_settings = self.get_selected_profile()

        # Check if the profile is valid
        if profile_settings != None:
            # Get the profile defaults
            profile_defaults = self.get_settings_defaults()["_profiles"]

            # Merge the profile settings with the defaults
            profile = dict_merge(profile_defaults, profile_settings)

            # Return the superset of settings
            return profile
        else:
            return None

    # Gets the value of a specified setting from the profile
    #  Returns the value or None if the given key was not found in the profile
    def get_profile_setting(self, key):
        # Check if the key is valid
        if key != None:
            # Get the superset of profile settings
            profile = self.get_profile_settings()

            # Check if the profile is valid
            if profile == None:
                return None

            # Check if the key is present in the profile
            if key in profile.keys():
                # Return the value
                return profile[key]
            else:
                return None
        else:
            return None

    # Gets the integer value of a specified setting from the profile
    #  Returns the value or None if the given key was not found in the profile or is not an integer
    def get_profile_setting_int(self, key, **kwargs):
        minimum = kwargs.pop("min", None)
        maximum = kwargs.pop("max", None)

        value = self.get_profile_setting(key)
        if value is None:
            return None

        try:
            intValue = int(value)

            if minimum is not None and intValue < minimum:
                return minimum
            elif maximum is not None and intValue > maximum:
                return maximum
            else:
                return intValue
        except ValueError:
            self._logger.warning(
                "Could not convert %r to a valid integer when getting option %r"
                % (value, key)
            )
            return None

    # Gets the boolean value of a specified setting from the profile
    #  Returns the value or None if the given key was not found in the profile or is cannot be parsed as a boolean
    def get_profile_setting_boolean(self, key):
        value = self.get_profile_setting(key)
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, basestring):
            return value.lower() in valid_boolean_trues
        return value is not None


    # Sets the specified value in the profile
    def set_profile_setting(self, key, value):
        # Get the current value
        current_value = self.get_profile_setting(key)

        # Check if the new value matches the current value
        if current_value == value:
            # Don't need to modify a setting which isn't changing
            return

        # Get the default value
        default_value = self.get_settings_defaults()["_profiles"][key]

        # Get all the profile settings
        profiles = self._settings.get(["profiles"])

        # Check if the new value matches the default
        if default_value == value:
            # Don't need to store default values so remove the setting from the profile
            del profiles[self._settings.get_int(["_selected_profile"])][key]
        else:
            # Update this setting in the profile
            profiles[self._settings.get_int(["_selected_profile"])][key] = value

        # Save the settings
        profiles = self._settings.set(["profiles"], profiles)

    # Sets the specified int value in the profile
    def set_profile_setting_int(self, key, value, **kwargs):
        if value is None:
            self.set_profile_setting(key, None)
            return

        minimum = kwargs.pop("min", None)
        maximum = kwargs.pop("max", None)

        try:
            intValue = int(value)

            if minimum is not None and intValue < minimum:
                intValue = minimum
            if maximum is not None and intValue > maximum:
                intValue = maximum
        except ValueError:
            self._logger.warning(
                "Could not convert %r to a valid integer when setting option %r"
                % (value, key)
            )
            return

        self.set_profile_setting(key, intValue)

    # Sets the specified boolean value in the profile
    def set_profile_setting_boolean(self, key, value):
        if value is None or isinstance(value, bool):
            self.set_profile_setting(key, value)
        elif isinstance(value, basestring) and value.lower() in valid_boolean_trues:
            self.set_profile_setting(key, True)
        else:
            self.set_profile_setting(key, False)

    # Gets the last BFT filename for the current profile
    def get_lastbft_filename(self):
        profile_id = self.get_profile_setting_int("_id")
        if profile_id != None:
            filenames = self._settings.get(["last_bft_filenames"])
            if filenames == None:
                return None
            if profile_id in filenames.keys():
                return filenames[profile_id]
            elif str(profile_id) in filenames.keys():
                return filenames[str(profile_id)]
            else:
                return None
        else:
            return None

    # Sets the last BFT filename for the current profile
    def set_lastbft_filename(self, value):
        profile_id = self.get_profile_setting_int("_id")
        last_bft_filenames = self._settings.get(["last_bft_filenames"])
        last_bft_filenames[profile_id] = value
        self._settings.set(["last_bft_filenames"], last_bft_filenames)

    # Send capability information to the UI
    def _send_capability(self, capability, enabled):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="capability", capability=capability, enabled=enabled))

    # Send status messages to the UI
    def _send_status(self, status, subtype=None, message=None):
        self._plugin_manager.send_plugin_message(self._identifier, dict(type="status", status=status, subtype=subtype, message=message))

    #~~ SettingsPlugin API
    def get_settings_defaults(self):
        return {
            "_selected_profile": None,
            "_plugin_version": self._plugin_version,
            "enable_navbar": False,
            "enable_profiles": False,
            "save_url": False,
            "has_bftcapability": False,
            "has_binproto2package": False,
            "disable_filefilter": False,
            "prevent_connection_when_flashing": True,
            "maximum_fw_size_kb": 5120,
            "last_bft_filenames": {},
            "profiles": {},
            "_profiles": {
                "_id": None,
                "_name": None,
                "flash_method": None,
                "disable_bootloadercheck": False,
                "last_url": None,
                "avrdude_path": None,
                "avrdude_conf": None,
                "avrdude_avrmcu": None,
                "avrdude_programmer": None,
                "avrdude_baudrate": None,
                "avrdude_disableverify": False,
                "avrdude_commandline": "{avrdude} -v -q -p {mcu} -c {programmer} -P {port} -D -C {conffile} -b {baudrate} {disableverify} -U flash:w:{firmware}:i",
                "bootcmdr_path": None,
                "bootcmdr_preflashreset": True,
                "bootcmdr_commandline": "{bootcommander} -d={port} -b={baudrate} {firmware}",
                "bootcmdr_baudrate": 115200,
                "bootcmdr_command_timeout": 30,
                "bossac_path": None,
                "bossac_commandline": "{bossac} -i -p {port} -U true -e -w {disableverify} -b {firmware} -R",
                "bossac_disableverify": False,
                "dfuprog_path": None,
                "dfuprog_avrmcu": None,
                "dfuprog_commandline": "sudo {dfuprogrammer} {mcu} flash {firmware} --debug-level 10",
                "dfuprog_erasecommandline": "sudo {dfuprogrammer} {mcu} erase --debug-level 10 --force",
                "dfuutil_path": None,
                "dfuutil_commandline": "sudo {dfuutil} -a 0 -s 0x8000000:leave -D {firmware}",
                "esptool_path": None,
                "esptool_chip": "auto",
                "esptool_address": "0x10000",
                "esptool_baudrate": 921600,
                "esptool_commandline": "{esptool} -p {port} -c {chip} -b {baud} --before default_reset --after hard_reset write_flash -z -fm dio {address} {firmware}",
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
                "lpc1768_unmount_command": "sudo umount {mountpoint}",
                "lpc1768_preflashreset": True,
                "lpc1768_no_m997_reset_wait": False,
                "lpc1768_no_m997_restart_wait": False,
                "lpc1768_use_custom_filename": False,
                "lpc1768_custom_filename": "firmware.bin",
                "lpc1768_timestamp_filenames": False,
                "lpc1768_last_filename": None,
                "marlinbft_waitafterconnect": 0,
                "marlinbft_timeout": 1000,
                "marlinbft_progresslogging": False,
                "marlinbft_alt_reset": False,
                "marlinbft_m997_reset_wait": 10,
                "marlinbft_m997_restart_wait": 20,
                "marlinbft_no_m997_reset_wait": False,
                "marlinbft_no_m997_restart_wait": False,
                "marlinbft_use_custom_filename": False,
                "marlinbft_custom_filename": "firmware.bin",
                "marlinbft_timestamp_filenames": False,
                "marlinbft_last_filename": None,
                "marlinbft_got_start": False,
                "postflash_delay": 0,
                "preflash_delay": 3,
                "postflash_gcode": None,
                "preflash_gcode": None,
                "run_postflash_gcode": False,
                "preflash_commandline": None,
                "postflash_commandline": None,
                "enable_preflash_commandline": False,
                "enable_postflash_commandline": False,
                "enable_postflash_delay": False,
                "enable_preflash_delay": False,
                "enable_postflash_gcode": False,
                "enable_preflash_gcode": False,
                "disable_bootloadercheck": False,
                "no_reconnect_after_flash": False,
                "serial_port": None,
            },
        }

    def get_settings_version(self):
        return 3

    def on_settings_migrate(self, target, current=None):
        if current is None or current < 2:
            # Migrate single printer settings to a profile
            self._logger.info("Migrating plugin settings to a profile")

            # Create a new empty array of printer profiles
            profiles_new = []

            # Get a dictionary of the default printer profile settings
            settings_dict = self.get_settings_defaults()["_profiles"]

            # Get the names of all the printer profile settings
            keys = self.get_settings_defaults()["_profiles"].keys()

            # Iterate over each setting in the defaults
            for key in keys:
                # Get the current value
                value = self._settings.get([key])

                # Get the default value
                default_value = settings_dict[key]

                # If the current value is an empty string, and the default is 'None' set the value to 'None'
                if (value == "" and settings_dict[key] == None):
                    value = None

                # If the current value is None, and the default is a string set the value to the default
                if (value == None and settings_dict[key] != None):
                    value = settings_dict[key]

                # If the current value is a number stored it as a string, convert it to a number
                try:
                    # Python 3 compatible
                    if isinstance(value, str) and value.isnumeric():
                        value = int(value)
                except:
                    try:
                        # Python 2 compatible
                        uvalue = unicode(value)
                        if isinstance(uvalue, unicode) and uvalue.isnumeric():
                            value = int(uvalue)
                    except:
                        self._logger.warn(u"{}: unable to convert '{}' to a numeric value. Will be reset to default.".format(key, value))


                # If the the default value is a number but the current value is not, reset the value to the default
                if isinstance(default_value, int) and not isinstance(value, int):
                    self._logger.warn(u"{}: current value '{}' should be a number but isn't, resetting to default value of '{}'".format(key, value, default_value))
                    value = default_value

                # If the current value isn't the same as the default value, set the value otherwise delete it (so we don't set things to their default unnecessarily)
                if (value != settings_dict[key]):
                    self._logger.info(u"{}: {} (default is '{}')".format(key, value, default_value))
                    settings_dict[key] = value
                else:
                    del settings_dict[key]

                self._settings.set([key], None)

            # Give the new profile a default ID and name
            settings_dict["_id"] = 0
            settings_dict["_name"] = "Default"

            # Append the new profile and save the settings
            profiles_new.append(settings_dict)
            self._settings.set(['profiles'], profiles_new)

            # Set the profile to the new one
            self._settings.set_int(['_selected_profile'], 0)

        elif current == 2:
            profiles_new = []
            last_bft_filenames_new = {}
            # Loop through the profiles
            for index, profile in enumerate(self._settings.get(['profiles'])):
                self._logger.info("Migrating settings for profile {}: {}".format(index, profile["_name"]))
                # Set the id to the index
                profile["_id"] = index

                # Migrate the last BFT filesnames
                if "marlinbft_last_filename" in profile and profile["marlinbft_last_filename"] is not None:
                    last_bft_filenames_new.update({index: profile["marlinbft_last_filename"]})
                    del profile["marlinbft_last_filename"]

                profiles_new.append(profile)

            self._settings.set(['last_bft_filenames'],last_bft_filenames_new)
            self._settings.set(['profiles'],profiles_new)

    #~~ EventHandlerPlugin API
    def on_event(self, event, payload):
        # Only handle the CONNECTED event
        if event == Events.CONNECTED:
            self._logger.info("Got CONNECTED event")

            # Check if the current profile has the postflash gcode flag set
            if self.get_profile_setting_boolean("run_postflash_gcode"):
                self._logger.info("Run postflash gcode flag is set")

                # Get the postflash gcode from the profile
                postflash_gcode = self.get_profile_setting("postflash_gcode")

                # If there is something to send, send it
                if postflash_gcode is not None:
                    self._logger.info("Sending post-flash commands: {}".format(postflash_gcode))
                    self._printer.commands(postflash_gcode.split(";"))

                # Clear the postflash gcode flag
                self._logger.info("Clearing postflash gcode flag")
                self.set_profile_setting_boolean("run_postflash_gcode", False)
                self._settings.save()

            else:
                self._logger.info("Run postflash flag is not set")

    #~~ AssetPlugin API
    def get_assets(self):
        return dict(
            js=["js/firmwareupdater.js"],
            css=["css/firmwareupdater.css"]
        )

    #~~ Hook handlers
    ##~~ Capabilites hook
    def firmware_capability_hook(self, comm_instance, capability, enabled, already_defined):
        del comm_instance, already_defined
        if capability.lower() == "BINARY_FILE_TRANSFER".lower():
            self._logger.info("Setting BINARY_FILE_TRANSFER capability to %s" % (enabled))
            self._settings.set_boolean(["has_bftcapability"], enabled)
            self._settings.save()
            self._send_capability("BINARY_FILE_TRANSFER", enabled)

    ##~~ Bodysize hook
    def bodysize_hook(self, current_max_body_sizes, *args, **kwargs):
        # Max size is (maximum_fw_size_kb * 1024) + 1024B to allow for API overhead
        max_size = (self._settings.get(["maximum_fw_size_kb"]) * 1024) + 1024
        self._logger.info("Setting maximum upload size for /flash to %s" % (max_size))
        return [("POST", r"/flash", max_size)]

    ##~~ Connect hook
    def handle_connect_hook(self, *args, **kwargs):
        if self._settings.get_boolean(["prevent_connection_when_flashing"]) and self._flash_thread:
            self._logger.info("Flash in progress, preventing connection to printer")
            return True
        else:
            return False

    ##~~ Comm Hook
    def check_for_start(self, comm, line, *args, **kwargs):
        if line.strip().strip("\0") == "start" and self._flash_thread:
            self._logger.info("Got start event while flashing in progress")
            self.set_profile_setting_boolean("marlinbft_got_start", True)
        else:
            return line

    ##~~ Update hook
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

                # stable releases
                stable_branch=dict(
                    name="Stable",
                    branch="master",
                    comittish=["master"]
                ),

                # release candidates
                prerelease_branches=[
                    dict(
                        name="Release Candidate",
                        branch="rc",
                        comittish=["rc", "master"],
                    ),
                    dict(
                        name="Development",
                        branch="devel",
                        comittish=["devel", "rc", "master"],
                    )
                ],

                # update method: pip
                pip="https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/{target_version}.zip"
            )
        )

    def is_blueprint_csrf_protected(self):
        return True

class FlashException(Exception):
    def __init__(self, reason, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
        self.reason = reason

__plugin_name__ = "Firmware Updater"
__plugin_pythoncompat__ = ">=2.7,<4"

def __plugin_load__():
    global __plugin_implementation__
    global __plugin_hooks__

    __plugin_implementation__ = FirmwareupdaterPlugin()

    __plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.bodysize_hook,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.update_hook,
        "octoprint.comm.protocol.firmware.capabilities": __plugin_implementation__.firmware_capability_hook,
        "octoprint.printer.handle_connect": __plugin_implementation__.handle_connect_hook,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.check_for_start,
    }
