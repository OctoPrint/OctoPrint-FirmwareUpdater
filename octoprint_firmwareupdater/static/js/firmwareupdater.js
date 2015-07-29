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

        self.pathBroken = ko.observable(false);
        self.pathOk = ko.observable(false);
        self.pathText = ko.observable();
        self.pathHelpVisible = ko.computed(function() {
            return self.pathBroken() || self.pathOk();
        });

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
            if (!self.config_path_avrdude()) {
                self._showPopup({
                    title: gettext("Avrdude path not configured"),
                    hide: false,
                    type: "error"
                });
                return false;
            }
            if (!self.selected_port()) {
                self._showPopup({
                    title: gettext("Port not selected"),
                    hide: false,
                    type: "error"
                });
                return false;
            }
            if (!self.hexFileURL() && !self.hexFileName()) {
                self._showPopup({
                    title: gettext("Hex file not selected"),
                    hide: false,
                    type: "error"
                });
                return false;
            }

            self._showPopup({
                title: gettext("Starting to flash firmware"),
                hide: false,
                type: "warning"
            });

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

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "firmwareupdater") {
                return;
            }
            self._showPopup({
                title: gettext(data.title),
                text: data.text,
                hide: false,
                type: data.type
            });
        }

        self.showPluginSettings = function() {
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
            self.settings.saveData(data, function() { self.configurationDialog.modal("hide"); self._copyConfig(); self.onConfigHidden(); });
        }

        self.onConfigHidden = function() {
            self.pathBroken(false);
            self.pathOk(false);
            self.pathText("");
        }

        self._copyConfig = function() {
            self.config_path_avrdude(self.settings.settings.plugins.firmwareupdater.path_avrdude());
            self.config_path_avrdudeconfig(self.settings.settings.plugins.firmwareupdater.path_avrdudeconfig());
        }

        self.testAvrdudePath = function() {
            $.ajax({
                url: API_BASEURL + "util/test",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "path",
                    path: self.config_path_avrdude(),
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

        self.onAfterBinding = function() {
            self._copyConfig();
        }

        // Status Messages

        self._showPopup = function(options, eventListeners) {
            self._closePopup();
            self.popup = new PNotify(options);

            if (eventListeners) {
                var popupObj = self.popup.get();
                _.each(eventListeners, function(value, key) {
                    popupObj.on(key, value);
                })
            }
        };

        self._updatePopup = function(options) {
            if (self.popup === undefined) {
                self._showPopup(options);
            } else {
                self.popup.update(options);
            }
        };

        self._closePopup = function() {
            if (self.popup !== undefined) {
                self.popup.remove();
            }
        };
    }

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel"],
        document.getElementById("settings_plugin_firmwareupdater")
    ]);
});
