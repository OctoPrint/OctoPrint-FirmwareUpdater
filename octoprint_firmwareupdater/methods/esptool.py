import re
import os
import sarge
import time
import serial
from serial import SerialException

ESPTOOL_CONNECTING = "Connecting"
ESPTOOL_WRITING = "Writing at"
ESPTOOL_RESETTING = "resetting"
ESPTOOL_NODATA = "No serial data received"
ESPTOOL_NOBOARD = "Could not open"
ESPTOOL_WRONGCHIP = "Wrong --chip argument?"
ESPTOOL_WRONGMODE = "Wrong boot mode detected"
ESPTOOL_ERROR = "esptool: error:"
ESPTOOL_BADARG = "argument"

def _check_esptool(self):
    esptool_path = self.get_profile_setting("esptool_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(esptool_path):
        self._logger.error(u"Path to esptool is not valid: {path}".format(path=esptool_path))
        return False
    elif esptool_path is None:
        self._logger.error(u"Path to esptool is not set.")
        return False
    if not os.path.exists(esptool_path):
        self._logger.error(u"Path to esptool does not exist: {path}".format(path=esptool_path))
        return False
    elif not os.path.isfile(esptool_path):
        self._logger.error(u"Path to esptool is not a file: {path}".format(path=esptool_path))
        return False
    elif not os.access(esptool_path, os.X_OK):
        self._logger.error(u"Path to esptool is not executable: {path}".format(path=esptool_path))
        return False
    else:
        return True

def _flash_esptool(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)
    assert(printer_port is not None)

    esptool_path = self.get_profile_setting("esptool_path")
    esptool_chip = self.get_profile_setting("esptool_chip")
    esptool_address = self.get_profile_setting("esptool_address")
    esptool_baudrate = self.get_profile_setting("esptool_baudrate")

    working_dir = os.path.dirname(esptool_path)

    esptool_command = self.get_profile_setting("esptool_commandline")
    esptool_command = esptool_command.replace("{esptool}", esptool_path)
    esptool_command = esptool_command.replace("{port}", printer_port)
    esptool_command = esptool_command.replace("{chip}", esptool_chip.lower())
    esptool_command = esptool_command.replace("{address}", esptool_address)
    esptool_command = esptool_command.replace("{baud}", str(esptool_baudrate))
    esptool_command = esptool_command.replace("{firmware}", firmware)

    self._logger.info(u"Running '{}' in {}".format(esptool_command, working_dir))
    self._console_logger.info(u"")
    self._console_logger.info(esptool_command)
    try:
        p = sarge.run(esptool_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stdout.read(timeout=0.1).decode('utf-8')
            if not output:
                p.commands[0].poll()
                continue
            
            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if ESPTOOL_CONNECTING in line:
                    self._logger.info(u"Connecting...")
                    self._send_status("progress", subtype="connecting")
                elif ESPTOOL_WRITING in line:
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")
                elif ESPTOOL_RESETTING in line:
                    self._logger.info(u"Resetting...")
                    self._send_status("progress", subtype="boardreset")
                elif ESPTOOL_NODATA in line:
                    raise FlashException("No serial data received.")
                elif ESPTOOL_NOBOARD in line:
                    raise FlashException("Could not open the port.")
                elif ESPTOOL_WRONGCHIP in line:
                    message = "Incompatible ESP chip specified."
                    try:
                        message = message + u" {}.".format(re.split(r"[\:\.]", line)[1].strip())
                    except:
                        self._logger.info(u"Could not parse chip error")
                    raise FlashException(message)
                elif ESPTOOL_WRONGMODE in line:
                    raise FlashException("Wrong boot mode detected. The chip needs to be in download mode.")

        if p.returncode == 0:
            time.sleep(1)
            return True
        else:
            output = p.stderr.read(timeout=0.1).decode('utf-8')
            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if ESPTOOL_ERROR in line and ESPTOOL_BADARG in line:
                    raise FlashException(u"Unrecognized or invalid Esptool argument(s).\n\n{}".format(line))
                elif ESPTOOL_ERROR in line:
                    errline = line

            if errline:
                raise FlashException("Esptool returned code {returncode}.\n{error}".format(returncode=p.returncode, error=errline))
            else:
                raise FlashException("Esptool returned code {returncode}.".format(returncode=p.returncode))

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
