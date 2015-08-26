$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];

        self.configPathAvrdude = ko.observable();
        self.configPathAvrdudeConfig = ko.observable();

        self.hexFileName = ko.observable(undefined);
        self.hexFileURL = ko.observable(undefined);
        self.selectedPort = ko.observable(undefined);

        self.warningMessage = ko.observable(undefined);
        self.showWarning = ko.observable(false);
        self.infoMessage = ko.observable(undefined);
        self.showInfo = ko.observable(false);

        self.statusPercentage = ko.observable(0);
        self.statusString = ko.observable("0%");

        self.pathBroken = ko.observable(false);
        self.pathOk = ko.observable(false);
        self.pathText = ko.observable();
        self.pathHelpVisible = ko.computed(function() {
            return self.pathBroken() || self.pathOk();
        });

        self.updateAvailable = ko.observable(false);

        self.checkAfterConnect = ko.observable(true);
        self.checkAfterConnect.subscribe(function(newValue){
            self.onCheckAfterConnect(newValue);
        }, self);

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

        self.onStartupComplete = function() {
            self.checkAfterConnect(self.settings.settings.plugins.firmwareupdater.check_after_connect());
        }

        self.startFlashFromFile = function() {
            if (self.printerState.isPrinting()){
                self.warningMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showWarning(true);
                return false;
            }

            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                self.warningMessage(gettext("Avrdude path not configured"));
                self.showWarning(true);
                return false;
            }

            if (!self.hexFileURL() && !self.hexFileName()) {
                self.warningMessage(gettext("Hex file not selected"));
                self.showWarning(true);
                return false;
            }

            if (!self.selectedPort()) {
                self.warningMessage(gettext("Port not selected"));
                self.showWarning(true);
                return false;
            }

            self.showWarning(false);
            self.infoMessage("Printer will be disconnected.")
            //self.showInfo(true);

            var form = {
                selected_port: self.selectedPort()
            };

            self.hexData.formData = form;
            self.hexData.submit();
        }

        self.startFlashFromURL = function() {
            if (self.printerState.isPrinting()){
                self.warningMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showWarning(true);
                return false;
            }

            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                self.warningMessage(gettext("Avrdude path not configured"));
                self.showWarning(true);
                return false;
            }

            if (!self.hexFileURL()) {
                self.warningMessage(gettext("Hex file URL not selected"));
                self.showWarning(true);
                return false;
            }

            if (!self.selectedPort()) {
                self.warningMessage(gettext("Port not selected"));
                self.showWarning(true);
                return false;
            }

            self.showWarning(false);
            self.infoMessage("Printer will be disconnected.")
            //self.showInfo(true);

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/flashFirmwareWithURL",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.selectedPort(),
                    hex_url: self.hexFileURL()
                }),
                contentType: "application/json; charset=UTF-8"
            })
        }

        self.checkForUpdates = function() {
            if (self.printerState.isPrinting()){
                self.warningMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showWarning(true);
                return false;
            }

            if (!self.selectedPort()) {
                self.warningMessage(gettext("Port not selected"));
                self.showWarning(true);
                return false;
            }

            self.showWarning(false);
            self.infoMessage("Printer will be disconnected.")
            //self.showInfo(true);

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/checkForUpdates",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.selectedPort()
                }),
                contentType: "application/json; charset=UTF-8"
            });
        }

        self.flashUpdate = function() {
            if (self.printerState.isPrinting()){
                self.warningMessage(gettext("Printer is printing. Please wait for the print to be finished."));
                self.showWarning(true);
                return false;
            }

            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                self.warningMessage(gettext("Avrdude path not configured"));
                self.showWarning(true);
                return false;
            }

            if (!self.selectedPort()) {
                self.warningMessage(gettext("Port not selected"));
                self.showWarning(true);
                return false;
            }

            self.showWarning(false);
            self.infoMessage("Printer will be disconnected.")
            //self.showInfo(true);

            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/flashUpdate",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    selected_port: self.selectedPort()
                }),
                contentType: "application/json; charset=UTF-8"
            });
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "firmwareupdater") {
                return;
            }
            if (data.type == "status" && data.status_type == "update_available") {
                if (data.status_value) {
                    self.updateAvailable(true);
                } else {
                    self.updateAvailable(false);
                }
                return;
            }
            if (data.type == "message") {
                self._showPopup({
                    title: gettext(data.title),
                    text: data.text,
                    type: data.message_type,
                    hide: false
                    },
                    data.replaceable
                );
            }
        }

        self.showPluginConfig = function() {
            self.configPathAvrdude(self.settings.settings.plugins.firmwareupdater.avrdude_path());
            self.configurationDialog.modal();
        }

        self._savePluginSettings = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        avrdude_path: self.configPathAvrdude(),
                        check_after_connect: self.checkAfterConnect()
                    }
                }
            }
            self.settings.saveData(data);
        }

        self.onConfigClose = function() {
            self._savePluginSettings();
            self.configurationDialog.modal("hide");
            self.onConfigHidden();
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
            if (self.printerState.isPrinting()){
                return false;
            }
            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.selectedPort()) {
                return false;
            }
            if (!self.hexFileName()) {
                return false;
            }
            return true;
        }

        self.isReadyToFlashFromURL = function() {
            if (self.printerState.isPrinting()){
                return false;
            }
            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.selectedPort()) {
                return false;
            }
            if (!self.hexFileURL()) {
                return false;
            }
            return true;
        }

        self.isReadyToCheck = function() {
            if (self.printerState.isPrinting()){
                return false;
            }
            if (!self.selectedPort()) {
                return false;
            }
            return true;
        }

        self.isReadyToUpdate = function() {
            if (self.printerState.isPrinting()){
                return false;
            }
            if (!self.settings.settings.plugins.firmwareupdater.avrdude_path()) {
                return false;
            }
            if (!self.selectedPort()) {
                return false;
            }
            return true;
        }

        self.onCheckAfterConnect = function(value) {
            self._savePluginSettings();
        }

        // Popup Messages

        self._showPopup = function(options, replaceable) {
            if (self.popup !== undefined && self.popup_replaceable){
                self._closePopup();
            }
            self.popup_replaceable = replaceable;
            self.popup = new PNotify(options);
        };

        self._closePopup = function() {
            if (self.popup !== undefined) {
                self.popup.remove();
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel", "printerStateViewModel"],
        [document.getElementById("settings_plugin_firmwareupdater"), document.getElementById("sidebar_plugin_firmwareupdater")]
    ]);
});
