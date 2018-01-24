# OctoPrint Firmware Updater

This plugin can be used to flash pre-compiled firmware images to your printer from a file or URL.

![Firmware Updater Plugin](extras/img/updater.png)

Works with boards with Atmega1280, Atmega1284p, and Atmega2560 MCUs using arduino, usbasp, or wiring programmers.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/archive/master.zip

### AVRDUDE setup

AVRDUDE needs to be installed on the server where OctoPrint is running.

#### Raspberry Pi

```
sudo apt-get update
sudo apt-get install avrdude
```

#### Ubuntu (12.04 - 14.04 - 15.04)

Information about the package needed can be found here [Ubuntu avrdude package](https://launchpad.net/ubuntu/+source/avrdude)

```
sudo add-apt-repository ppa:pmjdebruijn/avrdude-release
sudo apt-get update
sudo apt-get install avrdude
```

## Configuration

In order to be able to flash firmware we need to specify the path to avrdude, and some parameters it will need.

![Firmware Updater Plugin](extras/img/updater-settings.png)

You can use the post-flash gcode settings to run gcode commands after a successful firmware flash.

The post-flash code will run more or less immediately if the printer was connected before the flash started (so reconnects automatically when the flash finishes), or whenever the printer is manually reconnected.

The minimum settings are:
* Path to avrdude
* AVR MCU Type
* AVR Programmer Type

Typical MCU/programmer combinations are:

| AVR MCU | Programmer | Example Board |
| --- | --- | --- |
| Atmega1284p | arduino | Anet A series |
| Atmega2560 | wiring | RAMPS, RAMbo, etc. |
