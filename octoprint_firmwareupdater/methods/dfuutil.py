import re
import os
import sarge

DFUUTIL_ERASING = "Erase"
DFUUTIL_WRITING = "Downloading"
DFUUTIL_NOACCESS = "Cannot open DFU device"
DFUUTIL_NODEVICE = "No DFU capable USB device available"

def _check_dfuutil(self):
    dfuutil_path = self.get_profile_setting("dfuutil_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(dfuutil_path):
        self._logger.error(u"Path to dfu-util is not valid: {path}".format(path=dfuutil_path))
        return False
    elif dfuutil_path is None:
        self._logger.error(u"Path to dfu-util is not set.")
        return False
    if not os.path.exists(dfuutil_path):
        self._logger.error(u"Path to dfu-util does not exist: {path}".format(path=dfuutil_path))
        return False
    elif not os.path.isfile(dfuutil_path):
        self._logger.error(u"Path to dfu-util is not a file: {path}".format(path=dfuutil_path))
        return False
    elif not os.access(dfuutil_path, os.X_OK):
        self._logger.error(u"Path to dfu-util is not executable: {path}".format(path=dfuutil_path))
        return False
    else:
        return True

def _flash_dfuutil(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)

    dfuutil_path = self.get_profile_setting("dfuutil_path")
    working_dir = os.path.dirname(dfuutil_path)

    dfuutil_command = self.get_profile_setting("dfuutil_commandline")
    dfuutil_command = dfuutil_command.replace("{dfuutil}", dfuutil_path)
    dfuutil_command = dfuutil_command.replace("{firmware}", firmware)

    import sarge
    self._logger.info(u"Running '{}' in {}".format(dfuutil_command, working_dir))
    self._console_logger.info(dfuutil_command)
    try:
        p = sarge.run(dfuutil_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stdout.read(timeout=0.2).decode('utf-8')
            error = p.stderr.read(timeout=0.2).decode('utf-8')

            if not output and not error:
                p.commands[0].poll()
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if DFUUTIL_ERASING in line:
                    self._logger.info(u"Erasing memory...")
                    self._send_status("progress", subtype="erasing")
                elif DFUUTIL_WRITING in line:
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")

            for line in error.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))
                
                if DFUUTIL_NOACCESS in line:
                    raise FlashException("Cannot access DFU device")
                elif DFUUTIL_NODEVICE in line:
                    raise FlashException("No DFU device found")

        if p.returncode == 0:
            return True
        else:
            raise FlashException("dfu-util returned code {returncode}".format(returncode=p.returncode))

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
