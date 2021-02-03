import re
import os
import time
import shutil
import subprocess
import sys
import copy
import binproto2 as mbp

def _check_marlinbft(self):
    # TODO: Figure out how to check for the Marlin BFT capability
    return True

def _flash_marlinbft(self, firmware=None, printer_port=None):
    assert(firmware is not None)
    assert(printer_port is not None)

    self._logger.info(u"Transfering file to printer using Marlin BFT '{}' -> /firmware.bin".format(firmware))
    self._send_status("progress", subtype="sending")

    try:
        # Open the binary protocol connection
        protocol = mbp.Protocol(printer_port, 115200, 512, 1000, self._logger)

        # Make sure temperature auto-reporting is disabled
        protocol.send_ascii("M155 S0")

        # Connect
        protocol.connect()

        # Copy the file
        filetransfer = mbp.FileTransferProtocol(protocol, None)
        filetransfer.copy(firmware, 'firmware.bin', True, False)

        self._logger.info(u"Transfer complete")

        # Disconnect
        protocol.disconnect()

    except:
        self._logger.exception(u"Flashing failed. Unable to transfer file.")
        self._send_status("flasherror", message="Unable to transfer firmware file to printer")
        return False

    finally:
        if (protocol):
            protocol.shutdown()

    self._send_status("progress", subtype="boardreset")
    self._logger.info(u"Firmware update reset: attempting to reset the board")
    if not _reset_board(self, printer_port):
        self._logger.error(u"Reset failed")
        return False

    return True

def _reset_board(self, printer_port=None):
    assert(printer_port is not None)
    self._logger.info(u"Resetting printer at '{port}'".format(port=printer_port))

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

    if _wait_for_board(self, printer_port):
        return True
    else:
        self._logger.error(u"Board reset failed")
        self._send_status("flasherror", message="Board reset failed")
        return False

def _wait_for_board(self, printer_port=None):
    assert(printer_port is not None)
    self._logger.info(u"Waiting for printer at '{port}' to reset".format(port=printer_port))

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

    self._logger.info(u"Printer at '{port}' is resetting".format(port=printer_port))

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
    self._logger.info(u"Printer at '{port}' reset in {duration} seconds".format(port=printer_port, duration=(round((end - start),2))))
    return True
