import re
import os
import sarge
import serial
import time

CONNECTING = "Connecting to target bootloader"
ERASING = "Erasing"
WRITING = "Programming"
FINISHING = "Finishing"
LOADING = "Loading firmware data from file"
BACKDOOR = "Attempting backdoor entry"

current_baudrate = None

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
    elif not self._printer.is_operational():
        self._logger.error("Printer is not connected")
        self._send_status("flasherror", subtype="notconnected")
        return False
    else:
        global current_baudrate
        _, current_port, current_baudrate, current_profile = self._printer.get_current_connection()
        return True

def _flash_bootcmdr(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)
    assert(printer_port is not None)
    assert(current_baudrate is not None)

    bootcmdr_path = self.get_profile_setting("bootcmdr_path")
    bootcmdr_baudrate = self.get_profile_setting("bootcmdr_baudrate")
    bootcmdr_command_timeout = self.get_profile_setting("bootcmdr_command_timeout")
    if not bootcmdr_command_timeout or bootcmdr_command_timeout < 10 or bootcmdr_command_timeout > 180:
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
    self._console_logger.info(bootcmdr_command)

    try:
        starttime = time.time()
        connecting = False
        reset = False
        p = sarge.run(bootcmdr_command, cwd=working_dir, async_=True, stdout=sarge.Capture(buffer_size=1), stderr=sarge.Capture(buffer_size=1))
        p.wait_events()

        while p.returncode is None:
            output = p.stdout.read(timeout=0.02).decode('utf-8')
            if not output:
                p.commands[0].poll()
                if (connecting and time.time() > (starttime + bootcmdr_command_timeout)):
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
                    connecting = False
                    reset = False
                    self._logger.info(u"Writing memory...")
                    self._send_status("progress", subtype="writing")
                if CONNECTING in line:
                    connecting = True
                    reset = False
                    self._logger.info(u"Connecting to bootloader...")
                    self._send_status("progress", subtype="connecting")
                if BACKDOOR in line:
                    connecting = True
                    reset = True
                    self._logger.info(u"Connecting to backdoor...")
                    self._send_status("progress", subtype="backdoor")
                if ERASING in line:
                    connecting = False
                    reset = False
                    self._logger.info(u"Erasing memory...")
                    self._send_status("progress", subtype="erasing")
                if FINISHING in line:
                    connecting = False
                    reset = False
                    self._logger.info(u"Finishing programming...")
                    self._send_status("progress", subtype="finishing")

                if connecting and reset and self.get_profile_setting_boolean("bootcmdr_preflashreset"):
                    reset = False
                    self._logger.info(u"Attempting to reset the board")
                    self._send_status("progress", subtype="boardreset")
                    if not _reset_board(self, printer_port, current_baudrate):
                        raise FlashException("Reset failed")
                    time.sleep(2)

        if p.returncode == 0:
            time.sleep(2)
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

def _reset_board(self, printer_port=None, baudrate=None):
    assert(printer_port is not None)
    assert(baudrate is not None)

    self._logger.info(u"Resetting printer at '{port}'".format(port=printer_port))

    try:
        ser = serial.Serial(printer_port, baudrate, timeout=1)
        ser.write(b'reset\r\n')
        ser.write(b'M997\r\n')
        ser.flush()
        ser.close()
    except serial.SerialException:
        self._logger.error(u"Board reset failed")
        return False

    return True

class FlashException(Exception):
	def __init__(self, reason, *args, **kwargs):
		Exception.__init__(self, *args, **kwargs)
		self.reason = reason
