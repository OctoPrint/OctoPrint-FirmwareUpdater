$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];

        self.hexFileName = ko.observable();
        self.hexFileURL = ko.observable();
        self.config_path_avrdude = ko.observable();
        self.config_path_avrdudeconfig = ko.observable();

        self.uploadFirmware = $("#settings-firmwareupdater-upload");
        self.flashFirmware = $("#settings-firmwareupdater-start");

        self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");

        self.uploadFirmware.fileupload({
            dataType: "hex",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function(e, data) {
                if (data.files.length == 0) {
                    return false;
                }

                self.hexFileName(data.files[0].name);

                self.flashFirmware.unbind("click");
                self.flashFirmware.on("click", function() {
                    data.submit();
                });
            }
        });

        self.showPluginSettings = function() {
            self._copyConfig();
            self.configurationDialog.modal();
        };

        self.savePluginSettings = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        path_avrdude: self.config_path_avrdude(),
                        path_avrdudeconfig: self.config_path_avrdudeconfig()
                    }
                }
            };
            self.settings.saveData(data, function() { self.configurationDialog.modal("hide"); self._copyConfig(); });
        };

        self._copyConfig = function() {
            self.config_path_avrdude(self.settings.settings.plugins.firmwareupdater.path_avrdude());
            self.config_path_avrdudeconfig(self.settings.settings.plugins.firmwareupdater.path_avrdudeconfig());
        };

    };

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        ["settingsViewModel"],
        document.getElementById("settings_plugin_firmwareupdater")
    ]);
});
