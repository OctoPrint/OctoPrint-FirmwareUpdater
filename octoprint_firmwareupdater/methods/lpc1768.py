import datetime
import re
import os
import time
import shutil
import subprocess
import sys

def _check_lpc1768(self):
    lpc1768_path = self.get_profile_setting("lpc1768_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(lpc1768_path):
        self._logger.error(u"Firmware folder path is not valid: {path}".format(path=lpc1768_path))
        return False
    elif lpc1768_path is None:
        self._logger.error(u"Firmware folder path is not set.")
        return False
    if not os.path.exists(lpc1768_path):
        self._logger.error(u"Firmware folder path does not exist: {path}".format(path=lpc1768_path))
        return False
    elif not os.path.isdir(lpc1768_path):
        self._logger.error(u"Firmware folder path is not a folder: {path}".format(path=lpc1768_path))
        return False
    else:
        return True

def _flash_lpc1768(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)
    assert(printer_port is not None)

    no_m997_reset_wait = self.get_profile_setting_boolean("lpc1768_no_m997_reset_wait")
    lpc1768_path = self.get_profile_setting("lpc1768_path")
    timestamp_filenames = self.get_profile_setting_boolean("lpc1768_timestamp_filenames")
    use_custom_filename = self.get_profile_setting_boolean("lpc1768_use_custom_filename")
    custom_filename = self.get_profile_setting("lpc1768_custom_filename").strip()

    if self.get_profile_setting_boolean("lpc1768_preflashreset"):
        self._send_status("progress", subtype="boardreset")

        # Sync the filesystem to flush writes
        self._logger.info(u"Synchronizing cached writes to SD card")
        try:
            r = os.system('sync')
        except:
            e = sys.exc_info()[0]
            self._logger.error("Error executing 'sync' command")
            return False
        time.sleep(1)

        if os.access(lpc1768_path, os.W_OK):
            unmount_command = self.get_profile_setting("lpc1768_unmount_command")
            if unmount_command:
                unmount_command = unmount_command.replace("{mountpoint}", lpc1768_path)

                self._logger.info(u"Unmounting SD card: '{}'".format(unmount_command))
                try:
                    p = subprocess.Popen(unmount_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
                    out, err = p.communicate()
                    r = p.returncode

                except:
                    e = sys.exc_info()[0]
                    self._logger.error("Error executing unmount command '{}'".format(unmount_command))
                    self._logger.error("{}".format(str(e)))
                    self._send_status("flasherror", message="Unable to unmount SD card")
                    return False

                if r != 0:
                    if err.strip().endswith("not mounted."):
                        self._logger.info("{}".format(err.strip()))
                    else:
                        self._logger.error("Error executing unmount command '{}'".format(unmount_command))
                        self._logger.error("{}".format(err.strip()))
                        self._send_status("flasherror", message="Unable to unmount SD card")
                        return False
        else:
            self._logger.info(u"SD card not mounted, skipping unmount")

        self._logger.info(u"Pre-flash reset: attempting to reset the board")
        if not _reset_lpc1768(self, printer_port):
            self._logger.error(u"Reset failed")
            return False

    # Release the SD card
    if not _unmount_sd(self, printer_port):
        self._send_status("flasherror", message="Unable to unmount SD card")
        return False

    # loop until the mount is available; timeout after 60s
    count = 1
    timeout = 60
    interval = 1
    sdstarttime = time.time()
    self._logger.info(u"Waiting for SD card to be available at '{}'".format(lpc1768_path))
    self._send_status("progress", subtype="waitforsd")
    while (time.time() < (sdstarttime + timeout) and not os.access(lpc1768_path, os.W_OK)):
        self._logger.debug(u"Waiting for firmware folder path to become available [{}/{}]".format(count, int(timeout / interval)))
        count = count + 1
        time.sleep(interval)

    if not os.access(lpc1768_path, os.W_OK):
        self._send_status("flasherror", message="Unable to access firmware folder")
        self._logger.error(u"Firmware folder path is not writeable: {path}".format(path=lpc1768_path))
        return False

    self._logger.info(u"Firmware update folder '{}' available for writing after {} seconds".format(lpc1768_path, round((time.time() - sdstarttime),0)))

    # Try to delete the last-flashed file
    last_filename = self.get_profile_setting("lpc1768_last_filename")
    if timestamp_filenames and last_filename is not None:
        last_path = lpc1768_path + '/' + last_filename
        self._logger.info(u"Attempting to delete previous firmware file {}".format(last_path))
        if os.path.isfile(last_path):
            try:
                os.remove(last_path)
            except:
                self._logger.warn(u"Unable to delete {}".format(last_path))
        else:
            self._logger.info(u"{} does not exist".format(last_path))

    # Copy the new firmware file
    if timestamp_filenames:
        target = datetime.datetime.now().strftime("fw%H%M%S.bin")
    elif use_custom_filename and custom_filename is not None:
        target = custom_filename
    else:
        target = "firmware.bin"

    target_path = lpc1768_path + '/' + target
    self._logger.info(u"Copying firmware to update folder '{}' -> '{}'".format(firmware, target_path))
    self._send_status("progress", subtype="copying")

    try:
        shutil.copyfile(firmware, target_path)
    except:
        self._logger.exception(u"Flashing failed. Unable to copy file.")
        self._send_status("flasherror", message="Unable to copy firmware file to firmware folder")
        return False

    # Save the filename
    if timestamp_filenames:
        self.set_profile_setting("lpc1768_last_filename", target)

    self._send_status("progress", subtype="unmounting")

    # Sync the filesystem to flush writes
    self._logger.info(u"Synchronizing cached writes to SD card")
    try:
        r = os.system('sync')
    except:
        e = sys.exc_info()[0]
        self._logger.error("Error executing 'sync' command")
        return False
    time.sleep(1)

    unmount_command = self.get_profile_setting("lpc1768_unmount_command")
    if unmount_command:
        unmount_command = unmount_command.replace("{mountpoint}", lpc1768_path)

        self._logger.info(u"Unmounting SD card: '{}'".format(unmount_command))
        try:
            p = subprocess.Popen(unmount_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            out, err = p.communicate()
            r = p.returncode

        except:
            e = sys.exc_info()[0]
            self._logger.error("Error executing unmount command '{}'".format(unmount_command))
            self._logger.error("{}".format(str(e)))
            self._send_status("flasherror", message="Unable to unmount SD card")
            return False

        if r != 0:
            if err.strip().endswith("not mounted."):
                self._logger.info("{}".format(err.strip()))
            else:
                self._logger.error("Error executing unmount command '{}'".format(unmount_command))
                self._logger.error("{}".format(err.strip()))
                self._send_status("flasherror", message="Unable to unmount SD card")
                return False

    self._send_status("progress", subtype="boardreset")
    self._logger.info(u"Firmware update reset: attempting to reset the board")
    if not _reset_lpc1768(self, printer_port, no_m997_reset_wait):
        self._logger.error(u"Reset failed")
        return False

    return True

def _reset_lpc1768(self, printer_port=None, no_reset_wait=False):
    assert(printer_port is not None)
    no_m997_restart_wait = self.get_profile_setting_boolean("lpc1768_no_m997_restart_wait")
    self._logger.info(u"Resetting LPC1768 at '{port}'".format(port=printer_port))

    # Configure the port
    try:
        os.system('stty -F ' + printer_port + ' speed 115200 -echo > /dev/null')
    except:
        self._logger.exception(u"Error configuring serial port.")
        self._send_status("flasherror", message="Board reset failed")
        return False

    # Smoothie reset command
    try:
        os.system('echo reset >> ' + printer_port)
    except:
        self._logger.exception(u"Error sending Smoothie 'reset' command.")
        self._send_status("flasherror", message="Board reset failed")
        return False

    # Marlin reset command
    try:
        os.system('echo M997 >> ' + printer_port)
    except:
        self._logger.exception(u"Error sending Marlin 'M997' command.")
        self._send_status("flasherror", message="Board reset failed")
        return False

    if no_reset_wait:
        # Give the board time to reset so that OctoPrint does not try to reconnect before the reset
        time.sleep(1)
        self._logger.info(u"Not waiting for reset")
        return True
    else:
        if _wait_for_lpc1768(self, printer_port, no_m997_restart_wait):
            return True
        else:
            self._logger.error(u"Board reset failed")
            self._send_status("flasherror", message="Board reset failed")
            return False

def _wait_for_lpc1768(self, printer_port=None, no_restart_wait=False):
    assert(printer_port is not None)
    self._logger.info(u"Waiting for LPC1768 at '{port}' to reset".format(port=printer_port))

    check_command = 'ls ' + printer_port + ' > /dev/null 2>&1'
    start = time.time()
    timeout = 10
    interval = 0.2
    count = 1
    connected = True

    loopstarttime = time.time()

    while (time.time() < (loopstarttime + timeout) and connected):
        self._logger.debug(u"Waiting for reset to init [{}/{}]".format(count, int(timeout / interval)))
        count = count + 1

        if not os.system(check_command):
            connected = True
            time.sleep(interval)

        else:
            time.sleep(interval)
            connected = False

    if connected:
        self._logger.error(u"Timeout waiting for board reset to init")
        return False

    self._logger.info(u"LPC1768 at '{port}' is resetting".format(port=printer_port))

    if no_restart_wait:
        self._logger.info(u"Not waiting for restart to complete")
        return True
    else:
        time.sleep(3)

        timeout = 20
        interval = 0.2
        count = 1
        connected = False
        loopstarttime = time.time()

        while (time.time() < (loopstarttime + timeout) and not connected):
            self._logger.debug(u"Waiting for reset to complete [{}/{}]".format(count, int(timeout / interval)))
            count = count + 1

            if not os.system(check_command):
                connected = True
                time.sleep(interval)

            else:
                time.sleep(interval)
                connected = False

        if not connected:
            self._logger.error(u"Timeout waiting for board reset to complete")
            return False

        end = time.time()
        self._logger.info(u"LPC1768 at '{port}' reset in {duration} seconds".format(port=printer_port, duration=(round((end - start),2))))
        return True

def _unmount_sd(self, printer_port=None):
    assert(printer_port is not None)
    self._logger.info(u"Release the firmware lock on the SD Card by sending 'M22' to '{port}'".format(port=printer_port))

    try:
        os.system('stty -F ' + printer_port + ' speed 115200 -echo > /dev/null')
    except:
        self._logger.exception(u"Error configuring serial port.")
        self._send_status("flasherror", message="Card unmount failed")
        return False

    try:
        os.system('echo M22 >> ' + printer_port)
    except:
        self._logger.exception(u"Error sending 'M22' command.")
        self._send_status("flasherror", message="Card unmount failed")
        return False

    time.sleep(2)
    return True
