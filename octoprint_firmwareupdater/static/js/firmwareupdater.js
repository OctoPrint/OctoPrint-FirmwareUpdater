$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.hexFileName = ko.observable();
        self.hexFileURL = ko.observable();

        self.flashFirmware = function() {
            $.ajax({
                url: PLUGIN_BASEURL + "firmwareupdater/uploadHexFile",
                type: "POST",
                data: {hexFileName: self.hexFileName(),
                       hexFileURL: self.hexFileURL()}
            });
        };
    };

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        [],
        ["#settings_plugin_firmwareupdater"]
    ]);
});
