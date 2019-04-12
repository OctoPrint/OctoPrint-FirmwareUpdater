$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];

        // General settings
        self.configFlashMethod = ko.observable();
        self.showAdvancedConfig = ko.observable(false);
        self.showAvrdudeConfig = ko.observable(false);
        self.showBossacConfig = ko.observable(false);
        self.showLpc1768Config = ko.observable(false);
        self.showPostflashConfig = ko.observable(false);
        self.configEnablePostflashDelay = ko.observable();
        self.configPostflashDelay = ko.observable();
        self.configEnablePostflashGcode = ko.observable();
        self.configPostflashGcode = ko.observable();
        self.configDisableBootloaderCheck = ko.observable();

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

        self.lpc1768PathBroken = ko.observable(false);
        self.lpc1768PathOk = ko.observable(false);
        self.lpc1768PathText = ko.observable();
        self.lpc1768PathHelpVisible = ko.computed(function() {
            return self.lpc1768PathBroken() || self.lpc1768PathOk();
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

        self.selectFilePath = undefined;
        self.configurationDialog = undefined;

        self.inSettingsDialog = false;

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

        self.configFlashMethod.subscribe(function(value) {
            if(value == 'avrdude') {
                self.showAvrdudeConfig(true);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
            } else if(value == 'bossac') {
                self.showAvrdudeConfig(false);
                self.showBossacConfig(true);
                self.showLpc1768Config(false);
            } else if(value == 'lpc1768'){
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(true);
            } else {
                self.showAvrdudeConfig(false);
                self.showBossacConfig(false);
                self.showLpc1768Config(false);
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

            if (!self.flashPort()) {
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

            if (data.type === "status") {
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
                                case "already_flashing": {
                                    message = gettext("Already flashing.");
                                }
                            }
                        }

                        self.showPopup("error", gettext("Flashing failed"), message);
                        self.isBusy(false);
                        self.showAlert(false);
                        self.firmwareFileName("");
                        self.firmwareFileURL("");
                        break;
                    }
                    case "success": {
                        self.showPopup("success", gettext("Flashing successful"), "");
                        self.isBusy(false);
                        self.showAlert(false);
                        self.firmwareFileName("");
                        self.firmwareFileURL("");
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
            }
        };

        self.showPluginConfig = function() {
            // Load the general settings
            self.configFlashMethod(self.settingsViewModel.settings.plugins.firmwareupdater.flash_method());
            self.configPostflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_delay());
            self.configPostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_gcode());

            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_delay() != 'false') {
                self.configEnablePostflashDelay(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_delay());
            }
            
            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode() != 'false') {
                self.configEnablePostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode());
            }
            
            if(self.settingsViewModel.settings.plugins.firmwareupdater.disable_bootloadercheck() != 'false') {
                self.configDisableBootloaderCheck(self.settingsViewModel.settings.plugins.firmwareupdater.disable_bootloadercheck());
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
            
            // Load the lpc1768 settings
            self.configLpc1768Path(self.settingsViewModel.settings.plugins.firmwareupdater.lpc1768_path());
            
            self.configurationDialog.modal();
        };

        self.onConfigClose = function() {
            self._saveConfig();

            self.configurationDialog.modal("hide");
            self.alertMessage(undefined);
            self.showAlert(false);
        };

        self._saveConfig = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        flash_method: self.configFlashMethod(),
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
                        lpc1768_path: self.configLpc1768Path(),
                        postflash_delay: self.configPostflashDelay(),
                        postflash_gcode: self.configPostflashGcode(),
                        enable_postflash_delay: self.configEnablePostflashDelay(),
                        enable_postflash_gcode: self.configEnablePostflashGcode(),
                        disable_bootloadercheck: self.configDisableBootloaderCheck()
                    }
                }
            };
            self.settingsViewModel.saveData(data);
        };

        self.onConfigHidden = function() {
            self.avrdudePathBroken(false);
            self.avrdudePathOk(false);
            self.avrdudePathText("");
            self.bossacPathBroken(false);
            self.bossacPathOk(false);
            self.bossacPathText("");
        };

        self.testAvrdudePath = function() {
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configAvrdudePath())) {
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
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configBossacPath())) {
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
                    check_type: "path",
                    check_access: ["r", "w"],
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
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel", "printerStateViewModel"],
        [document.getElementById("settings_plugin_firmwareupdater")]
    ]);
});
