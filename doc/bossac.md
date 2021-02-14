# Flashing a SAM board with Bossac

Arduino DUE and other Atmel SAM based 32-bit boards can be flashed using bossac.

## Table of Contents
1. [Bossac Installation](#bossac-installation)
   1. [Linux (including Raspberry Pi)](#linux-including-raspberry-pi)
1. [Bossac Configuration](#bossac-configuration)
   1. [Required Settings](#required-settings)
   1. [Optional Settings](#optional-settings)

## Bossac Installation
To flash a SAM-based board the tool `bossac` needs to be installed on the OctoPrint host.

### Linux (includng Raspberry Pi)
Bossac cannot be installed using a package manager as the packaged version is out of date and will not work.  Installation from source is straight-forward.

```
cd ~/
sudo apt-get install libwxgtk3.0-dev libreadline-dev
wget https://github.com/shumatech/BOSSA/archive/1.7.0.zip
unzip 1.7.0.zip
cd BOSSA-1.7.0
./arduino/make_package.sh
sudo cp ~/BOSSA-1.7.0/bin/bossac /usr/local/bin/
```

## Bossac Configuration
<p align="center">
  <img alt="Firmware Updater" src="../extras/img/bossac.png">
</p>

### Required Settings
The only required setting is the path to the bossac binary.

### Optional Settings
| Option | Description |
| --- | --- |
| Disable write verification | Speed up flashing by not verifying the write operation. Not recommended. |
| Flash command line | The command used to flash the firmware to the board. |
