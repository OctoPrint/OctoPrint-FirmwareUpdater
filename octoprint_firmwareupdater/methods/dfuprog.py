import re
import os
import sarge

DFUPROG_ERASING = "Erasing flash"
DFUPROG_WRITING = "Programming"
DFUPROG_VERIFYING = "Reading"
DFUPROG_VALIDATING = "Validating"
DFUPROG_NODEVICE = "no device present"

def _check_dfuprog(self):
    dfuprog_path = self.get_profile_setting("dfuprog_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(dfuprog_path):
        self._logger.error(u"Path to dfu-programmer is not valid: {path}".format(path=dfuprog_path))
        return False
    elif dfuprog_path is None:
        self._logger.error(u"Path to dfu-programmer is not set.")
        return False
    if not os.path.exists(dfuprog_path):
        self._logger.error(u"Path to dfu-programmer does not exist: {path}".format(path=dfuprog_path))
        return False
    elif not os.path.isfile(dfuprog_path):
        self._logger.error(u"Path to dfu-programmer is not a file: {path}".format(path=dfuprog_path))
        return False
    elif not os.access(dfuprog_path, os.X_OK):
        self._logger.error(u"Path to dfu-programmer is not executable: {path}".format(path=dfuprog_path))
        return False
    else:
        return True

def _flash_dfuprog(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)

    if not _erase_dfuprog(self):
        return False

    dfuprog_path = self.get_profile_setting("dfuprog_path")
    dfuprog_avrmcu = self.get_profile_setting("dfuprog_avrmcu")
    working_dir = os.path.dirname(dfuprog_path)

    dfuprog_command = self.get_profile_setting("dfuprog_commandline")
    dfuprog_command = dfuprog_command.replace("{dfuprogrammer}", dfuprog_path)
    dfuprog_command = dfuprog_command.replace("{mcu}", dfuprog_avrmcu)
    dfuprog_command = dfuprog_command.replace("{firmware}", firmware)

    import sarge
    self._logger.info(u"Running '{}' in {}".format(dfuprog_command, working_dir))
    self._send_status("progress", subtype="writing")
    self._console_logger.info(dfuprog_command)
    try:
        p = sarge.run(dfuprog_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stderr.read(timeout=0.5).decode('utf-8')
            if not output:
                p.commands[0].poll()
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if DFUPROG_WRITING in line:
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")
                if DFUPROG_VERIFYING in line:
                    self._logger.info(u"Verifying memory...")
                    self._send_status("progress", subtype="verifying")
                elif DFUPROG_NODEVICE in line:
                    raise FlashException("No device found")

        if p.returncode == 0:
            return True
        else:
            raise FlashException("dfu-programmer returned code {returncode}".format(returncode=p.returncode))

    except FlashException as ex:
        self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
        self._send_status("flasherror", message=ex.reason)
        return False
    except:
        self._logger.exception(u"Flashing failed. Unexpected error.")
        self._send_status("flasherror")
        return False

def _erase_dfuprog(self):
    dfuprog_path = self.get_profile_setting("dfuprog_path")
    dfuprog_avrmcu = self.get_profile_setting("dfuprog_avrmcu")

    working_dir = os.path.dirname(dfuprog_path)

    dfuprog_erasecommand = self.get_profile_setting("dfuprog_erasecommandline")
    dfuprog_erasecommand = dfuprog_erasecommand.replace("{dfuprogrammer}", dfuprog_path)
    dfuprog_erasecommand = dfuprog_erasecommand.replace("{mcu}", dfuprog_avrmcu)

    import sarge
    self._logger.info(u"Running '{}' in {}".format(dfuprog_erasecommand, working_dir))
    self._console_logger.info(dfuprog_erasecommand)
    try:
        p = sarge.run(dfuprog_erasecommand, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stderr.read(timeout=0.5).decode('utf-8')
            if not output:
                p.commands[0].poll()
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if DFUPROG_ERASING in line:
                    self._logger.info(u"Erasing memory...")
                    self._send_status("progress", subtype="erasing")
                elif DFUPROG_NODEVICE in line:
                    raise FlashException("No device found")

        if p.returncode == 0:
            return True
        else:
            raise FlashException("dfu-programmer returned code {returncode}".format(returncode=p.returncode))

    except FlashException as ex:
        self._logger.error(u"Erasing failed. {error}.".format(error=ex.reason))
        self._send_status("flasherror", message=ex.reason)
        return False
    except:
        self._logger.exception(u"Erasing failed. Unexpected error.")
        self._send_status("flasherror")
        return False

class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason
