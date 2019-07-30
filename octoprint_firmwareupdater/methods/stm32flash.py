import re
import os
import sarge

def getGPIO(pin, low):
    return ('-' if low else '') + pin

def _check_stm32flash(self):
    stm32flash_path = self._settings.get(["stm32flash_path"])

    pattern = re.compile("^(\/[^\0/]+)+$")

    if not pattern.match(stm32flash_path):
        self._logger.error(u"Path to stm32flash is not valid: {path}".format(path=avrdude_path))
        return False
    elif not os.path.exists(stm32flash_path):
        self._logger.error(u"Path to stm32flash does not exist: {path}".format(path=avrdude_path))
        return False
    elif not os.path.isfile(stm32flash_path):
        self._logger.error(u"Path to stm32flash is not a file: {path}".format(path=avrdude_path))
        return False
    elif not os.access(stm32flash_path, os.X_OK):
        self._logger.error(u"Path to stm32flash is not executable: {path}".format(path=avrdude_path))
        return False
    else:
        return True

def _flash_stm32flash(self, firmware=None, printer_port=None):
    assert(firmware is not None)
    assert(printer_port is not None)

    stm32flash_path = self._settings.get(["stm32flash_path"])
    stm32flash_verify = self._settings.get(["stm32flash_verify"])
    stm32flash_boot0pin = self._settings.get(["stm32flash_boot0pin"])
    stm32flash_boot0low = self._settings.get(["stm32flash_boot0low"])
    stm32flash_resetpin = self._settings.get(["stm32flash_resetpin"])
    stm32flash_resetlow = self._settings.get(["stm32flash_resetlow"])
    stm32flash_execute = self._settings.get(["stm32flash_execute"])
    stm32flash_executeaddress = self._settings.get(["stm32flash_executeaddress"])
    stm32flash_reset = self._settings.get(["stm32flash_reset"])


    working_dir = os.path.dirname(stm32flash_path)

    stm32flash_args = [
        stm32flash_path
    ]
    if (stm32flash_verify):
        stm32flash_args.append('-v')

    stm32flash_args.append('-i')
    stm32flash_args.append(','.join([
        getGPIO(stm32flash_boot0pin, stm32flash_boot0low),
        getGPIO(stm32flash_resetpin, stm32flash_resetlow),
        getGPIO(stm32flash_resetpin, not stm32flash_resetlow),
        getGPIO(stm32flash_boot0pin, not stm32flash_boot0low),
    ]))

    if (stm32flash_execute):
        stm32flash_args.append('-g')
        stm32flash_args.append(stm32flash_executeaddress)

    if (stm32flash_reset and not stm32flash_execute):
        stm32flash_args.append('-R')

    stm32flash_args.append('-w')
    stm32flash_args.append(firmware)
    stm32flash_args.append(printer_port)

    stm32flash_command = ' '.join(stm32flash_args)

    self._logger.info(u"Running '{}' in {}".format(stm32flash_command, working_dir))
    self._console_logger.info(u"")
    self._console_logger.info(stm32flash_command)

    try:
        p = sarge.run(stm32flash_command, cwd=working_dir, async=True, stdout=sarge.Capture(), stderr=sarge.Capture())
        p.wait_events()

        while p.returncode is None:
            output = p.stderr.read(timeout=0.5)
            if not output:
                p.commands[0].poll()
                continue

            for line in output.split("\n"):
                if line.endswith("\r"):
                    line = line[:-1]
                self._console_logger.info(u"> {}".format(line))

            if "Writing" in output:
                self._logger.info(u"Writing memory...")
                self._send_status("progress", subtype="writing")
            elif "Error" in output:
                p.commands[0].kill()
                p.close()
                raise FlashException("stm32flash error " + output[output.find("Error") + len("Error"):].strip() + "'")

        if p.returncode == 0:
            return True
        else:
            raise FlashException("stm32flash returned code {returncode}".format(returncode=p.returncode))

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
