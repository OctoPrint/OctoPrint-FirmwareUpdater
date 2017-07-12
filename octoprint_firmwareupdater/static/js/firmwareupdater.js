$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];

        self.configPathAvrdude = ko.observable();
        self.configConfAvrdude = ko.observable();

        self.flashPort = ko.observable(undefined);
        self.hexFileName = ko.observable(undefined);
        self.hexFileURL = ko.observable(undefined);

        self.alertMessage = ko.observable("");
        self.alertType = ko.observable("alert-warning");
        self.showAlert = ko.observable(false);
        self.missingParamToFlash = ko.observable(false);
        self.progressBarText = ko.observable();
        self.isBusy = ko.observable(false);

        self.pathBroken = ko.observable(false);
        self.pathOk = ko.observable(false);
        self.pathText = ko.observable();
        self.pathHelpVisible = ko.computed(function() {
            return self.pathBroken() || self.pathOk();
        });

        self.confBroken = ko.observable(false);
        self.confOk = ko.observable(false);
        self.confText = ko.observable();
        self.confHelpVisible = ko.computed(function() {
            return self.pathBroken() || self.pathOk();
        });

        self.selectHexPath = undefined;
        self.configurationDialog = undefined;

        self.inSettingsDialog = false;

        self.connection.selectedPort.subscribe(function(value) {
            if (value === undefined) return;
            self.flashPort(value);
        });

        self.onStartup = function() {
            self.selectHexPath = $("#settings_firmwareupdater_selectHexPath");
            self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");

            self.selectHexPath.fileupload({
                dataType: "hex",
                maxNumberOfFiles: 1,
                autoUpload: false,
                add: function(e, data) {
                    if (data.files.length === 0) {
                        return false;
                    }
                    self.hexData = data;
                    self.hexFileName(data.files[0].name);
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

            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                alert = gettext("The Avrdude path is not configured.");
            }

            if (!self.flashPort()) {
                alert = gettext("The printer port is not selected.");
            }

            if (source === "file" && !self.hexFileName()) {
                alert = gettext("Hex file path is not specified");
            } else if (source === "url" && !self.hexFileURL()) {
                alert = gettext("Hex file URL is not specified");
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
                    url: self.hexFileURL()
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
                    case "error": {
                        message = gettext("Unknown error");

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
                        self.hexFileName(undefined);
                        self.hexFileURL(undefined);

                        break;
                    }
                    case "success": {
                        self.showPopup("success", gettext("Flashing successful"), "");
                        self.isBusy(false);
                        self.showAlert(false);
                        self.hexFileName(undefined);
                        self.hexFileURL(undefined);
                        break;
                    }
                    case "progress": {
                        if (data.subtype) {
                            switch (data.subtype) {
                                case "disconnecting": {
                                    message = gettext("Disconnecting printer...");
                                    break;
                                }
                                case "starting": {
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
            self.configPathAvrdude(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path());
            self.configurationDialog.modal();
        };

        self.onConfigClose = function() {
            self._saveAvrdudePaths();
            self.configurationDialog.modal("hide");
            self.onConfigHidden();
            if (self.configPathAvrdude()) {
                self.showAlert(false);
            }
        };

        self._saveAvrdudePaths = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        avrdude_path: self.configPathAvrdude(),
                        avrdude_conf: self.configConfAvrdude()
                    }
                }
            };
            self.settingsViewModel.saveData(data);
        };

        self.onConfigHidden = function() {
            self.pathBroken(false);
            self.pathOk(false);
            self.pathText("");
        };

        self.testAvrdudePath = function() {
            $.ajax({
                url: API_BASEURL + "util/test",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "path",
                    path: self.configPathAvrdude(),
                    check_type: "file",
                    check_access: "x"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (!response.result) {
                        if (!response.exists) {
                            self.pathText(gettext("The path doesn't exist"));
                        } else if (!response.typeok) {
                            self.pathText(gettext("The path is not a file"));
                        } else if (!response.access) {
                            self.pathText(gettext("The path is not an executable"));
                        }
                    } else {
                        self.pathText(gettext("The path is valid"));
                    }
                    self.pathOk(response.result);
                    self.pathBroken(!response.result);
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
                    path: self.configConfAvrdude(),
                    check_type: "file",
                    check_access: "r"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (!response.result) {
                        if (!response.exists) {
                            self.confText(gettext("The path doesn't exist"));
                        } else if (!response.typeok) {
                            self.confText(gettext("The path is not a file"));
                        } else if (!response.access) {
                            self.confText(gettext("The path is not readable"));
                        }
                    } else {
                        self.confText(gettext("The path is valid"));
                    }
                    self.confOk(response.result);
                    self.confBroken(!response.result);
                }
            })
        };

        self.isReadyToFlashFromFile = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.connection.selectedPort()) {
                return false;
            }
            if (!self.hexFileName()) {
                return false;
            }
            self.showAlert(false);
            return true;
        };

        self.isReadyToFlashFromURL = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.connection.selectedPort()) {
                return false;
            }
            if (!self.hexFileURL()) {
                return false;
            }
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
