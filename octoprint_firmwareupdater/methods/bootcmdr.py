import re
import os
import sarge
import time

ERASING = "Erasing flash"
WRITING = "Programming"
VERIFYING = "Reading"
VALIDATING = "Validating"
NODEVICE = "no device present"
LOADING = "Loading firmware data from file"
CONNECTING = "Connecting to target bootloader"
BACKDOOR = "Attempting backdoor entry"

def _check_bootcmdr(self):
    bootcmdr_path = self.get_profile_setting("bootcmdr_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(bootcmdr_path):
        self._logger.error(u"Path to BootCommander is not valid: {path}".format(path=bootcmdr_path))
        return False
    elif bootcmdr_path is None:
        self._logger.error(u"Path to BootCommander is not set.")
        return False
    if not os.path.exists(bootcmdr_path):
        self._logger.error(u"Path to BootCommander does not exist: {path}".format(path=bootcmdr_path))
        return False
    elif not os.path.isfile(bootcmdr_path):
        self._logger.error(u"Path to BootCommander is not a file: {path}".format(path=bootcmdr_path))
        return False
    elif not os.access(bootcmdr_path, os.X_OK):
        self._logger.error(u"Path to BootCommander is not executable: {path}".format(path=bootcmdr_path))
        return False
    else:
        return True

def _flash_bootcmdr(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)

    bootcmdr_path = self.get_profile_setting("bootcmdr_path")
    bootcmdr_baudrate = self.get_profile_setting("bootcmdr_baudrate")
    bootcmdr_command_timeout = self.get_profile_setting("bootcmdr_command_timeout")
    if not bootcmdr_command_timeout or bootcmdr_command_timeout < 10 or bootcmdr_command_timeout > 90:
        self._logger.warn(u"BootCommander command timeout '{}' is invalid. Defaulting to 30s.".format(bootcmdr_command_timeout))
        self.set_profile_setting_int("bootcmdr_command_timeout", 30)
        self._settings.save()
        bootcmdr_command_timeout = 30

    working_dir = os.path.dirname(bootcmdr_path)

    bootcmdr_command = self.get_profile_setting("bootcmdr_commandline")
    bootcmdr_command = bootcmdr_command.replace("{bootcommander}", bootcmdr_path)
    bootcmdr_command = bootcmdr_command.replace("{port}", printer_port)
    bootcmdr_command = bootcmdr_command.replace("{baudrate}", str(bootcmdr_baudrate))
    bootcmdr_command = bootcmdr_command.replace("{firmware}", firmware)

    self._logger.info(u"Running '{}' in {}".format(bootcmdr_command, working_dir))
    self._send_status("progress", subtype="writing")
    self._console_logger.info(bootcmdr_command)
    try:
        starttime = time.time()
        connecting = False
        p = sarge.run(bootcmdr_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stdout.read(timeout=0.1).decode('utf-8')
            if not output:
                p.commands[0].poll()
                if (time.time() > (starttime + bootcmdr_command_timeout)):
                    self._logger.error(u"Timeout waiting for command to complete")
                    p.commands[0].kill()
                    if connecting:
                        raise FlashException("Connection timeout")
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if WRITING in line:
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")
                if CONNECTING in line:
                    connecting = True
                    self._logger.info(u"Connecting to bootloader...")
                    self._send_status("progress", subtype="connecting")
                if BACKDOOR in line:
                    connecting = True
                    self._logger.info(u"Connecting to backdoor...")
                    self._send_status("progress", subtype="backdoor")
                elif NODEVICE in line:
                    raise FlashException("No device found")

        if p.returncode == 0:
            return True
        else:
            raise FlashException("BootCommander returned code {returncode}".format(returncode=p.returncode))

    except FlashException as ex:
        self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
        self._send_status("flasherror", message=ex.reason)
        return False
    except:
        self._logger.exception(u"Flashing failed. Unexpected error.")
        self._send_status("flasherror")
        return False

class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason
