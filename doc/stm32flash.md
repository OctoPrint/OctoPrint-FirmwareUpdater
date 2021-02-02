# Flashing an STM32 Board wth STM32Flash

**Note:** STM32-based boards which can be updated from the SD card (e.g., SKR Pro v1.1, SKR Mini E3 v2) should use the [lpc176x flash method](lpc176x.md).  This method described on this page is only for boards which are updated using stm32flash.

## STM32Flash Installation
To flash an STM32-based board using stm32flash, the tool needs to be installed on the OctoPrint host.

### Install on Linux/RaspberryPi using apt-get

```
sudo apt-get update
sudo apt-get install stm32flash
```

### Install on macOS using brew
```
brew install stm32flash
```

### Install on Windows
You can install a Windows binary from https://sourceforge.net/projects/stm32flash/ however the plugin hasn't been tested on that platform.

## STM32Flash Configuration
### Firmware verification
Unlike avrdude, verification is done during write process after each packet. Writing process is longer than other flashing methods, but there is no verification after the write. It is strongly recommended to keep it enabled.

### BOOT0/Reset pins
When using ST serial bootloader, the boards needs to enter into bootloader mode by setting up the MCU BOOT0 input to HIGH and then proceeding with a MCU RESET input to LOW. 

Such MCU inputs are generally connected to RTS/DTR signals of the USB-UART transceiver.  For example, FYSETC Cheetah uses RTS to set BOOT0, and DTR to reset.

Please set STM32Flash BOOT0/Reset according to your board.

### Execution address
Unlike other MCU, STM32 ones will remain in bootloader mode after resetting DTR line and realeasing UART. The bootloader needs an explicit command to jump at a given flash address.

Please setup Execution address according to your board.

### Reset
When setting Execution address, reset option is ignored by stm32flash. Setting Reset instead of Execution address will actually send an `Execute @ 0x00000000`, which is where the bootloader is located. You will then need to power cycle your board to execute firmware. This option is not recommended then. 
