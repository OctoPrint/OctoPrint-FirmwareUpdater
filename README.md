# OctoPrint Firmware Updater

This plugin can be used to flash the firmware of your printer by selecting a file or an URL.

It can also manage automatic new firmware checks by connecting to the printer to get it's current FW version
and consult a web service for the latest one. 

![Firmware Updater Plugin](http://i.imgur.com/3S37KUM.png)

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/master.zip

## Configuration

In order to be able to flash the firmware, avrdude is needed. The path to avrdude can be set in the plugin's configuration dialog.

Also, the URL to the web service can be set manually by editing OctoPrint's config.yaml