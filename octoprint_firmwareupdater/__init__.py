# coding=utf-8
from __future__ import absolute_import

import os
import base64
from subprocess import Popen
import psutil
from time import sleep
import requests
from threading import Thread
from glob import glob
from serial import Serial, SerialException
import flask
import octoprint.plugin
import shutil
from octoprint.events import eventManager, Events
from octoprint.server.util.flask import restricted_access
from octoprint.server import admin_permission, VERSION

Events.FIRMWARE_UPDATE = "FirmwareUpdate"

__author__ = "Allen McAfee (allen@robo3d.com)"
__license__ = ("GNU Affero General Public License "
               "http://www.gnu.org/licenses/agpl.html")
__copyright__ = ("Copyright (C) 2016 Robo 3D, Inc. "
                 "Released under terms of the AGPLv3 License")


class FirmwareUpdatePlugin(octoprint.plugin.StartupPlugin,
                           octoprint.plugin.TemplatePlugin,
                           octoprint.plugin.AssetPlugin,
                           octoprint.plugin.SettingsPlugin,
                           octoprint.plugin.SimpleApiPlugin,
                           octoprint.plugin.BlueprintPlugin):

    def __init__(self):
        # State to keep track if an update is in progress
        self.isUpdating = False
        # Location of the hex file
        self.firmware_file = None
        # Name of a local file if detected
        self.local_file_name = None
        # Location of the version file
        self.version_file = os.path.expanduser('~/Marlin/.version')
        # PID of the update process (avrdude) so we can kill if timeout
        self.updatePID = None
        # Update build log
        self.build_log = None
        # How long it took to complete the update
        self.completion_time = 0
        # Write time and read time variables to be added together
        self.write_time = None
        self.read_time = None
        # 'Autodetected' port that avrdude will flash to
        self.port = None
        # Version to compare against latest Marlin release on GitHub
        self.version = None
        # Update process Popen object
        self.process = None
        # Directories where firmware lives
        self.firmware_directory = os.path.expanduser(
            '~/Marlin/.build/mega2560/')
        self.src_directory = os.path.expanduser('~/Marlin/src')
        # Variable that defines if the update was started on startup
        self.updating_on_startup = False

    # Allow other OctoPrint plugins to get firmware updating status
    def _is_updating(self):
        return self.isUpdating
        
    # Set default plugin settings for OctoPrint
    def get_settings_defaults(self):
        return dict(
            auto_update=True
        )

    def get_assets(self):
        return {
            "js": ["js/firmwareupdate.js",
                   "js/knockout-file-bindings.js"],
            "css": ["css/style.css",
                    "css/knockout-file-bindings.css"]
        }

    def get_api_commands(self):
        return dict(
            update_firmware=[],
            toggle_auto_update=[]
        )

    def on_api_command(self, command, data):
        if command == "update_firmware":
            self._start_update()
        elif command == "toggle_auto_update":
            if data['current']:
                auto_update = False
            else:
                auto_update = True
            self._settings.set_boolean(["auto_update"], auto_update)
            self._settings.save()
            eventManager().fire(Events.SETTINGS_UPDATED)
        else:
            self._logger.info("Unknown command: " + command)

    def on_api_get(self, request):
        return flask.jsonify(isUpdating=self.isUpdating)

    def on_after_startup(self):
        if self._settings.get_boolean(["auto_update"]):
            self._start_update(True)
        else:
            self._logger.info("Auto firmware update disabled, skipping...")

    # Creates endpoint located at /plugin/firmwareupdate/upload
    # Allows for custom firmware upload by accepting a base64-encoded string
    # Saves file to filesystem and begins the update process
    @octoprint.plugin.BlueprintPlugin.route("/upload", methods=["POST"])
    @restricted_access
    @admin_permission.require(403)
    def upload_file(self):
        if "base64String" not in flask.request.values:
            return flask.make_response("Expected a base64String value", 400)

        try:
            decode = base64.b64decode(flask.request.values['base64String'])
            self._check_directories()

            # Delete any firmware files that may exist when using
            # custom firmware
            self._delete_firmware_files()
            with open(os.path.join(self.firmware_directory,
                                   "firmware.hex"), "wb") as firmware:
                firmware.write(decode)
                firmware.close()
        except (TypeError, IOError) as e:
            error_text = "There was an issue saving the firmware file."
            self._logger.warn("Error saving firmware file: %s" % str(e))
            self._update_status(
                False, "error", error_text)
            return flask.make_response(error_text, 400)

        self._start_update()
        return flask.make_response("OK", 200)

    def _start_update(self, onstartup=False):
        # If by any chance the API command was called outside of Octoprint,
        # we want to make sure we don't cancel a print.
        if self.printer_is_printing():
            self._logger.warn("Firmware called but print in progress.")
        else:
            # Make sure printer is disconnected before continuing
            self._printer.disconnect()

            self._update_firmware_init_thread = Thread(
                target=self._update_firmware_init, args=(onstartup,))
            self._update_firmware_init_thread.daemon = True
            self._update_firmware_init_thread.start()

    # Loop that is constantly checking the build log for errors or success
    # messages
    def checkStatus(self):
        while True:
            with open(os.path.expanduser('~/Marlin/.build_log')) as f:
                update_result = f.read()
            if 'No device matching following was found' in update_result:
                self._logger.info("Failed update...")
                self._update_status(
                    False, "error", "A connected device was not found.")
                self._clean_up()
                break
            elif 'FAILED' in update_result:
                self._logger.info("Failed update...")
                self._update_status(False, "error")
                self._clean_up()
                break
            elif ('bytes of flash verified' in update_result and
                  'avrdude done' in update_result):
                self._logger.info("Successful update!")
                for line in update_result.splitlines():
                    if "Reading" in line:
                        self.read_time = self.find_between(line, " ", "s")
                        self.completion_time += float(self.read_time)
                    elif "Writing" in line:
                        self.write_time = self.find_between(line, " ", "s")
                        self.completion_time += float(self.write_time)

                self._update_status(False, "completed",
                                    round(self.completion_time, 2))
                self._clean_up()
                break
            elif 'ReceiveMessage(): timeout' in update_result:
                self._logger.info(
                    "Update timed out. Check if port is already in use!")
                self._update_status(
                    False, "error", "Device timed out. Please check that the "
                                    "port is not in use!")

                p = psutil.Process(self.updatePID)
                for child in p.children(recursive=True):
                    child.kill()
                    p.kill()
                self._clean_up()
                break
            else:
                # Catch all other potential errors. Here we want to check if
                # the firmware flash process is still running. If it's not,
                # emit an error.
                if self.process.poll() is not None:
                    self._logger.info("Failed update. Consult the build log")
                    self._update_status(
                        False, "error", "An unknown error occurred. Please "
                                        "consult the build log for more "
                                        "information.")
                    self._clean_up()
                    break
            sleep(1)

    # Initiation of firmware update which gathers information about current
    # release version and compares to present installation version
    def _update_firmware_init(self, onstartup=False):
        if self.printer_is_printing():
            self._update_status(False, "error", "Printer is in use.")
        else:
            self._check_directories()

            if onstartup:
                self.updating_on_startup = True
                self._delete_firmware_files()

                # Check against current version
                if not os.path.isfile(self.version_file):
                    self._logger.info(
                        "No version file exists, grabbing latest from GitHub")
                    self._update_status(True, "inprogress")

                    self._update_from_github()
                else:
                    with open(self.version_file, 'r') as f:
                        self.version = f.readline()

                    try:
                        r = requests.get(
                            "https://api.github.com/repos/Robo3D/"
                            "Marlin/releases/latest", timeout=27)
                    except (requests.exceptions.ConnectionError,
                            requests.exceptions.HTTPError,
                            requests.exceptions.Timeout) as e:
                        self.raise_connection_error(e)
                        return

                    rjson = r.json()
                    github_version = rjson['assets'][0]['updated_at']

                    if self.version == github_version:
                        self._logger.info("Skipping update process")
                        self.isUpdating = False
                    else:
                        self._logger.info(
                            "Version in file is different, grabbing from "
                            "GitHub")
                        self._update_status(True, "inprogress")

                        self._update_from_github()
            else:
                self.updating_on_startup = False
                self.local_file_name = self._check_for_firmware_file()
                if self.local_file_name is not None:
                    self._logger.info("Updating using " + self.local_file_name)
                    self._update_status(True, "inprogress")

                    self.firmware_file = os.path.join(os.path.expanduser(
                        '~/Marlin/.build/mega2560/'), self.local_file_name)

                    # Using something other than GitHub, delete version file
                    self._delete_version_file()

                    self._update_firmware("local")
                else:
                    self._logger.info(
                        "No files exist, grabbing latest from GitHub")
                    self._update_status(True, "inprogress")

                    self._update_from_github()

    # Checks if any firmware files exists; returns the first one in the list
    def _check_for_firmware_file(self):
        filenames = glob(os.path.join(self.firmware_directory, "*.hex"))
        if len(filenames) > 0:
            return os.path.basename(filenames[0])
        else:
            return None

    # Begin the update process from GitHub
    def _update_from_github(self):
        try:
            r = requests.get(
                'https://api.github.com/repos/Robo3D/Marlin/releases/latest',
                timeout=27)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout) as e:
            self.raise_connection_error(e)
            return

        rjson = r.json()
        self.firmware_file = os.path.join(
            self.firmware_directory, 'firmware.hex')
        # Write version to File
        with open(self.version_file, 'w') as f:
            f.write(rjson['assets'][0]['updated_at'])

        # Download the hex file from GitHub
        try:
            r = requests.get(rjson['assets'][0]['browser_download_url'],
                             stream=True, timeout=27)
            r.raise_for_status()
        except (requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout) as e:
            self.raise_connection_error(e)
            return

        with open(self.firmware_file, 'wb') as f:
            r.raw.decode_content = True
            try:
                shutil.copyfileobj(r.raw, f)
            except (shutil.Error, IOError) as e:
                self.raise_connection_error(e)
                return

        if os.path.isfile(self.firmware_file):
            self._logger.info("File downloaded, continuing...")
            self._update_firmware("github")
        else:
            self._update_status(
                False, "error", "Release firmware was not downloaded.")

    def _update_firmware(self, target):
        if not self.isUpdating:
            self._logger.info("Skipped initiation. Aborting...")
        else:
            self.completion_time = 0
            self.write_time = None
            self.read_time = None
            try:
                os.remove(os.path.expanduser('~/Marlin/.build_log'))
            except OSError:
                self._logger.info("Build log couldn't be deleted")

            self._update_firmware_thread = Thread(target=self._update_worker,
                                                  args=(target,))
            self._update_firmware_thread.daemon = True
            self._update_firmware_thread.start()

    # Worker process that actually controls the firmware process and writes
    # to the build log
    def _update_worker(self, target=None):
        self._logger.info("Updating now using: " + target)

        if target in ["github", None]:
            filename = "firmware.hex"
        else:
            filename = self.local_file_name

        try:
            self.port = glob('/dev/ttyACM*')[0]
        except IndexError:
            self._update_status(False, "error", "No ports exist.")
            self._clean_up()
            raise RuntimeError('No ports detected')

        self.build_log = open(os.path.expanduser('~/Marlin/.build_log'), "w")
        try:
            s = Serial(self.port, 115200)
        except SerialException as e:
            self._update_status(False, "error", str(e))
            self._clean_up()
            raise RuntimeError(str(e))

        # Pulse connection to ensure avrdude can make a connection
        s.setDTR(False)
        sleep(0.1)
        s.setDTR(True)
        s.close()
        self.process = Popen("cd ~/Marlin/; avrdude -p m2560 -P /dev/ttyACM0 "
                             "-c stk500v2 -b 250000 -D "
                             "-U flash:w:./.build/mega2560/%s:i" % filename,
                             stdout=self.build_log,
                             stderr=self.build_log,
                             shell=True,
                             preexec_fn=os.setsid)
        self.updatePID = self.process.pid
        self.checkStatus()

    def find_between(self, s, first, last):
        try:
            start = s.rindex(first) + len(first)
            end = s.rindex(last, start)
            return s[start:end]
        except ValueError:
            return ""

    # Function to distribute the state of updating to OctoPrint's front-end
    # and to printer_ui in the form of an OctoPrint event
    def _update_status(self, isUpdating, status=None, message=None):
        self.isUpdating = isUpdating
        # Reconnect again after no longer updating
        if not self.isUpdating:
            self._printer.connect()
            if status == "error":
                self._delete_version_file()

        self._plugin_manager.send_plugin_message(self._identifier, dict(
            isUpdating=self.isUpdating, status=status, message=message,
            onStartup=self.updating_on_startup))
        payload = {'isUpdating': self.isUpdating,
                   'status': status, 'message': message,
                   'onStartup': self.updating_on_startup}
        eventManager().fire(Events.FIRMWARE_UPDATE, payload)

    # Remove the build log and firmware file, if there is one
    def _clean_up(self):
        if self.build_log is not None:
            if not self.build_log.closed:
                self.build_log.close()
        try:
            os.remove(self.firmware_file)
        except OSError:
            self._logger.info("Firmware file could not be deleted")

    # Create firmware directories, if they don't exist
    def _check_directories(self):
        if not os.path.exists(self.firmware_directory):
            os.makedirs(self.firmware_directory)
        if not os.path.exists(self.src_directory):
            os.makedirs(self.src_directory)

    # Delete all files inside firmware_directory
    def _delete_firmware_files(self):
        self._logger.info("Wiping firmware directory...")
        filelist = glob(os.path.join(self.firmware_directory, "*.hex"))
        for f in filelist:
            try:
                os.remove(f)
            except OSError:
                self._logger.info("Firmware file could not be deleted")

    def _delete_version_file(self):
        if os.path.isfile(self.version_file):
            self._logger.info("Removing version file")
            try:
                os.remove(self.version_file)
            except OSError:
                self._logger.warn("Error removing version file")

    def raise_connection_error(self, e):
        self._logger.info(e)
        self._update_status(
            False, "error", "Connection error encountered")

    def printer_is_printing(self):
        if self._printer.is_printing() or self._printer.is_paused():
            return True
        return False

    def get_template_configs(self):
        return [
            dict(type="settings", name="Firmware Update",
                 data_bind="visible: loginState.isAdmin()"),
        ]

    def increase_upload_bodysize(self, current_max_body_sizes, *args,
                                 **kwargs):
        # set a maximum body size of 100 MB for plugin archive uploads
        return [("POST", r"/upload", 100 * 1024 * 1024)]

__plugin_name__ = "Firmware Update Plugin"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = FirmwareUpdatePlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.server.http.bodysize":
            __plugin_implementation__.increase_upload_bodysize
    }

    global __plugin_helpers__

    __plugin_helpers__ = dict(
        firmware_updating = __plugin_implementation__._is_updating
    )
