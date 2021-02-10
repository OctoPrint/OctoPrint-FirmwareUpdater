# Flashing an LPC176x or STM32 board using Marlin's Binary File Transfer

Binary File ransfer is an alternative method to transfer the `firmware.bin` file to a printer that can be flashed from the SD card.

## Table of Contents
1. [Warnings and Caveats](#warnings-and-caveats)
1. [Installation](#installation)
   1. [Marlin Binary Protocol Package](#marlin-binary-protocol-package)
1. [Marlin Configuration](#marlin-configuration)
1. [Plugin Configuration](#plugin-configuration)
   1. [Required Settings](#required-settings)
   1. [Optional Settings](#optional-settings)

## Warnings and Caveats
1. **The binary file transfer protocol is still work in progress**
   While the current implementation works, it **will** change, and these changes **will** break the current version.  As much as possible, I will try to support the current implementation and the final version, but my ability to do so may be limited due to dependencies on other libraries.  

   If it comes to a choice, the final version will be the one which is supported.

1. **Your Raspberry Pi may crash, but it's not my fault**
   While developing this I came across what seems to be a [bug in the Raspberry Pi kerne](https://github.com/raspberrypi/linux/issues/4120)l, where it will sometimes panic (crash) when the printer board resets.  To mitigate this, as of Feb 6th 2021, a 2s delay [has been added](https://github.com/MarlinFirmware/Marlin/commit/004bed8a7fc3ff9feb73a0ea9794635b50073c27) to the LPC `M997` reset routine which appears to stop the crash from happening.  You will need to be running Marlin from the `bugfix-2.0.x` branch, after https://github.com/MarlinFirmware/Marlin/commit/004bed8a7fc3ff9feb73a0ea9794635b50073c27 to have the fix.

   On my test system, with the old reset code, I would easily crash my Pi anywhere between 1-25 resets.  After the change I have flashed the board dozens of times and reset it 500+ times without crashing it.

   That said, the underlying bug still exists, so you may still experience your Pi crashing when the board resets.  Caveat emptor.
   
## Installation
### Marlin Binary Protocol Package
The plugin currently uses the `marlin-binary-protocol` package to implement the transfer protocol.  This package has dependencies on `heatshrink`, which is hard to install automatically due to compatibility issues with Python2 and Python3.  For this reason the marlin-binary-protocol package and the heatshrink dependency need to be installed manually using `pip`.

NB: If you are running OctoPrint in a VirtualEnv you need to run the appropriate `pip` commands below inside that environment.

#### Python 2
1. Install `marlin-binary-protocol` - the dependencies just work
    `pip install marlin-binary-protocol`

#### Python3
1. Install a Python 3 compatible version of `heatshrink` to satisfy `marlin-binary-protocol`
    `pip3 install https://github.com/p3p/pyheatshrink/releases/download/0.3.3/pyheatshrink-pip.zip`
1. Install `marlin-binary-protocol`
    `pip3 install marlin-binary-protocol`

## Marlin Configuration
The line following line must be uncommented in `Configuration_adv.h`:

`#define BINARY_FILE_TRANSFER`

## PluginConfiguration
<p align="center">
  <img alt="Firmware Updater" src="../extras/img/marlinbft.png">
</p>

### Required Settings
There are no required settings.

### Optional Settings
| Option | Description |
| --- | --- |
| Wait after connect | Some boards reset after getting the command to start binary transfer mode. A value of 3 seconds is normal for when this wait is required. Default is 0. |
| Communication timeout | Protocol communication timeout. Default is 1000ms. |
| Verbose progress logging | Log verbose transfer progress to the OctoPrint log file |
