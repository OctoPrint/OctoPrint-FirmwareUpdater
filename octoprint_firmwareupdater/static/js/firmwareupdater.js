$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];

        // General settings
        self.configProcessor = ko.observable();
        self.showAdvancedConfig = ko.observable(false);
        self.showAvrdudeConfig = ko.observable(false);
        self.showBossacConfig = ko.observable(false);
        self.configEnablePostflashGcode = ko.observable();
        self.configPostflashGcode = ko.observable();

        // Config settings for avrdude
        self.configAvrdudePath = ko.observable();
        self.configAvrdudeConfigFile = ko.observable(); 
        self.configAvrdudeProgrammer = ko.observable();
        self.configAvrdudeBaudRate = ko.observable();
        self.configAvrdudeDisableVerification = ko.observable();
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
        self.bossacPathBroken = ko.observable(false);
        self.bossacPathOk = ko.observable(false);
        self.bossacPathText = ko.observable();
        self.bossacPathHelpVisible = ko.computed(function() {
            return self.bossacPathBroken() || self.bossacPathOk();
        });

        self.flashPort = ko.observable(undefined);
        self.fileExtension = ko.observable("")

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

         self.configProcessor.subscribe(function(value) {
            if (!value) {
                value = self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu();
            }
            if(value == 'sam3x8e') {
                self.showBossacConfig(true);
                self.showAvrdudeConfig(false);
                self.firmwareFileName(undefined)
                self.fileExtension(".bin")
            } else {
                self.showBossacConfig(false);
                self.showAvrdudeConfig(true);
                self.firmwareFileName(undefined)
                self.fileExtension(".hex")
            }
         });

        self.onStartup = function() {
            self.selectFilePath = $("#settings_firmwareupdater_selectFilePath");
            self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");

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

            if (self.showAvrdudeConfig() && !self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                alert = gettext("The avrdude path is not configured.");
            }

            if (self.showBossacConfig() && !self.settingsViewModel.settings.plugins.firmwareupdater.bossac_path()) {
                alert = gettext("The bossac path is not configured.");
            }

            if (!self.flashPort()) {
                alert = gettext("The printer port is not selected.");
            }

            if (source === "file" && !self.firmwareFileName()) {
                alert = gettext("Firmware file path is not specified");
            } else if (source === "url" && !self.firmwareFileURL()) {
                alert = gettext("Firmware file URL is not specified");
            }

            if (alert !== undefined) {
                self.alertType("alert-warning");
                self.alertMessage(alert);
                self.showAlert(true);
                return false;
            }

            return true;
        };

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
                                    message = gettext("Flash method is not fully configured.");
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
                        self.firmwareFileName(undefined);
                        self.firmwareFileURL(undefined);

                        break;
                    }
                    case "success": {
                        self.showPopup("success", gettext("Flashing successful"), "");
                        self.isBusy(false);
                        self.showAlert(false);
                        self.firmwareFileName(undefined);
                        self.firmwareFileURL(undefined);
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
                                case "verifying": {
                                    message = gettext("Verifying memory...");
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
            self.configAvrdudePath(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path());
            self.configAvrdudeConfigFile(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_conf());
            self.configProcessor(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu());
            self.configAvrdudeProgrammer(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_programmer());
            self.configAvrdudeBaudRate(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_baudrate());
            if(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_disableverify() != 'false') {
                self.configAvrdudeDisableVerification(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_disableverify());
            }

            self.configBossacPath(self.settingsViewModel.settings.plugins.firmwareupdater.bossac_path());
            
            if(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode() != 'false') {
                self.configEnablePostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.enable_postflash_gcode());
            }
            self.configPostflashGcode(self.settingsViewModel.settings.plugins.firmwareupdater.postflash_gcode());


            self.configurationDialog.modal();
        };

        self.onConfigClose = function() {
            self._saveConfig();
            self.configurationDialog.modal("hide");
            self.onConfigHidden();
            if (self.configAvrdudePath()) {
                self.showAlert(false);
            }
        };

        self._saveConfig = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        avrdude_path: self.configAvrdudePath(),
                        avrdude_conf: self.configAvrdudeConfigFile(),
                        avrdude_avrmcu: self.configProcessor(),
                        avrdude_programmer: self.configAvrdudeProgrammer(),
                        avrdude_baudrate: self.configAvrdudeBaudRate(),
                        avrdude_disableverify: self.configAvrdudeDisableVerification(),
                        bossac_path: self.configBossacPath(),
                        postflash_gcode: self.configPostflashGcode(),
                        enable_postflash_gcode: self.configEnablePostflashGcode()
                    }
                }
            };
            if(self.configProcessor() == 'sam3x8e') {
                self.fileExtension(".bin")
            } else {
                self.fileExtension(".hex")
            }
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
        };

        self.testBossacPath = function() {
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

        self.isReadyToFlashFromFile = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.fileFlashButtonText(gettext("Unable to flash: Printer is busy"));
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu()) {
                self.fileFlashButtonText(gettext("Unable to flash: Processor type not selected"));
                return false;
            }
            if (self.showAvrdudeConfig() && !self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                self.fileFlashButtonText(gettext("Unable to flash: avrdude path is not set"));
                return false;
            }
            if (self.showBossacConfig() && !self.settingsViewModel.settings.plugins.firmwareupdater.bossac_path()) {
                self.fileFlashButtonText(gettext("Unable to flash: bossac path is not set"));
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_programmer()) {
                self.fileFlashButtonText(gettext("Unable to flash: Programmer type not selected"));
                return false;
            }
            if (!self.flashPort()) {
                self.fileFlashButtonText(gettext("Unable to flash: Port not selected"));
                return false;
            }
            if (!self.firmwareFileName()) {
                self.fileFlashButtonText(gettext("Unable to flash: Firmware file not selected"));
                return false;
            }
                self.fileFlashButtonText(gettext("Ready to flash from file"));
            self.showAlert(false);
            return true;
        };

        self.isReadyToFlashFromURL = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.urlFlashButtonText(gettext("Unable to flash: Printer is busy"));
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                self.urlFlashButtonText(gettext("Unable to flash: avrdude path is not set"));
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_avrmcu()) {
                self.urlFlashButtonText(gettext("Unable to flash: MCU type not selected"));
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_programmer()) {
                self.urlFlashButtonText(gettext("Unable to flash: Programmer type not selected"));
                return false;
            }
            if (!self.flashPort()) {
                self.urlFlashButtonText(gettext("Unable to flash: Port not selected"));
                return false;
            }
            if (!self.firmwareFileURL()) {
                self.urlFlashButtonText(gettext("Unable to flash: Firmware file URL not set"));
                return false;
            }
            self.urlFlashButtonText(gettext("Ready to flash from file"));
            self.showAlert(false);
            return true;
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
