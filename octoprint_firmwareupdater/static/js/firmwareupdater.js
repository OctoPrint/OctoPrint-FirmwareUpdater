$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];

        self.configPathAvrdude = ko.observable();
        self.hexFileName = ko.observable(undefined);
        self.hexFileURL = ko.observable(undefined);

        self.alertMessage = ko.observable("");
        self.alertType = ko.observable("alert-warning");
        self.showAlert = ko.observable(false);
        self.missingParamToFlash = ko.observable(false);
        self.progressBarText = ko.observable();
        self.isBusy = ko.observable(false);
        self.updateAvailable = ko.observable(false);

        self.pathBroken = ko.observable(false);
        self.pathOk = ko.observable(false);
        self.pathText = ko.observable();
        self.pathHelpVisible = ko.computed(function() {
            return self.pathBroken() || self.pathOk();
        });

        self.inSettingsDialog = false;

        self.selectHexPath = $("#settings_firmwareupdater_selectHexPath");
        self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");

        self.selectHexPath.fileupload({
            dataType: "hex",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function(e, data) {
                if (data.files.length == 0) {
                    return false;
                }
                self.hexData = data;
                self.hexFileName(data.files[0].name);
            }
        })

        self.startFlashFromFile = function() {
            if (!self.loginState.isAdmin()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Administrator privileges are needed to flash firmware."));
                self.showAlert(true);
                return false;
            }
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showAlert(true);
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Avrdude path not configured"));
                self.showAlert(true);
                return false;
            }
            if (!self.hexFileName()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Hex file path not specified"));
                self.showAlert(true);
                return false;
            }
            if (!self.connection.selectedPort()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Port not selected"));
                self.showAlert(true);
                return false;
            }

            self.progressBarText("Flashing firmware...");
            self.isBusy(true);
            self.showAlert(false);

            var form = {
                selected_port: self.connection.selectedPort()
            };

            self.hexData.formData = form;
            self.hexData.submit();
        }

        self.startFlashFromURL = function() {
            if (!self.loginState.isAdmin()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Administrator privileges are needed to flash firmware."));
                self.showAlert(true);
                return false;
            }
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showAlert(true);
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Avrdude path not configured"));
                self.showAlert(true);
                return false;
            }
            if (!self.hexFileURL()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Hex file URL not specified"));
                self.showAlert(true);
                return false;
            }
            if (!self.connection.selectedPort()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Port not selected"));
                self.showAlert(true);
                return false;
            }

            self.isBusy(true);
            self.showAlert(false);
            self.progressBarText("Flashing firmware...");

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/flashFirmwareWithURL",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.connection.selectedPort(),
                    hex_url: self.hexFileURL()
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }

        self.checkForUpdates = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showAlert(true);
                return false;
            }

            if (!self.connection.selectedPort()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Port not selected"));
                self.showAlert(true);
                return false;
            }

            self.isBusy(true);
            self.showAlert(false);

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/checkForUpdates",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.connection.selectedPort(),
                }),
                contentType: "application/json; charset=UTF-8"
            });
        }

        self.flashUpdate = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                self.alertType("alert-warning")
                self.alertMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showAlert(true);
                return false;
            }

            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Avrdude path not configured"));
                self.showAlert(true);
                return false;
            }

            if (!self.connection.selectedPort()) {
                self.alertType("alert-warning")
                self.alertMessage(gettext("Port not selected"));
                self.showAlert(true);
                return false;
            }

            self.isBusy(true);
            self.showAlert(false);
            self.progressBarText("Flashing firmware...");

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/flashUpdate",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.connection.selectedPort()
                }),
                contentType: "application/json; charset=UTF-8"
            });
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "firmwareupdater") {
                return;
            }
            if (data.type == "status" && data.status_type == "check_update_status") {
                if (data.status_value == "progress") {
                    self.progressBarText(data.status_description);
                    return;
                }
                if (data.status_value == "update_available") {
                    if (!self.inSettingsDialog) {
                        self.showUpdateAvailablePopup(data.status_description);
                    }
                    self.updateAvailable(true);
                    self.isBusy(false);
                    return;
                }
                if (data.status_value == "up_to_date") {
                    self.updateAvailable(false);
                    self.isBusy(false);
                    self.showAlert(false);
                    if (self.inSettingsDialog) {
                        self.alertType("alert-success");
                        self.alertMessage(data.status_description);
                        self.showAlert(true);
                    }
                    return;
                }
                if (data.status_value == "error") {
                    self.updateAvailable(false);
                    self.isBusy(false);
                    self.alertType("alert-danger");
                    self.alertMessage(data.status_description);
                    self.showAlert(true);
                    return;
                }
            }
            if (data.type == "status" && data.status_type == "flashing_status") {
                if (data.status_value == "progress") {
                    self.progressBarText(data.status_description);
                } else if (data.status_value == "successful") {
                    self.showPopup("success", "Flashing Successful", "");
                    self.isBusy(false);
                    self.showAlert(false);
                } else if (data.status_value == "error") {
                    self.showPopup("error", "Flashing Failed", data.status_description);
                    self.isBusy(false);
                    self.showAlert(false);
                }
            }
        }

        self.showPluginConfig = function() {
            self.configPathAvrdude(self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path());
            self.configurationDialog.modal();
        }

        self.onConfigClose = function() {
            self._saveAvrdudePath();
            self.configurationDialog.modal("hide");
            self.onConfigHidden();
            if (self.configPathAvrdude()) {
                self.showAlert(false);
            }
        }

        self._saveAvrdudePath = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        avrdude_path: self.configPathAvrdude(),
                    }
                }
            }
            self.settingsViewModel.saveData(data);
        }

        self.onConfigHidden = function() {
            self.pathBroken(false);
            self.pathOk(false);
            self.pathText("");
        }

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
        }

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
        }

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
        }

        self.isReadyToCheck = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                return false;
            }
            if (!self.connection.selectedPort()) {
                return false;
            }
            return true;
        }

        self.isReadyToUpdate = function() {
            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                return false;
            }
            if (!self.settingsViewModel.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.connection.selectedPort()) {
                return false;
            }
            return true;
        }

        self.onSettingsShown = function() {
            self.inSettingsDialog = true;
        }

        self.onSettingsHidden = function() {
            self.inSettingsDialog = false;
        }

        // Popup Messages

        self.showUpdateAvailablePopup = function(new_fw_version) {
            // Hack to remove automatically added Cancel button
            // See https://github.com/sciactive/pnotify/issues/141
            PNotify.prototype.options.confirm.buttons = [];
            self.updateAvailablePopup = new PNotify({
                title: gettext('Firmware Update Available'),
                text: gettext('Version ') + new_fw_version,
                icon: true,
                hide: false,
                type: 'success',
                confirm: {
                    confirm: true,
                    buttons: [{
                        text: 'Update Firmware',
                        addClass: 'btn-block btn-success',
                        promptTrigger: true,
                        click: function(notice, value){
                            notice.remove();
                            self.flashUpdate();
                        }
                    }]
                },
                buttons: {
                    closer: true,
                    sticker: false,
                },
                history: {
                    history: false
                }
            });
            if (!self.isReadyToUpdate()) {
                self.updateAvailablePopup.get().confirm.confirm(false);
            };
        };

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
        }

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
