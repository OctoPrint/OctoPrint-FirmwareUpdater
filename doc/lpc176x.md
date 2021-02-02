# Flashing a Board from the SD Card

This method applies to LPC1768 and LPC1769, and certain STM32 boards which have the required bootloader installed (e.g., SKR Pro v1.1, SKR Mini E3 v2).

## SD Card Mounting
Flashing an LPC176x board requires that the host can mount the board's on-board SD card to a known mount point in the host filesystem.  

There are several ways to do this, but using [usbmount](https://github.com/rbrito/usbmount) works well and is documented below. It will mount the SD card to `/media/usb`.

Once installed, usbmount requires some tweaking to make it work well on the Raspberry Pi.  The instructions below assume that you are running OctoPrint on a Raspberry Pi, as the user 'pi'.

### Marlin Firmware Options
The following options should be enabled in the Marlin firmware configuration in order for the board's SD card to be accessible by the OctoPrint host:
Configuration.h:
```
#define SDSUPPORT
```

Configuration_adv.h:
```
#define SDCARD_CONNECTION ONBOARD
```

Optionally, if you do not routinely use the SD card in Marlin, you can prevent Marlin mounting the card at startup, which will make firmware flashing faster as the firmware's lock on the card does not have to be released.

Configuration_adv.h:
```
#define SD_IGNORE_AT_STARTUP 
```

### Usbmount Installation
1. Install usbmount

   `sudo apt-get install usbmount`

2. Configure usbmount so that the mount has the correct permissions for the 'pi' user

   `sudo nano /etc/usbmount/usbmount.conf`
   
   Find FS_MOUNTOPTIONS and change it to:
   
   `FS_MOUNTOPTIONS="-fstype=vfat,gid=pi,uid=pi,dmask=0022,fmask=0111"`

3. Configure systemd-udevd so that the mount is accessible

   `sudo systemctl edit systemd-udevd`
   
   Insert these lines then save and close the file:
   ```
   [Service]
   PrivateMounts=no
   MountFlags=shared
   ```

   Then run:
   ```
   sudo systemctl daemon-reload
   sudo service systemd-udevd --full-restart
   ```
Once usbmount is installed and configured the LPC1768 on-board SD card should be mounted at `/media/usb` the next time it is plugged in or restarted.

**Important:** Do not modify the permissions on any of the /media/usb* directories!

See [here](https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/issues/175#issuecomment-760949800) and [here](https://github.com/OctoPrint/OctoPrint-FirmwareUpdater/issues/175#issuecomment-761111117) for the explanation of why this is important and a very bad idea.

### Sudo rights
The plugin needs to be able to unmount the SD card to reduce the risk of file system corruption.  The default command the plugin will use is `sudo umount /media/usb`.  You must be able to run this command at the command line without being prompted for a password.

If your system is configured to allow `pi` to run all `sudo` commands without a password (the default) then you do not need to do anything further.

If you need to enter a password when running `sudo` commands as `pi` you will need to create a new `sudoers` entry in order for the plugin to work correctly.
1. Run `sudo nano /etc/sudoers.d/020_firmware_updater` to create a new file
2. Paste this line into the new file:
   `pi ALL=NOPASSWD: /bin/umount`
3. Save and close the file
   
Otherwise, you can disable the unmount command entirely by clearing the **Unmount command** field in the plugin's advanced settings.

## LPC1768 Configuration
The only required setting is the path to the firmware update folder.  If using usbmount it will probably be `/media/usb`.

Optional advanced settings are available for:
* Resetting the board prior to flashing - adds an extra board reset which can help ensure that the SD card is mounted correctly

### Minimum Marlin Firmware Version
Some boards (e.g. SKR v1.3) have been known to ship with older Marlin firmware which does not support the `M997` command, so must be updated conventionally one time before using the plugin. A board running too-old Marlin firmware will log 'Board reset failed' when attempting to flash from the plugin.

If flashing an existing Marlin installation, the existing firmware must be newer than March 2nd, 2019 (i.e [this commit](https://github.com/MarlinFirmware/Marlin/pull/13281)) as that is when the `M997` was added to support resetting the board.

## Troubleshooting LPC1768 Uploads
The firmware upload will fail if the SD card is not accessible, either because it is not mounted on the host, or because the printer firmware has control over it.
