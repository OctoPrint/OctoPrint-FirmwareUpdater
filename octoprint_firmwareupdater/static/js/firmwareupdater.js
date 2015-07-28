$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.settings = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];

        self.config_path_avrdude = ko.observable();
        self.config_path_avrdudeconfig = ko.observable();

        self.hexFileName = ko.observable(undefined);
        self.hexFileURL = ko.observable(undefined);
        self.selected_port = ko.observable(undefined);

        self.selectHexPath = $("#settings-firmwareupdater-selectHexPath");
        self.flashFirmware = $("#settings-firmwareupdater-start");

        self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationdialog");

        self.selectHexPath.fileupload({
            dataType: "hex",
            maxNumberOfFiles: 1,
            autoUpload: false,
            add: function(e, data) {
                if (data.files.length == 0) {
                    return false;
                }

                self.hexFileName(data.files[0].name);
                self.hexFileURL(undefined);

                self.flashFirmware.unbind("click");
                self.flashFirmware.on("click", function() {
                    if (!self.hexFileName() || !self.config_path_avrdude() || !self.selected_port()) {
                        return false;
                    }

                    var form = {
                        avrdude_path: self.config_path_avrdude(),
                        selected_port: self.selected_port()
                    };

                    data.formData = form;
                    data.submit();
                })
            }
        })

        self.showPluginSettings = function() {
            self._copyConfig();
            self.configurationDialog.modal();
        }

        self.savePluginSettings = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        path_avrdude: self.config_path_avrdude(),
                        path_avrdudeconfig: self.config_path_avrdudeconfig()
                    }
                }
            }
            self.settings.saveData(data, function() { self.configurationDialog.modal("hide"); self._copyConfig() });
        }

        self._copyConfig = function() {
            self.config_path_avrdude(self.settings.settings.plugins.firmwareupdater.path_avrdude());
            self.config_path_avrdudeconfig(self.settings.settings.plugins.firmwareupdater.path_avrdudeconfig());
        }
        
        self.onAfterBinding = function() {
            self._copyConfig();
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel"],
        document.getElementById("settings_plugin_firmwareupdater")
    ]);
});
