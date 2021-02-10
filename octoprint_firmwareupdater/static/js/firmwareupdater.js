$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];
        self.access = parameters[4];

        // General settings
        self.configFlashMethod = ko.observable();
        self.configShowNavbarIcon = ko.observable();
        self.showFirmwareUpdaterNavbarIcon = ko.observable(false);
        self.showAdvancedConfig = ko.observable(false);
        self.showAvrdudeConfig = ko.observable(false);
        self.showBossacConfig = ko.observable(false);
        self.showLpc1768Config = ko.observable(false);
        self.showDfuConfig = ko.observable(false);
        self.showStm32flashConfig = ko.observable(false);
        self.showMarlinBftConfig = ko.observable(false);
        self.showPostflashConfig = ko.observable(false);
        self.showPluginOptions = ko.observable(false);
        self.configEnablePostflashDelay = ko.observable();
        self.configEnablePreflashDelay = ko.observable();
        self.configPostflashDelay = ko.observable();
        self.configPreflashDelay = ko.observable();
        self.configEnablePostflashGcode = ko.observable();
        self.configPostflashGcode = ko.observable();
        self.configDisableBootloaderCheck = ko.observable();
        self.configEnablePreflashCommandline = ko.observable();
        self.configPreflashCommandline = ko.observable();
        self.configEnablePostflashCommandline = ko.observable();
        self.configPostflashCommandline = ko.observable();
        self.configEnablePreflashGcode = ko.observable();
        self.configPreflashGcode = ko.observable();
        self.configSaveUrl = ko.observable();
        self.configLastUrl = ko.observable();
        self.configDisableFileFilter = ko.observable();
        self.pluginVersion = ko.observable();

        self.filterFileTypes = ko.computed(function() {
            if (self.configDisableFileFilter()) {
                return null;
            } else {
                return '.hex,.bin';
            }
        });

        // Config settings for avrdude
        self.configAvrdudeMcu = ko.observable();
        self.configAvrdudePath = ko.observable();
        self.configAvrdudeConfigFile = ko.observable();
        self.configAvrdudeProgrammer = ko.observable();
        self.configAvrdudeBaudRate = ko.observable();
        self.configAvrdudeDisableVerification = ko.observable();
        self.configAvrdudeCommandLine = ko.observable();
        self.avrdudePathBroken = ko.observable(false);
        self.avrdudePathOk = ko.observable(false);
        self.avrdudePathText = ko.observable();
        self.avrdudePathHelpVisible = ko.computed(function() {
            return self.avrdudePathBroken() || self.avrdudePathOk();
        });

        self.avrdudeConfPathBroken = ko.observable(false);
        self.avrdudeConfPathOk = ko.observable(false);
        self.avrdudeConfPathText = ko.observable();
        self.avrdudeConfPathHelpVisible = ko.computed(function() {
            return self.avrdudeConfPathBroken() || self.avrdudeConfPathOk();
        });

        // Config settings for bossac
        self.configBossacPath = ko.observable();
        self.configBossacDisableVerification = ko.observable()
        self.configBossacCommandLine = ko.observable();

        self.bossacPathBroken = ko.observable(false);
        self.bossacPathOk = ko.observable(false);
        self.bossacPathText = ko.observable();
        self.bossacPathHelpVisible = ko.computed(function() {
            return self.bossacPathBroken() || self.bossacPathOk();
        });

        // Config settings for lpc1768
        self.configLpc1768Path = ko.observable();
        self.configLpc1768ResetBeforeFlash = ko.observable();
        self.configLpc1768UnmountCommand = ko.observable();
        self.lpc1768PathBroken = ko.observable(false);
        self.lpc1768PathOk = ko.observable(false);
        self.lpc1768PathText = ko.observable();
        self.lpc1768PathHelpVisible = ko.computed(function() {
            return self.lpc1768PathBroken() || self.lpc1768PathOk();
        });

        // Config settings for marlinbft
        self.configMarlinBftWaitAfterConnect = ko.observable();
        self.configMarlinBftTimeout = ko.observable();
        self.configMarlinBftProgressLogging = ko.observable();
        self.marlinbftHasCapability = ko.observable();

        // Config settings for dfu-programmer
        self.configDfuMcu = ko.observable();
        self.configDfuPath = ko.observable();
        self.configDfuCommandLine = ko.observable();
        self.configDfuEraseCommandLine = ko.observable();
        self.dfuPathBroken = ko.observable(false);
        self.dfuPathOk = ko.observable(false);
        self.dfuPathText = ko.observable();
        self.dfuPathHelpVisible = ko.computed(function() {
            return self.dfuPathBroken() || self.dfuPathOk();
        });

        // Config settings for stm32flash
        self.configStm32flashPath = ko.observable();
        self.configStm32flashVerify = ko.observable(true);
        self.configStm32flashBoot0Pin = ko.observable();
        self.configStm32flashBoot0Low = ko.observable(true);
        self.configStm32flashResetPin = ko.observable();
        self.configStm32flashResetLow = ko.observable(true);
        self.configStm32flashExecute = ko.observable();
        self.configStm32flashExecuteAddress = ko.observable();
        self.configStm32flashReset = ko.observable(false);
        self.stm32flashPathBroken = ko.observable();
        self.stm32flashPathOk = ko.observable(false);
        self.stm32flashPathText = ko.observable();
        self.stm32flashPathHelpVisible = ko.computed(function() {
            return self.stm32flashPathBroken() || self.stm32flashPathOk();
        });

        self.flashPort = ko.observable(undefined);

        self.firmwareFileName = ko.observable(undefined);
        self.firmwareFileURL = ko.observable(undefined);

        self.alertMessage = ko.observable("");
        self.alertType = ko.observable("alert-warning");
        self.showAlert = ko.observable(false);
        self.missingParamToFlash = ko.observable(false);
        self.progressBarText = ko.observable();
        self.isBusy = ko.observable(false);
        self.fileFlashButtonText = ko.observable("");
        self.urlFlashButtonText = ko.observable("");
        self.saving = ko.observable(false);

        self.selectFilePath = undefined;
        self.configurationDialog = undefined;

        self.inSettingsDialog = false;

        self.onAllBound = function(allViewModels) {
            self.configShowNavbarIcon(self.settingsViewModel.settings.plugins.firmwareupdater.enable_navbar());
            if (self.loginState.isAdmin() && self.configShowNavbarIcon()) {
                self.showFirmwareUpdaterNavbarIcon(true);
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                self.firmwareFileURL(self.settingsViewModel.settings.plugins.firmwareupdater.last_url());
            } else {
                self.firmwareFileURL("");
            }

            self.marlinbftHasCapability(self.settingsViewModel.settings.plugins.firmwareupdater.marlinbft_hascapability());
            self.configDisableFileFilter(self.settingsViewModel.settings.plugins.firmwareupdater.disable_filefilter());
            self.pluginVersion(self.settingsViewModel.settings.plugins.firmwareupdater.plugin_version());
        }

        self.showFirmwareUpdater = function(){
            self.settingsViewModel.show("#settings_plugin_firmwareupdater");
        }

        self.connection.selectedPort.subscribe(function(value) {
            if (value === undefined) return;
            self.flashPort(value);
        });

        self.toggleAdvancedConfig = function(){
            self.showAdvancedConfig(!self.showAdvancedConfig());
        }

        self.togglePostflashConfig = function(){
            self.showPostflashConfig(!self.showPostflashConfig());
        }

        self.togglePluginOptions = function(){
            self.showPluginOptions(!self.showPluginOptions());
        }

        self.configFlashMethod.subscribe(function(value) {
            if(value == 'avrdude') {
                self.showAvrdudeConfig(true);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
                self.showDfuConfig(false);
                self.showStm32flashConfig(false);
                self.showMarlinBftConfig(false);
            } else if(value == 'bossac') {
                self.showAvrdudeConfig(false);
                self.showBossacConfig(true);
                self.showLpc1768Config(false);
                self.showDfuConfig(false);
                self.showStm32flashConfig(false);
                self.showMarlinBftConfig(false);
            } else if(value == 'lpc1768'){
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(true);
                self.showStm32flashConfig(false);
                self.showDfuConfig(false);
                self.showMarlinBftConfig(false);
            } else if(value == 'dfuprogrammer'){
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
                self.showDfuConfig(true);
                self.showStm32flashConfig(false);
                self.showMarlinBftConfig(false);
            } else if(value == 'stm32flash'){
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
                self.showDfuConfig(false);
                self.showStm32flashConfig(true);
                self.showMarlinBftConfig(false);
            } else if(value == 'marlinbft'){
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
                self.showDfuConfig(false);
                self.showStm32flashConfig(false);
                self.showMarlinBftConfig(true);
            } else {
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
                self.showDfuConfig(false);
                self.showStm32flashConfig(false);
                self.showMarlinBftConfig(false);
            }
         });

         self.firmwareFileName.subscribe(function(value) {
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.disable_bootloadercheck()) {
                if (self._checkForBootloader(value)) {
                    self.bootloaderWarningDialog.modal();
                }
            }
         });

        self.onStartup = function() {
            self.selectFilePath = $("#settings_firmwareupdater_selectFilePath");
            self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");
            self.bootloaderWarningDialog = $("#BootLoaderWarning");

            self.selectFilePath.fileupload({
                dataType: "hex",
                maxNumberOfFiles: 1,
                autoUpload: false,
                add: function(e, data) {
                    if (data.files.length === 0) {
                        return false;
                    }
                    self.hexData = data;
                    self.firmwareFileName(data.files[0].name);
                }
            });
        };

        self._checkIfReadyToFlash = function(source) {
            var alert = undefined;

            if (!self.loginState.isAdmin()){
                alert = gettext("You need administrator privileges to flash firmware.");
            }

            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                alert = gettext("Printer is printing. Please wait for the print to be finished.");
            }

            if (!self.settingsViewModel.settings.plugins.firmwareupdater.flash_method()){
                alert = gettext("The flash method is not selected.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "avrdude" && !self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu()) {
                alert = gettext("The AVR MCU type is not selected.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "avrdude" && !self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                alert = gettext("The avrdude path is not configured.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "avrdude" && !self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_programmer()) {
                alert = gettext("The AVR programmer is not selected.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "bossac" && !self.settingsViewModel.settings.plugins.firmwareupdater.bossac_path()) {
                alert = gettext("The bossac path is not configured.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "lpc1768" && !self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_path()) {
                alert = gettext("The lpc1768 firmware folder path is not configured.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "dfuprogrammer" && !self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_path()) {
                alert = gettext("The dfu-programmer path is not configured.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "dfuprogrammer" && !self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_avrmcu()) {
                alert = gettext("The AVR MCU type is not selected.");
            }
            
            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "marlinbft" && !self.printerState.isReady()) {
                alert = gettext("The printer is not connected.");
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "marlinbft" && self.printerState.isReady() && !self.marlinbftHasCapability()) {
                alert = gettext("The printer does not support Binary File Transfer.");
            }

            if (!self.flashPort() &! self.settingsViewModel.settings.plugins.firmwareupdater.flash_method() == "dfuprogrammer") {
                alert = gettext("The printer port is not selected.");
            }

            if (source === "file" && !self.firmwareFileName()) {
                alert = gettext("Firmware file is not specified");
            } else if (source === "url" && !self.firmwareFileURL()) {
                alert = gettext("Firmware URL is not specified");
            }

            if (alert !== undefined) {
                self.alertType("alert-warning");
                self.alertMessage(alert);
                self.showAlert(true);
                return false;
            } else {
                self.alertMessage(undefined);
                self.showAlert(false);
            }

            return true;
        };

        self._checkForBootloader = function(filename) {
            if (filename.search(/bootloader/i) > -1) {
                return true;
            } else {
                return false;
            }
        }

        self.returnTrue = function() {
            return true;
        }

        self.returnFalse = function() {
            return false;
        }

        self.startFlashFromFile = function() {
            if (!self._checkIfReadyToFlash("file")) {
                return;
            }

            self.progressBarText("Flashing firmware...");
            self.isBusy(true);
            self.showAlert(false);

            self.hexData.formData = {
                port: self.flashPort()
            };
            self.hexData.submit();
        };

        self.startFlashFromURL = function() {
            if (!self._checkIfReadyToFlash("url")) {
                return;
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                self.configLastUrl(self.firmwareFileURL());
                self._saveLastUrl();
            }

            self.isBusy(true);
            self.showAlert(false);
            self.progressBarText("Flashing firmware...");

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/flash",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    port: self.flashPort(),
                    url: self.firmwareFileURL()
                }),
                contentType: "application/json; charset=UTF-8"
            })
        };

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin !== "firmwareupdater") {
                return;
            }

            var message;

            switch (data.type) {
                case "capability": {
                    if (data.capability == "BINARY_FILE_TRANSFER") {
                        self.marlinbftHasCapability(data.enabled);
                    }
                    break;
                }
                case "status": {
                    switch (data.status) {
                        case "flasherror": {
                            if (data.message) {
                                message = gettext(data.message);
                            } else {
                                message = gettext("Unknown error");
                            }

                            if (data.subtype) {
                                switch (data.subtype) {
                                    case "busy": {
                                        message = gettext("Printer is busy.");
                                        break;
                                    }
                                    case "port": {
                                        message = gettext("Printer port is not available.");
                                        break;
                                    }
                                    case "method": {
                                        message = gettext("Flash method is not properly configured.");
                                        break;
                                    }
                                    case "hexfile": {
                                        message = gettext("Cannot read file to flash.");
                                        break;
                                    }
                                    case "notconnected": {
                                        message = gettext("Printer is not connected.");
                                        break;
                                    }
                                    case "nobftcap": {
                                        message = gettext("Printer does not report support for the Marlin Binary File Transfer protocol.");
                                        break;
                                    }
                                    case "nobinproto2": {
                                        message = gettext("Python package 'marlin-binary-protocol' is not installed.");
                                        break;
                                    }
                                    case "already_flashing": {
                                        message = gettext("Already flashing.");
                                    }
                                }
                            }

                            self.showPopup("error", gettext("Flashing failed"), message);
                            self.isBusy(false);
                            self.showAlert(false);
                            self.firmwareFileName("");
                            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                                self.firmwareFileURL(self.configLastUrl());
                            } else {
                                self.firmwareFileURL("");
                            }
                            break;
                        }
                        case "success": {
                            self.showPopup("success", gettext("Flashing successful"), "");
                            self.isBusy(false);
                            self.showAlert(false);
                            self.firmwareFileName("");
                            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                                self.firmwareFileURL(self.configLastUrl());
                            } else {
                                self.firmwareFileURL("");
                            }
                            break;
                        }
                        case "progress": {
                            if (data.subtype) {
                                switch (data.subtype) {
                                    case "disconnecting": {
                                        message = gettext("Disconnecting printer...");
                                        break;
                                    }
                                    case "startingflash": {
                                        self.isBusy(true);
                                        message = gettext("Starting flash...");
                                        break;
                                    }
                                    case "waitforsd": {
                                        message = gettext("Waiting for SD card to mount on host...");
                                        break;
                                    }
                                    case "copying": {
                                        message = gettext("Copying firmware to SD card...");
                                        break;
                                    }
                                    case "bftinit": {
                                        message = gettext("Initializing file transfer protocol...");
                                        break;
                                    }
                                    case "bftconnect": {
                                        message = gettext("Connecting file transfer protocol...");
                                        break;
                                    }
                                    case "finishing": {
                                        message = gettext("Finishing up...");
                                        break;
                                    }
                                    case "sending": {
                                        message = gettext("Sending firmware to printer...");
                                        break;
                                    }
                                    case "unmounting": {
                                        message = gettext("Unmounting SD card...");
                                        break;
                                    }
                                    case "writing": {
                                        message = gettext("Writing memory...");
                                        break;
                                    }
                                    case "erasing": {
                                        message = gettext("Erasing memory...");
                                        break;
                                    }
                                    case "verifying": {
                                        message = gettext("Verifying memory...");
                                        break;
                                    }
                                    case "postflashdelay": {
                                        message = gettext("Post-flash delay...");
                                        break;
                                    }
                                    case "boardreset": {
                                            message = gettext("Resetting the board...");
                                            break;
                                    }
                                    case "reconnecting": {
                                        message = gettext("Reconnecting to printer...");
                                        break;
                                    }
                                }
                            }

                            if (message) {
                                self.progressBarText(message);
                            }
                            break;
                        }
                        case "info": {
                            self.alertType("alert-info");
                            self.alertMessage(data.status_description);
                            self.showAlert(true);
                            break;
                        }
                    }
                    break;
                }
            }
        };

        self.showPluginConfig = function() {
            // Load the general settings
            self.configFlashMethod(self.settingsViewModel.settings.plugins.firmwareupdater.flash_method());
            self.configShowNavbarIcon(self.settingsViewModel.settings.plugins.firmwareupdater.enable_navbar());
            self.configPreflashCommandline(self.settingsViewModel.settings.plugins.firmwareupdater.preflash_commandline());
            self.configPostflashCommandline(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_commandline());
            self.configPostflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_delay());
            self.configPreflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.preflash_delay());
            self.configPostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_gcode());
            self.configPreflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.preflash_gcode());
            self.configSaveUrl(self.settingsViewModel.settings.plugins.firmwareupdater.save_url());
            self.configLastUrl(self.settingsViewModel.settings.plugins.firmwareupdater.last_url());

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_commandline() != 'false') {
                self.configEnablePreflashCommandline(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_commandline());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_commandline() != 'false') {
                self.configEnablePostflashCommandline(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_commandline());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_delay() != 'false') {
                self.configEnablePostflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_delay());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_delay() != 'false') {
                self.configEnablePreflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_delay());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode() != 'false') {
                self.configEnablePostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_gcode() != 'false') {
                self.configEnablePreflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.enable_preflash_gcode());
            }

            if(self.settingsViewModel.settings.plugins.firmwareupdater.disable_bootloadercheck() != 'false') {
                self.configDisableBootloaderCheck(self.settingsViewModel.settings.plugins.firmwareupdater.disable_bootloadercheck());
            }

            if (self.settingsViewModel.settings.plugins.firmwareupdater.disable_filefilter() != 'false') {
                self.configDisableFileFilter(self.settingsViewModel.settings.plugins.firmwareupdater.disable_filefilter());
            }

            // Load the avrdude settings
            self.configAvrdudePath(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path());
            self.configAvrdudeConfigFile(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_conf());
            self.configAvrdudeMcu(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu());
            self.configAvrdudeProgrammer(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_programmer());
            self.configAvrdudeBaudRate(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_baudrate());
            if(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_disableverify() != 'false') {
                self.configAvrdudeDisableVerification(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_disableverify());
            }
            self.configAvrdudeCommandLine(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_commandline());

            // Load the bossac settings
            self.configBossacPath(self.settingsViewModel.settings.plugins.firmwareupdater.bossac_path());
            self.configBossacDisableVerification(self.settingsViewModel.settings.plugins.firmwareupdater.bossac_disableverify());
            self.configBossacCommandLine(self.settingsViewModel.settings.plugins.firmwareupdater.bossac_commandline());

            // Load the dfu-programmer settings
            self.configDfuPath(self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_path());
            self.configDfuMcu(self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_avrmcu());
            self.configDfuCommandLine(self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_commandline());
            self.configDfuEraseCommandLine(self.settingsViewModel.settings.plugins.firmwareupdater.dfuprog_erasecommandline());

            // Load the lpc1768 settings
            self.configLpc1768Path(self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_path());
            self.configLpc1768UnmountCommand(self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_unmount_command());
            if(self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_preflashreset() != 'false') {
                self.configLpc1768ResetBeforeFlash(self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_preflashreset());
            }

            // Load the marlinbft settings
            self.configMarlinBftWaitAfterConnect(self.settingsViewModel.settings.plugins.firmwareupdater.marlinbft_waitafterconnect());
            self.configMarlinBftTimeout(self.settingsViewModel.settings.plugins.firmwareupdater.marlinbft_timeout());
            self.configMarlinBftProgressLogging(self.settingsViewModel.settings.plugins.firmwareupdater.marlinbft_progresslogging());

            // Load the stm32flash settings
            self.configStm32flashPath(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_path());
            self.configStm32flashVerify(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_verify());
            self.configStm32flashBoot0Pin(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_boot0pin());
            self.configStm32flashBoot0Low(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_boot0low());
            self.configStm32flashResetPin(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_resetpin());
            self.configStm32flashResetLow(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_resetlow());
            self.configStm32flashExecute(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_execute());
            self.configStm32flashExecuteAddress(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_executeaddress());
            self.configStm32flashReset(self.settingsViewModel.settings.plugins.firmwareupdater.stm32flash_reset());

            self.configurationDialog.modal();
        };

        self.onConfigClose = function() {
            self._saveConfig();
        };

        self._saveConfig = function() {
            self.saving(true);
            var lastUrl;
            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url() &! self.configSaveUrl()) {
                self.firmwareFileURL("");
                lastUrl = null;
            } else {
                lastUrl = self.configLastUrl();
            }

            var data = {
                plugins: {
                    firmwareupdater: {
                        flash_method: self.configFlashMethod(),
                        enable_navbar: self.configShowNavbarIcon(),
                        avrdude_path: self.configAvrdudePath(),
                        avrdude_conf: self.configAvrdudeConfigFile(),
                        avrdude_avrmcu: self.configAvrdudeMcu(),
                        avrdude_programmer: self.configAvrdudeProgrammer(),
                        avrdude_baudrate: self.configAvrdudeBaudRate(),
                        avrdude_disableverify: self.configAvrdudeDisableVerification(),
                        avrdude_commandline: self.configAvrdudeCommandLine(),
                        bossac_path: self.configBossacPath(),
                        bossac_disableverify: self.configBossacDisableVerification(),
                        bossac_commandline: self.configBossacCommandLine(),
                        dfuprog_path: self.configDfuPath(),
                        dfuprog_avrmcu: self.configDfuMcu(),
                        dfuprog_commandline: self.configDfuCommandLine(),
                        dfuprog_erasecommandline: self.configDfuEraseCommandLine(),
                        stm32flash_path : self.configStm32flashPath(),
                        stm32flash_verify: self.configStm32flashVerify(),
                        stm32flash_boot0pin : self.configStm32flashBoot0Pin(),
                        stm32flash_boot0low : self.configStm32flashBoot0Low(),
                        stm32flash_resetpin : self.configStm32flashResetPin(),
                        stm32flash_resetlow : self.configStm32flashResetLow(),
                        stm32flash_execute : self.configStm32flashExecute(),
                        stm32flash_executeaddress : self.configStm32flashExecuteAddress(),
                        stm32flash_reset: self.configStm32flashReset(),
                        lpc1768_path: self.configLpc1768Path(),
                        lpc1768_unmount_command: self.configLpc1768UnmountCommand(),
                        lpc1768_preflashreset: self.configLpc1768ResetBeforeFlash(),
                        marlinbft_waitafterconnect: self.configMarlinBftWaitAfterConnect(),
                        marlinbft_timeout: self.configMarlinBftTimeout(),
                        marlinbft_progresslogging: self.configMarlinBftProgressLogging(),
                        enable_preflash_commandline: self.configEnablePreflashCommandline(),
                        preflash_commandline: self.configPreflashCommandline(),
                        enable_postflash_commandline: self.configEnablePostflashCommandline(),
                        postflash_commandline: self.configPostflashCommandline(),
                        postflash_delay: self.configPostflashDelay(),
                        preflash_delay: self.configPreflashDelay(),
                        postflash_gcode: self.configPostflashGcode(),
                        preflash_gcode: self.configPreflashGcode(),
                        enable_postflash_delay: self.configEnablePostflashDelay(),
                        enable_preflash_delay: self.configEnablePreflashDelay(),
                        enable_postflash_gcode: self.configEnablePostflashGcode(),
                        enable_preflash_gcode: self.configEnablePreflashGcode(),
                        disable_bootloadercheck: self.configDisableBootloaderCheck(),
                        save_url: self.configSaveUrl(),
                        disable_filefilter: self.configDisableFileFilter(),
                        last_url: lastUrl,
                    }
                }
            };
            self.settingsViewModel.saveData(data).done(function () {
                self.configurationDialog.modal("hide");
                self.alertMessage(undefined);
                self.showAlert(false);
                self.saving(false);
                self.showAdvancedConfig(false);
                self.showPostflashConfig(false);
                self.showPluginOptions(false);
            });
        };

        self._saveLastUrl = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        last_url: self.firmwareFileURL(),
                    }
                }
            };
            self.settingsViewModel.saveData(data);
        }

        self.onConfigHidden = function() {
            self.avrdudePathBroken(false);
            self.avrdudePathOk(false);
            self.avrdudePathText("");
            self.bossacPathBroken(false);
            self.bossacPathOk(false);
            self.bossacPathText("");
            self.showAdvancedConfig(false);
            self.showPostflashConfig(false);
            self.showPluginOptions(false);
        };

        self.testAvrdudePath = function() {
            var filePathRegEx_Linux = new RegExp("^(\/[^\0/]+)+$");
            var filePathRegEx_Windows = new RegExp("^[A-z]\:\\\\.+.exe$");

            if ( !filePathRegEx_Linux.test(self.configAvrdudePath()) && !filePathRegEx_Windows.test(self.configAvrdudePath()) ) {
                self.avrdudePathText(gettext("The path is not valid"));
                self.avrdudePathOk(false);
                self.avrdudePathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configAvrdudePath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.avrdudePathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.avrdudePathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.avrdudePathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.avrdudePathText(gettext("The path is valid"));
                        }
                        self.avrdudePathOk(response.result);
                        self.avrdudePathBroken(!response.result);
                    }
                })
            }
        };

        self.resetAvrdudeCommandLine = function() {
            self.configAvrdudeCommandLine("{avrdude} -v -q -p {mcu} -c {programmer} -P {port} -D -C {conffile} -b {baudrate} {disableverify} -U flash:w:{firmware}:i");
        };

        self.testBossacPath = function() {
            var filePathRegEx_Linux = new RegExp("^(\/[^\0/]+)+$");
            var filePathRegEx_Windows = new RegExp("^[A-z]\:\\\\.+.exe$");

            if ( !filePathRegEx_Linux.test(self.configBossacPath()) && !filePathRegEx_Windows.test(self.configBossacPath()) ) {
                self.bossacPathText(gettext("The path is not valid"));
                self.bossacPathOk(false);
                self.bossacPathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configBossacPath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.bossacPathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.bossacPathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.bossacPathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.bossacPathText(gettext("The path is valid"));
                        }
                        self.bossacPathOk(response.result);
                        self.bossacPathBroken(!response.result);
                    }
                })
            }
        };

        self.resetBossacCommandLine = function() {
            self.configBossacCommandLine("{bossac} -i -p {port} -U true -e -w {disableverify} -b {firmware} -R");
        };

        self.testDfuPath = function() {
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configDfuPath())) {
                self.dfuPathText(gettext("The path is not valid"));
                self.dfuPathOk(false);
                self.dfuPathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configDfuPath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.dfuPathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.dfuPathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.dfuPathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.dfuPathText(gettext("The path is valid"));
                        }
                        self.dfuPathOk(response.result);
                        self.dfuPathBroken(!response.result);
                    }
                })
            }
        };

        self.resetDfuCommandLine = function() {
            self.configDfuCommandLine("sudo {dfuprogrammer} {mcu} flash {firmware} --debug-level 10 --force");
        };

        self.resetDfuEraseCommandLine = function() {
            self.configDfuEraseCommandLine("sudo {dfuprogrammer} {mcu} erase --debug-level 10");
        };

        self.testStm32flashPath = function() {
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configStm32flashPath())) {
                self.stm32flashPathText(gettext("The path is not valid"));
                self.stm32flashPathOk(false);
                self.stm32flashPathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configStm32flashPath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.stm32flashPathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.stm32flashPathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.stm32flashPathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.stm32flashPathText(gettext("The path is valid"));
                        }
                        self.stm32flashPathOk(response.result);
                        self.stm32flashPathBroken(!response.result);
                    }
                })
            }
        };

        self.testAvrdudeConf = function() {
            $.ajax({
                url: API_BASEURL + "util/test",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "path",
                    path: self.configAvrdudeConfigFile(),
                    check_type: "file",
                    check_access: "r"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (!response.result) {
                        if (!response.exists) {
                            self.avrdudeConfPathText(gettext("The path doesn't exist"));
                        } else if (!response.typeok) {
                            self.avrdudeConfPathText(gettext("The path is not a file"));
                        } else if (!response.access) {
                            self.avrdudeConfPathText(gettext("The path is not readable"));
                        }
                    } else {
                        self.avrdudeConfPathText(gettext("The path is valid"));
                    }
                    self.avrdudeConfPathOk(response.result);
                    self.avrdudeConfPathBroken(!response.result);
                }
            })
        };

        self.testLpc1768Path = function() {
            $.ajax({
                url: API_BASEURL + "util/test",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "path",
                    path: self.configLpc1768Path(),
                    check_type: "dir",
                    check_writable_dir: "true"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (!response.result) {
                        if (!response.exists) {
                            self.lpc1768PathText(gettext("The path doesn't exist"));
                        } else if (!response.typeok) {
                            self.lpc1768PathText(gettext("The path is not a folder"));
                        } else if (!response.access) {
                            self.lpc1768PathText(gettext("The path is not writeable"));
                        }
                    } else {
                        self.lpc1768PathText(gettext("The path is valid"));
                    }
                    self.lpc1768PathOk(response.result);
                    self.lpc1768PathBroken(!response.result);
                }
            })
        };

        self.resetLpc1768UnmountCommand = function() {
            self.configLpc1768UnmountCommand("sudo umount {mountpoint}");
        }

        self.onSettingsShown = function() {
            self.inSettingsDialog = true;
        };

        self.onSettingsHidden = function() {
            self.inSettingsDialog = false;
            self.showAlert(false);
        };

        // Popup Messages

        self.showPopup = function(message_type, title, text){
            if (self.popup !== undefined){
                self.closePopup();
            }
            self.popup = new PNotify({
                title: gettext(title),
                text: text,
                type: message_type,
                hide: false
            });
        };

        self.closePopup = function() {
            if (self.popup !== undefined) {
                self.popup.remove();
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel", "printerStateViewModel", "accessViewModel"],
        ["#settings_plugin_firmwareupdater", "#navbar_plugin_firmwareupdater"]
    ]);
});
