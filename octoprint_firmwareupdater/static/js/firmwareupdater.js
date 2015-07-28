$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        self.hexFileName = ko.observable();
        self.hexFileURL = ko.observable();

        self.uploadFirmware = $("#settings-firmwareupdater-upload");
        self.flashFirmware = $("#settings-firmwareupdater-start");

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
        })
    };

    OCTOPRINT_VIEWMODELS.push([
        FirmwareUpdaterViewModel,
        [],
        ["#settings_plugin_firmwareupdater"]
    ]);
});
