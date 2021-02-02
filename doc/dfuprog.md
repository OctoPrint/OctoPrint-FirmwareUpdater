# Flashing an AT90USB Board with DFU Programmer

<p align="center">
  <img alt="Firmware Updater" src="../extras/img/dfu-prog.png">
</p>

To flash an AT90USB-based board the tool `dfu-programmer` needs to be installed on the OctoPrint host. 

## Dfu-programmer Installation
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
The minimum settings are:
* AVR MCU Type
* Path to dfu-programmer

Optional advanced settings are available for:
* Customizing the command lines for erasing and flashing the board

## DFU Mode
AT90USB boards must be in **Boot** or **DFU** mode before they can be flashed.  This is done by placing or removing a jumper then resetting the board.

For Printrboard:
* Remove the BOOT jumper (for Rev D, E & F boards, install the BOOT jumper)
* Press and release the **Reset** button.
* Replace the BOOT jumper onto the board (for Rev D, E & F boards, remove the BOOT jumper)

The board will now be ready for flashing. Once flashing is complete press the **Reset** button again to return to normal operation.
