# Flashing an Atmega (AVR) Board with Avrdude

<p align="center">
  <img alt="Firmware Updater" src="../extras/img/avrdude.png">
</p>

To flash an ATmega-based board the tool `avrdude` needs to be installed on the OctoPrint host.

## Avrdude Installation
### Raspberry Pi

```
sudo apt-get update
sudo apt-get install avrdude
```

### Ubuntu
Information about the package needed can be found here [Ubuntu avrdude package](https://launchpad.net/ubuntu/+source/avrdude)

```
sudo add-apt-repository ppa:pmjdebruijn/avrdude-release
sudo apt-get update
sudo apt-get install avrdude
```

## Avrdude Configuration
The minimum settings are:
* AVR MCU Type
* Path to avrdude
* AVR Programmer Type

Typical MCU/programmer combinations are:

| AVR MCU | Programmer | Example Board |
| --- | --- | --- |
| Atmega1284p | arduino | Anet A series, Creality, Ender, etc. |
| Atmega2560 | wiring | RAMPS, RAMbo, etc. |
| Atmega644p | arduino | Sanguinololu, Melzi |
| Atmega32u4 | avr109 | Prusa MMU, Prusa CW1 |

To locate `avrdude` on most Linux variants (including OctoPi):
* Connect via SSH and run the following: `which avrdude`
* The output should be similar to:
   ```
   pi@octopi:~ $ which avrdude
   /usr/bin/avrdude
   pi@octopi:~ $
   ```
* Add the full path to avrdude in the plugin settings.

Optional advanced settings are available for:
* Baud rate - sets the speed for communication with the board
* Avrdude config file - overrides the default config file with a custom one
* Disabling write verification - speeds up flashing by not verifying the write operation
* Customizing the avrdude command line
* Disabling the bootloader warning - disables a warning which is shown the hex filename has 'bootloader' in it

## Prusa MMU and CW1
Original firmware files for Prusa MMU and CW1 have special in the begining of the file:

For MMU these are:

```
1 ;device = mm-control   
2 
```

and for CW1:

```
1 ;device = cw1   
2 
```

The Firmware Updater plugin will automatically detect these headers and handle the files accordingly.

