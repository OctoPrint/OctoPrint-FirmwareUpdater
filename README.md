# OctoPrint Firmware Updater

This plugin can be used to flash the firmware of your printer by selecting a file or an URL.

It can also check automatically for new firmwares by getting the printer's current firmware version and checking online
for the latest one.

![Firmware Updater Plugin](http://i.imgur.com/3S37KUM.png)

The automatic firmware update is done by detecting the current firmware version from the M115's response. This response string is
parsed to identify the MACHINE_TYPE and the FIRMWARE_VERSION. This information is then sent to a web service which responds with
information about the latests firmware available and the URL to download it, which is done automatically after the check.

The update check can be done automatically after connecting to the printer or manually from the plugin's dialog.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/master.zip

## Configuration

In order to be able to flash the firmware, avrdude is needed. The path to avrdude can be set in the plugin's configuration dialog.

Also, the URL to the web service can be set manually by editing OctoPrint's config.yaml