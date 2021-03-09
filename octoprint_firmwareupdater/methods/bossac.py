import re
import os
import sarge
import time
import serial
from serial import SerialException

BOSSAC_ERASING = "Erase flash"
BOSSAC_WRITING = "bytes to flash"
BOSSAC_VERIFYING = "bytes of flash"
BOSSAC_NODEVICE = "No device found on"
BOSSAC_ERROR_VERIFICATION = "verification error"

def _check_bossac(self):
    bossac_path = self.get_profile_setting("bossac_path")
    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(bossac_path):
        self._logger.error(u"Path to bossac is not valid: {path}".format(path=bossac_path))
        return False
    elif bossac_path is None:
        self._logger.error(u"Path to bossac is not set.")
        return False
    if not os.path.exists(bossac_path):
        self._logger.error(u"Path to bossac does not exist: {path}".format(path=bossac_path))
        return False
    elif not os.path.isfile(bossac_path):
        self._logger.error(u"Path to bossac is not a file: {path}".format(path=bossac_path))
        return False
    elif not os.access(bossac_path, os.X_OK):
        self._logger.error(u"Path to bossac is not executable: {path}".format(path=bossac_path))
        return False
    else:
        return True

def _flash_bossac(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)
    assert(printer_port is not None)

    bossac_path = self.get_profile_setting("bossac_path")
    bossac_disableverify = self.get_profile_setting_boolean("bossac_disableverify")

    working_dir = os.path.dirname(bossac_path)

    bossac_command = self.get_profile_setting("bossac_commandline")
    bossac_command = bossac_command.replace("{bossac}", bossac_path)
    bossac_command = bossac_command.replace("{port}", printer_port)
    bossac_command = bossac_command.replace("{firmware}", firmware)

    if bossac_disableverify:
        bossac_command = bossac_command.replace(" {disableverify} ", " ")
    else:
        bossac_command = bossac_command.replace(" {disableverify} ", " -v ")

    self._logger.info(u"Attempting to reset the board to SAM-BA")
    self._send_status("progress", subtype="samreset")
    if not _reset_1200(self, printer_port):
        self._logger.error(u"Reset failed")
        return False

    self._logger.info(u"Running '{}' in {}".format(bossac_command, working_dir))
    self._console_logger.info(u"")
    self._console_logger.info(bossac_command)
    try:
        p = sarge.run(bossac_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
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

                if BOSSAC_ERASING in line:
                    self._logger.info(u"Erasing memory...")
                    self._send_status("progress", subtype="erasing")
                elif BOSSAC_WRITING in line:
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")
                elif BOSSAC_VERIFYING in line:
                    self._logger.info(u"Verifying memory...")
                    self._send_status("progress", subtype="verifying")
                elif BOSSAC_ERROR_VERIFICATION in line:
                    raise FlashException("Error verifying flash")

        if p.returncode == 0:
            time.sleep(1)
            return True
        else:
            output = p.stderr.read(timeout=0.5).decode('utf-8')
            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

                if BOSSAC_NODEVICE in line:
                    raise FlashException(line)

            raise FlashException("bossac returned code {returncode}".format(returncode=p.returncode))

    except FlashException as ex:
        self._logger.error(u"Flashing failed. {error}.".format(error=ex.reason))
        self._send_status("flasherror", message=ex.reason)
        return False
    except:
        self._logger.exception(u"Flashing failed. Unexpected error.")
        self._send_status("flasherror")
        return False

def _reset_1200(self, printer_port=None):
    assert(printer_port is not None)
    self._logger.info(u"Toggling '{port}' at 1200bps".format(port=printer_port))
    try:
        ser = serial.Serial(port=printer_port, \
                            baudrate=1200, \
                            parity=serial.PARITY_NONE, \
                            stopbits=serial.STOPBITS_ONE , \
                            bytesize=serial.EIGHTBITS, \
                            timeout=2000)
        time.sleep(1)
        ser.close()
        time.sleep(3)
    except SerialException as ex:
        self._logger.exception(u"Board reset failed: {error}".format(error=str(ex)))
        self._send_status("flasherror", message="Board reset failed")
        return False

    return True

class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason
