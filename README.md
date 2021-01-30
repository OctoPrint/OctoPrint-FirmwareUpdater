# OctoPrint Firmware Updater
The Firmware Updater plugin can be used to flash pre-compiled firmware images to your printer from a local file or URL.

<p align="center">
  <img alt="Firmware Updater" width="600" src="extras/img/firmware-updater.png">
</p>

## Documentation Index
1. [Supported Boards](#supported-boards)
1. [Plugin Installation](#plugin-installation)
1. [Plugin Configuration](#plugin-configuration)
   1. [ATmega Boards](doc/avrdude.md)
   1. [AT90USB Boards](doc/dfuprog.md)
   1. [LPC176x Boards](doc/lpc176x.md)
   1. [SAM Boards](doc/bossac.md)
   1. [STM32 Boards](doc/stm32flash.md)
1. [Flashing Firmware](#flashing-firmware)
1. [Advanced Options](#advanced-options)
   1. [Customizing the Command Lines](#customizing-the-command-lines)
   1. [Pre and Post Flash Settings](#pre-and-post-flash-settings)
   1. [Plugin Options](#plugin-options)
1. [Troubleshooting](#troubleshooting)
1. [Donations](#donations)

## Supported Boards
The plugin supports a variety of boards, based on the MCU (processor) they have:
* 'ATmega' family 8-bit MCUs (RAMPS, Sanguinololu, Melzi, Anet, Creality, Ender, Prusa MMU, Prusa CW1 many others)
* 'AT90USB' family 8-bit MCUs (Printrboard)
* 'LPC1768' & 'LPC1769' MCUs (MKS SBASE, SKR v1.1, v1.3, v1.4, etc., also SKR Pro v1.1)
* 'SAM' family 32-bit MCUs (Arduino DUE, etc.)
* 'STM32' family 32-bits MCUs with embedded ST serial bootloader (FYSETC Cheetah, **not** SKR Pro)
* 'STM32' family 32-bit MCUs which update from the SD card using the lpc176x method (SKR Pro v1.1, SKR Mini E3 v2, etc.)

Please open a [Github issue](https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/issues) if you would like a new board or MCU to be supported. If it's a new type of board which requires hardware testing please consider making a [donation](#Donations) to help fund the costs.

## Plugin Installation
Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:
    https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/master.zip

## Plugin Configuration
The appropriate flashing tool for the board type needs to be selected. 

| Board Family | Flashing Tool  |
| -----------: | :------------- | 
| ATmega       | avrdude        |
| AT90USB      | dfu-programmer |
| LPC176x      | lpc176x        |
| SAM          | bossac         |
| STM32        | stm32flash     |

#### Special Note for the SKR Pro v1.1 and SKR Mini E3 v2 STM32 Boards
It seems that SKR have included a custom bootloader which enables their STM32-based SKR Pro v1.1 and Mini E3 v2 boards (and maybe others) to be flashed using the same copy-and-reset procedure as their LPC176x-based boards.  **Please follow the LPC176x instructions for an SKR Pro v1.1 or SKR Mini E3 v2 boards.**  [Issue #103](https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/issues/103) may contain useful information for configuring the required firmware options.

#### Special Note for the Creality Ender 3
The mainboard in the Ender 3 (and probably other devices) is flashed without a boot loader. The first time you want to upgrade its firmware, you have to use extra programming hardware ("burner") to install a bootloader. Alternately you can use the "USB ISP" programmer which they include with their [BL-Touch Add-on Kit](https://www.creality3dofficial.com/products/creality-bl-touch?_pos=8&_sid=07be62867&_ss=rell), which comes with a pinout card. Using their kit instead of using this plugin can avoid exceeding memory limits with custom builds of Marlin.

### Board-Specific Configuration
Plugin settings vary depending on the flashing tool and are documented on the page for each flash method. Follow the instructions on the appropriate page to install and configure any necessary tools:
* [Atmega (AVR)](doc/avrdude.md)
* [AT90USB](doc/dfuprog.md)
* [LPC176x](doc/lpc176x.md)
* [SAM](doc/bossac.md)
* [STM32](doc/stm32flash.md)

## Flashing Firmware
Once the plugin is configured, flashing firmware is a simple operation:
1. Select the COM port to communicate with the board
1. Select a firmware file, either located on the filesystem or via a URL
1. Click the appropriate **Flash from** button
1. Wait for the firmware update to complete

## Advanced Options

### Customizing the Command Lines
The command lines for `avrdude`, `bossac`, and `dfu-programmer` can be customized by editing the string in the advanced settings for the flash method.  Text in braces (`{}`) will be substituted for preconfigured values if present.

| String | Description|
| --- | --- |
| `{avrdude}` | Full path to the `avrdude` executable<sup>1</sup> |
| `{bossac}` | Full path to the `bossac` executable<sup>2</sup> |
| `{dfuprogrammer}` | Full path to the `dfu-programmer` executable<sup>3</sup> |
| `{mcu}` | MCU type<sup>4</sup> |
| `{programmer}` | Avrdude programmer<sup>1</sup> |
| `{port}` | COM port the printer is connected to |
| `{conffile}` | Full path to the avrdude configuration file<sup>1</sup> |
| `{baudrate}` | Serial port speed<sup>1</sup> |
| `{disableverify}` | Switch to disable write verification |
| `{firmware}` | Path to the uploaded firmware file |

1. avrdude flash method only
2. bossac flash method only
3. dfu-programmer flash method only
4. avrdude and dfu-programmer flash methods

#### Command Line Defaults
Command lines can be returned to the default by clicking the **Reset** button.

##### Avrdude
`{avrdude} -v -q -p {mcu} -c {programmer} -P {port} -D -C {conffile} -b {baudrate} {disableverify} -U flash:w:{firmware}:i`

##### Bossac
`{bossac} -i -p {port} -U true -e -w {disableverify} -b {firmware} -R`

##### Dfu-programmer
Erase: `{bossac} -i -p {port} -U true -e -w {disableverify} -b {firmware} -R`
Flash: 

### Pre and Post-flash Settings

The flash sequence is:
1. Execute the pre-flash system command(s) on the host
1. Send the pre-flash gcode commands(s) to the printer
1. Pause for the pre-flash gcode delay
1. Disconnect the printer
1. Execute the firmware update
1. Pause for the post-flash delay
1. Execute the post-flash system command(s) on the host
1. Reconnect the printer
1. Send the post-flash gcode command(s) to the printer

| Option | Description |
| --- | --- |
| Pre-flash System Command| Specify a system command or script to run on the host prior to flashing.  Multiple commands can be separated with a semicolon. |
| Pre-flash Gcode | Specify gcode commands to run on the printer prior to flashing.  Multiple commands can be separated with a semicolon.  **Commands are only run if the printer is connected when flashing is initiated** |
| Pre-flash Gcode Delay | Delay after sending pre-flash gcode. Allows time for code to complete before initiating flash. |
| Post-flash Delay | This setting can be used to insert a delay of up to 180s after the firmware has been uploaded.  This can be useful if the board takes some time to restart.  A delay of 20-30s is usually enough. |
| Post-flash System Command | Specify a system command or script to run on the host after flashing.  Multiple commands can be separated with a semicolon. |
| Post-flash Gcode | You can use the post-flash gcode settings to run gcode commands after a successful firmware flash.  The post-flash code will run more or less immediately if the printer was connected before the flash started (so reconnects automatically when the flash finishes), or whenever the printer is manually reconnected after the firmware is flashed. |

### Plugin Options
| Option | Description |
| --- | --- |
| Enable Navbar Icon | Enables an icon in the OctoPrint Navbar which can be used to quickly access the Firmware Updater. |
| Remember URL | The last URL will be remembered when using 'Flash from URL. |

## Troubleshooting
Log messages can be found in the OctoPrint log `octoprint.log` and the Firmware Updater's console log `plugin_firmwareupdater_console.log`.  

Both log files can be downloaded from OctoPrint's logging interface, found under 'Logging' in the settings page.

If you have trouble using the plugin please check these logs for any error messages.  If you need help, please include both logs when reporting a problem.

## Donations
Donations to help with the cost of test hardware are gratefully received using any of the methods below.

| Currency | Link |
| --- | --- |
| Bitcoin | [1GjUmcjnAxCr9jFPUtVrr6gPQz8FhYddZz](https://www.blockchain.com/btc/address/1GjUmcjnAxCr9jFPUtVrr6gPQz8FhYddZz) |
| Bitcoin Cash | [bitcoincash:qzqys6mv9rgg7dxx0m4jzgqjezu9sryk2vmdexcr56](https://www.blockchain.com/bch/address/bitcoincash:qzqys6mv9rgg7dxx0m4jzgqjezu9sryk2vmdexcr56) |
| Ethereum | [0xA1788874E851b425F65FF5bcB6180b0d9F50fB6d](https://www.blockchain.com/eth/address/0xA1788874E851b425F65FF5bcB6180b0d9F50fB6d) |
| USD | [https://www.paypal.com/](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=PYRBY6KFWX5TJ&currency_code=USD&source=url) |
