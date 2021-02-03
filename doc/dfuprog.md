# Flashing an AT90USB Board with DFU Programmer

Printrboard boards using AT90USB MCUs (and possibly other compatible boards) can be flashed using dfu-programmer.

## Table of Contents
1. [Dfu-programmer Installation](#dfu-programmer-installation)
   1. [Linux (including Raspberry Pi)](#linux-including-raspberry-pi)
1. [Dfu-programmer Configuration](#dfu-programmer-configuration)
   1. [Required Settings](#required-settings)
   1. [Optional Settings](#optional-settings)
1. [Hardware Notes](#hardware-notes)
   1. [Printrboard DFU Mode](#printrboard-dfu-mode)

## Dfu-programmer Installation
To flash an AT90USB-based board the tool `dfu-programmer` needs to be installed on the OctoPrint host. 

### Linux (including Raspberry Pi)
A version of `dfu-programmer` can be installed via `apt-get install` but it is outdated.  Please build the latest version from [Github](https://github.com/dfu-programmer/dfu-programmer) using these commands:

```
cd ~
sudo apt-get install autoconf libusb-1.0-0-dev
git clone https://github.com/dfu-programmer/dfu-programmer.git
cd dfu-programmer
./bootstrap.sh
./configure 
make
sudo make install
```
If there were no errors `dfu-programmer` should now be installed at /usr/local/bin/dfu-programmer.

## Dfu-programmer Configuration
<p align="center">
  <img alt="Firmware Updater" src="../extras/img/dfu-prog.png">
</p>

### Required Settings
The minimum settings are:
* AVR MCU Type
* Path to dfu-programmer

### Optional Settings
| Option | Description |
| --- | --- |
| Erase command line | The command used to erase the board prior to flashing. |
| Flash command line | The command used to flash the firmware to the board. |

## Hardware Notes
AT90USB boards must be in **Boot** or **DFU** mode before they can be flashed.  This is done by placing or removing a jumper then resetting the board.

### Printrboard DFU Mode
To put a Printrboard board into DFU mode:
* Remove the BOOT jumper (for Rev D, E & F boards, install the BOOT jumper)
* Press and release the **Reset** button.
* Replace the BOOT jumper onto the board (for Rev D, E & F boards, remove the BOOT jumper)

The board will now be ready for flashing. Once flashing is complete press the **Reset** button again to return to normal operation.
