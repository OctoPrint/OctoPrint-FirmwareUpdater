import os
import time
import datetime

binproto2_installed = True
try:
    import binproto2 as mbp
except:
    binproto2_installed = False

current_port = None
current_baudrate = None
current_profile = None

def _check_binproto2(self):
    global binproto2_installed
    self._settings.set_boolean(["has_binproto2package"], binproto2_installed)
    self._settings.save()
    return binproto2_installed

def _check_marlinbft(self):
    self._logger.info("Python package 'marlin-binary-protocol' is installed: %s" % (_check_binproto2(self)))
    self._logger.info("Marlin BINARY_FILE_TRANSFER capability is enabled: %s" % (self._settings.get_boolean(["has_bftcapability"])))

    if not _check_binproto2(self):
        self._logger.error("Python package 'marlin-binary-protocol' is not installed")
        self._send_status("flasherror", subtype="nobinproto2")
    elif not self._settings.get_boolean(["has_bftcapability"]):
        self._logger.error("Marlin BINARY_FILE_TRANSFER capability is not supported")
        self._send_status("flasherror", subtype="nobftcap")
        return False
    elif not self._printer.is_operational():
        self._logger.error("Printer is not connected")
        self._send_status("flasherror", subtype="notconnected")
        return False
    else:
        global current_baudrate
        global current_port
        global current_profile
        _, current_port, current_baudrate, current_profile = self._printer.get_current_connection()
        return True

def _flash_marlinbft(self, firmware=None, printer_port=None, **kwargs):
    assert(firmware is not None)
    assert(printer_port is not None)
    assert(current_baudrate is not None)

    # Get the settings
    selected_profile = self._settings.get_int(["_selected_profile"])
    bft_waitafterconnect = self.get_profile_setting_int("marlinbft_waitafterconnect")
    bft_timeout = self.get_profile_setting_int("marlinbft_timeout")
    bft_verbose = self.get_profile_setting_boolean("marlinbft_progresslogging")
    no_m997_reset_wait = self.get_profile_setting_boolean("marlinbft_no_m997_reset_wait")
    timestamp_filenames = self.get_profile_setting_boolean("marlinbft_timestamp_filenames")
    use_custom_filename = self.get_profile_setting_boolean("marlinbft_use_custom_filename")
    custom_filename = self.get_profile_setting("marlinbft_custom_filename").strip()

    self.set_profile_setting_boolean("marlinbft_got_start", False)

    # Logging
    if bft_verbose:
        transfer_logger = self._logger
    else:
        transfer_logger = None

    try:
        # Open the binary protocol connection
        self._logger.info("Current Baud: %s" % current_baudrate)

        self._logger.info(u"Initializing Marlin BFT protocol")
        self._send_status("progress", subtype="bftinit")
        protocol = mbp.Protocol(printer_port, current_baudrate, 512, bft_timeout, self._logger)

        # Wait after connect protocol
        if bft_waitafterconnect > 0:
            self._logger.info("waiting %ss after protocol connect" % bft_waitafterconnect)
            time.sleep(bft_waitafterconnect)

        # Try to delete the last-flashed file
        last_filename = self.get_lastbft_filename()
        if timestamp_filenames and last_filename is not None:
            self._logger.info(u"Attempting to delete previous firmware file /{}".format(last_filename))
            protocol.send_ascii("M21")
            protocol.send_ascii("M30 {}".format(last_filename))

        # Make sure temperature auto-reporting is disabled
        protocol.send_ascii("M155 S0")

        # Connect
        self._logger.info(u"Connecting to printer at '{}' using Marlin BFT protocol".format(printer_port))
        self._send_status("progress", subtype="bftconnect")
        protocol.connect()

        # Copy the file
        if timestamp_filenames:
            target = datetime.datetime.now().strftime("fw%H%M%S.bin")
        elif use_custom_filename and custom_filename is not None:
            target = custom_filename
        else:
            target = "firmware.bin"

        self._logger.info(u"Transfering file to printer using Marlin BFT '{}' -> /{}".format(firmware, target))
        self._send_status("progress", subtype="sending")
        filetransfer = mbp.FileTransferProtocol(protocol, logger=transfer_logger)
        filetransfer.copy(firmware, target, True, False)
        self._logger.info(u"Binary file transfer complete")

        # Save the filename
        if timestamp_filenames:
            self._logger.info(u"Setting '{}' as last firmware filename".format(target))
            self.set_lastbft_filename(target)

        # Disconnect
        protocol.disconnect()

        # Display a message on the LCD
        protocol.send_ascii("M117 Resetting...")

    except mbp.exceptions.ConnectionLost:
        self._logger.exception(u"Flashing failed. Unable to connect to printer.")
        self._send_status("flasherror", message="Unable to open binary file transfer connection")
        return False

    except mbp.exceptions.FatalError:
        self._logger.exception(u"Flashing failed. Too many retries.")
        self._send_status("flasherror", message="Unable to transfer firmware file to printer - too many retries")
        return False

    except:
        self._logger.exception(u"Flashing failed. Unable to transfer file.")
        self._send_status("flasherror", message="Unable to transfer firmware file to printer")
        return False

    finally:
        if (protocol):
            protocol.shutdown()

    self._send_status("progress", subtype="boardreset")
    self._logger.info(u"Firmware update reset: attempting to reset the board")
    if not _reset_board(self, printer_port, current_baudrate, no_m997_reset_wait):
        self._logger.error(u"Reset failed")
        return False

    return True

def _reset_board(self, printer_port=None, current_baudrate=None, no_reset_wait=False):
    assert(printer_port is not None)
    assert(current_baudrate is not None)

    no_m997_restart_wait = self.get_profile_setting_boolean("marlinbft_no_m997_restart_wait")
    alt_reset_method = self.get_profile_setting_boolean("marlinbft_alt_reset")
    self._logger.info(u"Resetting printer at '{port}'".format(port=printer_port))

    # Configure the port
    try:
        os.system('stty -F ' + printer_port + ' speed ' + str(current_baudrate) + ' -echo > /dev/null')
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
    if alt_reset_method:
        temp_prevent_connect = self._settings.get_boolean(["prevent_connection_when_flashing"])
        self._settings.set_boolean(["prevent_connection_when_flashing"], False)
        try:
            global current_port
            global current_profile
            self._logger.info(u"Reconnecting to printer at port '{port}' to initiate reset".format(port=current_port))
            self._printer.connect(port=current_port, baudrate=current_baudrate, profile=current_profile)
            time.sleep(2)
            self._logger.info(u"Sending M997 reset command to printer")
            self._printer.commands("M997")
        except:
            self._logger.exception(u"Error sending Marlin 'M997' command.")
            self._send_status("flasherror", message="Board reset failed")
            return False
        finally:
            self._settings.set_boolean(["prevent_connection_when_flashing"], temp_prevent_connect)

        if no_m997_restart_wait:
            # Give the board time to reset so that OctoPrint does not try to reconnect before the reset
            self._logger.info(u"Not waiting for reset")
            return True
        else:
            if _wait_for_start(self, current_port):
                self._logger.info(u"Disconnecting printer")
                self._printer.disconnect()
                return True
            else:
                self._send_status("flasherror", message="Firmware update failed")
                return False
    else:
        try:
            self._logger.info(u"Sending out-of-band reset command to '{port}'".format(port=printer_port))
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
            if _wait_for_board(self, printer_port, no_m997_restart_wait):
                return True
            else:
                self._logger.error(u"Board reset failed")
                self._send_status("flasherror", message="Board reset failed")
                return False

def _wait_for_start(self, printer_port=None):
    assert(printer_port is not None)
    m997_restart_wait = self.get_profile_setting("marlinbft_m997_restart_wait")
    self._logger.info(u"Waiting {seconds}s for printer at '{port}' to reset".format(seconds=m997_restart_wait, port=printer_port))

    start = time.time()
    timeout = m997_restart_wait
    interval = 0.2
    count = 1
    restarted = False
    loopstarttime = time.time()

    while (time.time() < (loopstarttime + timeout) and not restarted):
        self._logger.debug(u"Waiting for reset [{}/{}]".format(count, int(timeout / interval)))
        count = count + 1
        if not self.get_profile_setting_boolean("marlinbft_got_start"):
            restarted = False
            time.sleep(interval)
        else:
            time.sleep(interval)
            restarted = True

    if not restarted:
        self._logger.error(u"Timeout waiting for board to reset")
        return False

    end = time.time()
    duration = round((end - start),2)

    self._logger.info(u"Printer at '{port}' reset in {duration} seconds".format(port=printer_port, duration=(round((end - start),2))))

    if duration < 1:
        self._logger.error(u"Board reset too quickly - firmware could not have updated")
        self.set_profile_setting_boolean("marlinbft_got_start", False)
        return False
    else:
        self.set_profile_setting_boolean("marlinbft_got_start", False)
        return True

def _wait_for_board(self, printer_port=None, no_restart_wait=False):
    assert(printer_port is not None)

    m997_reset_wait = self.get_profile_setting("marlinbft_m997_reset_wait")
    if m997_reset_wait is None:
        m997_reset_wait = 10

    self._logger.info(u"Waiting {seconds}s for printer at '{port}' to reset".format(seconds=m997_reset_wait, port=printer_port))

    check_command = 'ls ' + printer_port + ' > /dev/null 2>&1'
    start = time.time()
    timeout = m997_reset_wait
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

    self._logger.info(u"Printer at '{port}' is resetting".format(port=printer_port))

    if no_restart_wait:
        self._logger.info(u"Not waiting for restart to complete")
        return True
    else:
        time.sleep(3)
        m997_restart_wait = self.get_profile_setting("marlinbft_m997_restart_wait")
        if m997_restart_wait is None:
            m997_restart_wait = 20

        self._logger.info(u"Waiting {seconds}s for printer at '{port}' to restart".format(seconds=m997_restart_wait, port=printer_port))

        timeout = m997_restart_wait
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
        self._logger.info(u"Printer at '{port}' reset in {duration} seconds".format(port=printer_port, duration=(round((end - start),2))))
        return True
