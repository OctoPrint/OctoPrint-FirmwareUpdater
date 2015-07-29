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
                self.hexFileURL(undefined);
            }
        })


        self.startFlash = function() {
            if (!self.config_path_avrdude() || !self.selected_port()) {
                return false;
            }

            if (self.hexFileURL()) {
                $.ajax({
                    url: PLUGIN_BASEURL + "firmwareupdater/flashFirmwareWithURL",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        avrdude_path: self.config_path_avrdude(),
                        selected_port: self.selected_port(),
                        hex_url: self.hexFileURL()
                    }),
                    contentType: "application/json; charset=UTF-8"
                })

            } else if (self.hexFileName()) {
                var form = {
                    avrdude_path: self.config_path_avrdude(),
                    selected_port: self.selected_port()
                };

                self.hexData.formData = form;
                self.hexData.submit();
            }            
        }

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
