$(function() {
    function FirmwareUpdaterViewModel(parameters) {
        var self = this;

        // Parameters
        self.settingsViewModel = parameters[0];
        self.loginState = parameters[1];
        self.connection = parameters[2];
        self.printerState = parameters[3];
        self.access = parameters[4];
        
        // Observables for plugin options
        self.configShowNavbarIcon = ko.observable();                    // enable_navbar
        self.configProfilesEnabled = ko.observable();                   // enable_profiles
        self.configDisableFileFilter = ko.observable();
        
        // Observables for profiles
        self.selectedProfileIndex = ko.observable();                    // _selected_profile 
        self.profiles = ko.observableArray();                           // profiles
        self.configProfilesVisible = ko.observable();                   // Indicates if profiles should be displayed in the UI. Updated on load and settings save.
        self.configProfileName = ko.observable();

        // Observables for general profile settings
        self.configFlashMethod = ko.observable();                       // flash_method 
        self.configSaveUrl = ko.observable();                           // save_url
        self.configLastUrl = ko.observable();                           // last_url
        self.configDisableBootloaderCheck = ko.observable();            // disable_bootloadercheck

        // Observables for pre and post flash profile settings
        self.configNoAutoReconnect = ko.observable();
        self.configEnablePreflashDelay = ko.observable();
        self.configPreflashDelay = ko.observable();
        self.configEnablePostflashDelay = ko.observable();
        self.configPostflashDelay = ko.observable();
        self.configEnablePostflashGcode = ko.observable();
        self.configPostflashGcode = ko.observable();
        self.configEnablePreflashCommandline = ko.observable();
        self.configPreflashCommandline = ko.observable();
        self.configEnablePostflashCommandline = ko.observable();
        self.configPostflashCommandline = ko.observable();
        self.configEnablePreflashGcode = ko.observable();
        self.configPreflashGcode = ko.observable();

        // Observables for avrdude config settings
        self.configAvrdudeMcu = ko.observable();
        self.configAvrdudePath = ko.observable();
        self.configAvrdudeConfigFile = ko.observable();
        self.configAvrdudeProgrammer = ko.observable();
        self.configAvrdudeBaudRate = ko.observable();
        self.configAvrdudeDisableVerification = ko.observable();
        self.configAvrdudeCommandLine = ko.observable();

        // Observables for avrdude UI messages
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

        // Observables for bossac config settings
        self.configBossacPath = ko.observable();
        self.configBossacDisableVerification = ko.observable()
        self.configBossacCommandLine = ko.observable();

        // Observables for bossac UI messages
        self.bossacPathBroken = ko.observable(false);
        self.bossacPathOk = ko.observable(false);
        self.bossacPathText = ko.observable();
        self.bossacPathHelpVisible = ko.computed(function() {
            return self.bossacPathBroken() || self.bossacPathOk();
        });

        // Observables for lpc1768 config settings
        self.configLpc1768Path = ko.observable();
        self.configLpc1768ResetBeforeFlash = ko.observable();
        self.configLpc1768UnmountCommand = ko.observable();
        self.configLpc1768NoResetWait = ko.observable();
        self.configLpc1768NoRestartWait = ko.observable();

        // Observables for lpc1768 UI messages
        self.lpc1768PathBroken = ko.observable(false);
        self.lpc1768PathOk = ko.observable(false);
        self.lpc1768PathText = ko.observable();
        self.lpc1768PathHelpVisible = ko.computed(function() {
            return self.lpc1768PathBroken() || self.lpc1768PathOk();
        });

        // Observables for marlinbft config settings
        self.configMarlinBftWaitAfterConnect = ko.observable();
        self.configMarlinBftTimeout = ko.observable();
        self.configMarlinBftProgressLogging = ko.observable();
        self.configMarlinBftNoResetWait = ko.observable();
        self.configMarlinBftNoRestartWait = ko.observable();
        self.marlinbftHasCapability = ko.observable();
        self.marlinbftHasBinProto2Package = ko.observable();

        // Observables for dfu-programmer config settings
        self.configDfuMcu = ko.observable();
        self.configDfuPath = ko.observable();
        self.configDfuCommandLine = ko.observable();
        self.configDfuEraseCommandLine = ko.observable();

        // Observables for dfu-programmer UI messages
        self.dfuPathBroken = ko.observable(false);
        self.dfuPathOk = ko.observable(false);
        self.dfuPathText = ko.observable();
        self.dfuPathHelpVisible = ko.computed(function() {
            return self.dfuPathBroken() || self.dfuPathOk();
        });

        // Observables for stm32flash config settings
        self.configStm32flashPath = ko.observable();
        self.configStm32flashVerify = ko.observable();
        self.configStm32flashBoot0Pin = ko.observable();
        self.configStm32flashBoot0Low = ko.observable();
        self.configStm32flashResetPin = ko.observable();
        self.configStm32flashResetLow = ko.observable();
        self.configStm32flashExecute = ko.observable();
        self.configStm32flashExecuteAddress = ko.observable();
        self.configStm32flashReset = ko.observable();

        // Observables for stm32flash UI messages
        self.stm32flashPathBroken = ko.observable(false);
        self.stm32flashPathOk = ko.observable(false);
        self.stm32flashPathText = ko.observable();
        self.stm32flashPathHelpVisible = ko.computed(function() {
            return self.stm32flashPathBroken() || self.stm32flashPathOk();
        });

        // Observables to control which settings to show
        self.showAvrdudeConfig = ko.observable(false);
        self.showBossacConfig = ko.observable(false);
        self.showLpc1768Config = ko.observable(false);
        self.showDfuConfig = ko.observable(false);
        self.showStm32flashConfig = ko.observable(false);
        self.showMarlinBftConfig = ko.observable(false);

        // Observables for UI elements
        self.flashPort = ko.observable(undefined);
        self.pluginVersion = ko.observable(undefined);
        self.firmwareFileName = ko.observable(undefined);
        self.firmwareFileURL = ko.observable(undefined);
        self.showAlert = ko.observable(false);
        self.alertMessage = ko.observable("");
        self.alertType = ko.observable("alert-warning");

        self.missingParamToFlash = ko.observable(false);
        self.progressBarText = ko.observable();
        self.isBusy = ko.observable(false);
        self.fileFlashButtonText = ko.observable("");
        self.urlFlashButtonText = ko.observable("");
        
        self.saving = ko.observable(false);
        self.deleting = ko.observable(false);
        self.adding = ko.observable(false);

        self.newProfileName = ko.observable("");

        self.showPluginSettingsInOptions = ko.observable();
        self.showProfileSettingsInOptions = ko.observable();
        self.optionsDialogTitle = ko.observable("Firmware Updater Configuration");

        // Returns a list of file types to accept for upload based on whether or not file type filter is enabled or disabled
        self.filterFileTypes = ko.computed(function() {
            if (self.configDisableFileFilter()) {
                return null;
            } else {
                return '.hex,.bin';
            }
        });

        // Prevents enabling the delete button for profile 0
        self.canDeleteProfile = ko.computed(function() {
            return self.selectedProfileIndex() != 0;
        });
        
        // Disables the navbar icon if the logged-in user is not an admin
        self.showFirmwareUpdaterNavbarIcon = ko.computed(function() {
            return self.loginState.isAdmin() && self.configShowNavbarIcon();
        });

        // Gets the selected profile from the profile collection, based on the selected profile index
        self.selectedProfile = ko.computed(function() {
            var index = self.selectedProfileIndex();
            if (index < self.profiles().length) {
                return self.profiles()[index];
            } else {
                return null;
            }
        });

        // Gets the name of the selected profile
        self.selectedProfileName = ko.computed(function() {
            if (self.selectedProfile() != null) {
                return ko.toJS(self.selectedProfile())._name;
            } else {
                return null;
            }
        });

        self.selectFilePath = undefined;
        self.configurationDialog = undefined;
        self.bootloaderWarningDialog = undefined;
        self.profileAddDialog = undefined;
        self.profileCopyDialog = undefined;
        self.profileDeleteDialog = undefined;

        self.profileDefaults = undefined;
        self.inSettingsDialog = false;

        self.onStartup = function() {
            self.selectFilePath = $("#settings_plugin_firmwareupdater_selectFilePath");

            // Plugin modals
            self.configurationDialog = $("#settings_plugin_firmwareupdater_configurationDialog");
            self.bootloaderWarningDialog = $("#settings_plugin_firmwareupdater_bootLoaderWarningModal");

            // Profile Modals
            self.profileAddDialog = $("#settings_plugin_firmwareupdater_newProfileModal");
            self.profileCopyDialog = $("#settings_plugin_firmwareupdater_copyProfileModal");
            self.profileDeleteDialog = $("#settings_plugin_firmwareupdater_profileDeleteModal");

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

        self.onBeforeBinding = function() {
            // Get all the profiles from the settings
            self.profiles(self.settingsViewModel.settings.plugins.firmwareupdater.profiles());

            // Get the index of the selected profile
            self.selectedProfileIndex(self.settingsViewModel.settings.plugins.firmwareupdater._selected_profile());
            
            // Make sure the selected profile is valid, reset it to 0 if not
            if (self.selectedProfileIndex() >= self.profiles().length) {
                self.selectedProfileIndex(0);
                self._saveSelectedProfile();
            }

            // Select profile 0 if profiles are disabled
            self.configProfilesEnabled(self.settingsViewModel.settings.plugins.firmwareupdater.enable_profiles())
            if (self.configProfilesEnabled() != true) {
                self.selectedProfileIndex(0);
                self._saveSelectedProfile();
            }

            // Make the profiles UI elements visible/hidden per the setting
            self.configProfilesVisible(self.configProfilesEnabled())

            // Get all the default profile settings
            self.profileDefaults = ko.toJS(self.settingsViewModel.settings.plugins.firmwareupdater._profiles)
        }

        self.onAllBound = function(allViewModels) {
            self.configShowNavbarIcon(self.settingsViewModel.settings.plugins.firmwareupdater.enable_navbar());

            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                self.firmwareFileURL(self.settingsViewModel.settings.plugins.firmwareupdater.last_url());
            } else {
                self.firmwareFileURL("");
            }

            self.marlinbftHasCapability(self.settingsViewModel.settings.plugins.firmwareupdater.has_bftcapability());
            self.marlinbftHasBinProto2Package(self.settingsViewModel.settings.plugins.firmwareupdater.has_binproto2package());
            self.configDisableFileFilter(self.settingsViewModel.settings.plugins.firmwareupdater.disable_filefilter());
            self.pluginVersion(self.settingsViewModel.settings.plugins.firmwareupdater._plugin_version());
        }

        self.onSettingsShown = function() {
            self.inSettingsDialog = true;
        };

        self.onSettingsHidden = function() {
            self.inSettingsDialog = false;
            self.showAlert(false);
        };

        /*
        * Sets the serial port when the connected printer port changes
        */
        self.connection.selectedPort.subscribe(function(value) {
            if (value === undefined) return;
            self.flashPort(value);
        });

        /*
        * Opens the plugin UI from the Navbar
        */
        self.showFirmwareUpdater = function(){
            self.settingsViewModel.show("#settings_plugin_firmwareupdater");
        }

        /*
        * Opens the plugin options modal with he appropriate heading, visible pages, and selected page
        */
        self.showPluginOptions = function () {
            self.showPluginSettingsInOptions(true);
            self.showProfileSettingsInOptions(!self.configProfilesEnabled());
            if (self.configProfilesEnabled()) {
                self.optionsDialogTitle("Firmware Updater Options")
                $('.nav-tabs a[href="#plugin"]').tab('show');
            } else {
                self.optionsDialogTitle("Firmware Updater Configuration")
                $('.nav-tabs a[href="#flash-method"]').tab('show');
            }
            self.showPluginConfig();
        }

        /*
        * Shows the profile settings editor modal
        */
        self.editSelectedProfile = function(){
            self.showPluginSettingsInOptions(false);
            self.showProfileSettingsInOptions(true);
            self.optionsDialogTitle("Update Profile Configuration")
            $('.nav-tabs a[href="#flash-method"]').tab('show');
            self.showPluginConfig();
        }

        /*
        * Shows the new profile modal
        */
        self.showAddModal = function() {
            self.newProfileName("");
            self.profileAddDialog.modal();
        }

        /*
        * Creates a new profile and selects it
        */
        self.addNewProfile = function() {
            self.adding(true)
            var profiles = ko.toJS(self.profiles())
            var newProfile = {_name: self.newProfileName()}
            profiles.push(newProfile);
            var data = {
                plugins: {
                    firmwareupdater: {
                        _selected_profile: profiles.length - 1,
                        profiles: profiles,
                    }
                }
            };

            self.settingsViewModel.saveData(data).done(function () {
                self.profileAddDialog.modal("hide");
                self.adding(false);
                self.profiles(profiles)
                self.selectedProfileIndex(profiles.length - 1)
                self.newProfileName(null)
            });
        }

        /*
        * Shows the new profile modal
        */
        self.showCopyModal = function() {
            self.newProfileName(self.selectedProfileName() + ' - Copy')
            self.profileCopyDialog.modal()
        }

        self.copyProfile = function() {
            self.adding(true)
            var profiles = ko.toJS(self.profiles())
            var newProfile = ko.toJS(self.selectedProfile())
            newProfile._name = self.newProfileName()
            profiles.push(newProfile);
            var data = {
                plugins: {
                    firmwareupdater: {
                        _selected_profile: profiles.length - 1,
                        profiles: profiles,
                    }
                }
            };

            self.settingsViewModel.saveData(data).done(function () {
                self.profileCopyDialog.modal("hide");
                self.adding(false);
                self.profiles(profiles);
                self.selectedProfileIndex(profiles.length - 1);
                self.newProfileName(null)
            });
        }

        /*
        * Shows the profile deletion confirmation modal
        */
        self.showDeleteModal = function() {
            self.profileDeleteDialog.modal()
        }

        /*
        * Deletes the selected profile from the settings and saves the settings
        * Selects the n-1 profile after deleting the selected profile
        */
        self.deleteSelectedProfile = function(){
            self.deleting(true)
            var index = self.selectedProfileIndex()
            var profiles = ko.toJS(self.profiles())
            profiles.splice(index, 1);
            var data = {
                plugins: {
                    firmwareupdater: {
                        _selected_profile: index - 1,
                        profiles: profiles,
                    }
                }
            };

            self.settingsViewModel.saveData(data).done(function () {
                self.profileDeleteDialog.modal("hide");
                self.deleting(false);
                self.profiles(profiles)
                self.selectedProfileIndex(index - 1)
            });
        }

        self.getProfileSetting = function(key) {
            var profile_settings = Object.assign({}, self.profileDefaults, ko.toJS(self.selectedProfile()));
            return profile_settings[key]
        }

        /*
        * Shows and hides the relevant flash-method settings
        */
        self.configFlashMethod.subscribe(function(value) {
            // Hide all the flash method settings
            self.showAvrdudeConfig(false);
            self.showBossacConfig(false);
            self.showLpc1768Config(false);
            self.showDfuConfig(false);
            self.showStm32flashConfig(false);
            self.showMarlinBftConfig(false);
            
            // Show only the selected method's settings
            if(value == 'avrdude') {
                self.showAvrdudeConfig(true);
            } else if(value == 'bossac') {
                self.showBossacConfig(true);
            } else if(value == 'lpc1768'){
                self.showLpc1768Config(true);
            } else if(value == 'dfuprogrammer'){
                self.showDfuConfig(true);
            } else if(value == 'stm32flash'){
                self.showStm32flashConfig(true);
            } else if(value == 'marlinbft'){
                self.showMarlinBftConfig(true);
            }
        });

        /*
        * Shows a warning if the selected filename contains the word 'bootloader'
        */
        self.firmwareFileName.subscribe(function(value) {
            if (!self.getProfileSetting("disable_bootloadercheck")) {
                if (value.search(/bootloader/i) > -1) {
                    self.bootloaderWarningDialog.modal();
                }
            }
         });

        self._checkIfReadyToFlash = function(source) {
            var alert = undefined;

            if (!self.loginState.isAdmin()){
                alert = gettext("You need administrator privileges to flash firmware.");
            }

            if (self.printerState.isPrinting() || self.printerState.isPaused()){
                alert = gettext("Printer is printing. Please wait for the print to be finished.");
            }

            if (!self.getProfileSetting("flash_method")){
                alert = gettext("The flash method is not selected.");
            }

            if (self.getProfileSetting("flash_method") == "avrdude" && !self.getProfileSetting("avrdude_avrmcu")) {
                alert = gettext("The AVR MCU type is not selected.");
            }

            if (self.getProfileSetting("flash_method") == "avrdude" && !self.getProfileSetting("avrdude_path")) {
                alert = gettext("The avrdude path is not configured.");
            }

            if (self.getProfileSetting("flash_method") == "avrdude" && !self.getProfileSetting("avrdude_programmer")) {
                alert = gettext("The AVR programmer is not selected.");
            }

            if (self.getProfileSetting("flash_method") == "bossac" && !self.getProfileSetting("bossac_path")) {
                alert = gettext("The bossac path is not configured.");
            }

            if (self.getProfileSetting("flash_method") == "lpc1768" && !self.getProfileSetting("lpc1768_path")) {
                alert = gettext("The lpc1768 firmware folder path is not configured.");
            }

            if (self.getProfileSetting("flash_method") == "dfuprogrammer" && !self.getProfileSetting("dfuprog_path")) {
                alert = gettext("The dfu-programmer path is not configured.");
            }

            if (self.getProfileSetting("flash_method") == "dfuprogrammer" && !self.getProfileSetting("dfuprog_avrmcu")) {
                alert = gettext("The AVR MCU type is not selected.");
            }
            
            if (self.getProfileSetting("flash_method") == "marlinbft" && !self.printerState.isReady()) {
                alert = gettext("The printer is not connected.");
            }
            
            if (self.getProfileSetting("flash_method") == "marlinbft" && self.printerState.isReady() && !self.marlinbftHasBinProto2Package()) {
                alert = gettext("The marlin-binary-protocol Python package is not installed.");
            }

            if (self.getProfileSetting("flash_method") == "marlinbft" && self.printerState.isReady() && !self.marlinbftHasCapability()) {
                alert = gettext("The printer does not support Binary File Transfer.");
            }

            if (!self.flashPort() &! self.getProfileSetting("flash_method") == "dfuprogrammer") {
                alert = gettext("The printer port is not selected.");
            }

            if (source === "file" && !self.firmwareFileName()) {
                alert = gettext("Firmware file is not specified");
            } else if (source === "url" && !self.firmwareFileURL()) {
                alert = gettext("Firmware URL is not specified");
            }

            if (alert !== undefined) {
                self.alertType("alert-warning");
                self.alertMessage(alert);
                self.showAlert(true);
                return false;
            } else {
                self.alertMessage(undefined);
                self.showAlert(false);
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

            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                self.configLastUrl(self.firmwareFileURL());
                self._saveLastUrl();
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

            switch (data.type) {
                case "capability": {
                    if (data.capability == "BINARY_FILE_TRANSFER") {
                        self.marlinbftHasCapability(data.enabled);
                    }
                    break;
                }
                case "status": {
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
                                        message = gettext("Flash method is not properly configured.");
                                        break;
                                    }
                                    case "hexfile": {
                                        message = gettext("Cannot read file to flash.");
                                        break;
                                    }
                                    case "notconnected": {
                                        message = gettext("Printer is not connected.");
                                        break;
                                    }
                                    case "nobftcap": {
                                        message = gettext("Printer does not report support for the Marlin Binary File Transfer protocol.");
                                        break;
                                    }
                                    case "nobinproto2": {
                                        message = gettext("Python package 'marlin-binary-protocol' is not installed.");
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
                            self.firmwareFileName("");
                            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                                self.firmwareFileURL(self.configLastUrl());
                            } else {
                                self.firmwareFileURL("");
                            }
                            break;
                        }
                        case "success": {
                            self.showPopup("success", gettext("Flashing successful"), "");
                            self.isBusy(false);
                            self.showAlert(false);
                            self.firmwareFileName("");
                            if (self.settingsViewModel.settings.plugins.firmwareupdater.save_url()) {
                                self.firmwareFileURL(self.configLastUrl());
                            } else {
                                self.firmwareFileURL("");
                            }
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
                                    case "waitforsd": {
                                        message = gettext("Waiting for SD card to mount on host...");
                                        break;
                                    }
                                    case "copying": {
                                        message = gettext("Copying firmware to SD card...");
                                        break;
                                    }
                                    case "bftinit": {
                                        message = gettext("Initializing file transfer protocol...");
                                        break;
                                    }
                                    case "bftconnect": {
                                        message = gettext("Connecting file transfer protocol...");
                                        break;
                                    }
                                    case "finishing": {
                                        message = gettext("Finishing up...");
                                        break;
                                    }
                                    case "sending": {
                                        message = gettext("Sending firmware to printer...");
                                        break;
                                    }
                                    case "unmounting": {
                                        message = gettext("Unmounting SD card...");
                                        break;
                                    }
                                    case "writing": {
                                        message = gettext("Writing memory...");
                                        break;
                                    }
                                    case "erasing": {
                                        message = gettext("Erasing memory...");
                                        break;
                                    }
                                    case "verifying": {
                                        message = gettext("Verifying memory...");
                                        break;
                                    }
                                    case "postflashdelay": {
                                        message = gettext("Post-flash delay...");
                                        break;
                                    }
                                    case "boardreset": {
                                            message = gettext("Resetting the board...");
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
                    break;
                }
            }
        };

        /*
        * Loads all the settings and shows the configuration modal
        */
        self.showPluginConfig = function() {
            // Load the general plugin settings
            self.configProfilesEnabled(self.settingsViewModel.settings.plugins.firmwareupdater.enable_profiles());
            self.configShowNavbarIcon(self.settingsViewModel.settings.plugins.firmwareupdater.enable_navbar());
            self.configSaveUrl(self.settingsViewModel.settings.plugins.firmwareupdater.save_url());
            
            self.configDisableFileFilter(self.settingsViewModel.settings.plugins.firmwareupdater.disable_filefilter());
            self.marlinbftHasBinProto2Package(self.settingsViewModel.settings.plugins.firmwareupdater.has_binproto2package());

            // Load the profile settings
            self.configProfileName(self.getProfileSetting("_name"))
            self.configFlashMethod(self.getProfileSetting("flash_method"))
            self.configDisableBootloaderCheck(self.getProfileSetting("disable_bootloadercheck"));
            self.configLastUrl(self.getProfileSetting("last_url"));

            // Pre and post flash settings
            self.configNoAutoReconnect(self.getProfileSetting("no_reconnect_after_flash"))
            self.configEnablePreflashDelay(self.getProfileSetting("enable_preflash_delay"))
            self.configPreflashDelay(self.getProfileSetting("preflash_delay"))
            self.configEnablePostflashDelay(self.getProfileSetting("enable_postflash_delay"))
            self.configPostflashDelay(self.getProfileSetting("postflash_delay"))
            self.configEnablePreflashCommandline(self.getProfileSetting("enable_preflash_commandline"))
            self.configPreflashCommandline(self.getProfileSetting("preflash_commandline"))
            self.configEnablePostflashCommandline(self.getProfileSetting("enable_postflash_commandline"))
            self.configPostflashCommandline(self.getProfileSetting("postflash_commandline"))
            self.configEnablePreflashGcode(self.getProfileSetting("enable_preflash_gcode"))
            self.configPreflashGcode(self.getProfileSetting("preflash_gcode"))
            self.configEnablePostflashGcode(self.getProfileSetting("enable_postflash_gcode"))
            self.configPostflashGcode(self.getProfileSetting("postflash_gcode"))

            // Load the avrdude settings
            self.configAvrdudePath(self.getProfileSetting("avrdude_path"))
            self.configAvrdudeCommandLine(self.getProfileSetting("avrdude_commandline"))
            self.configAvrdudeConfigFile(self.getProfileSetting("avrdude_conf"))
            self.configAvrdudeMcu(self.getProfileSetting("avrdude_avrmcu"))
            self.configAvrdudeMcu(self.getProfileSetting("avrdude_avrmcu"))
            self.configAvrdudeProgrammer(self.getProfileSetting("avrdude_programmer"))
            self.configAvrdudeBaudRate(self.getProfileSetting("avrdude_baudrate"))
            self.configAvrdudeDisableVerification(self.getProfileSetting("avrdude_disableverify"))
            
            // Load the bossac settings
            self.configBossacPath(self.getProfileSetting("bossac_path"))
            self.configBossacDisableVerification(self.getProfileSetting("bossac_disableverify"))
            self.configBossacCommandLine(self.getProfileSetting("bossac_commandline"))

            // Load the dfu-programmer settings
            self.configDfuPath(self.getProfileSetting("dfuprog_path"))
            self.configDfuMcu(self.getProfileSetting("dfuprog_avrmcu"))
            self.configDfuCommandLine(self.getProfileSetting("dfuprog_commandline"))
            self.configDfuEraseCommandLine(self.getProfileSetting("dfuprog_erasecommandline"))

            // Load the lpc1768 settings
            self.configLpc1768Path(self.getProfileSetting("lpc1768_path"))
            self.configLpc1768UnmountCommand(self.getProfileSetting("lpc1768_unmount_command"))
            self.configLpc1768ResetBeforeFlash(self.getProfileSetting("lpc1768_preflashreset"))
            self.configLpc1768NoResetWait(self.getProfileSetting("lpc1768_no_m997_reset_wait"))
            self.configLpc1768NoRestartWait(self.getProfileSetting("lpc1768_no_m997_restart_wait"))

            // Load the marlinbft settings
            self.configMarlinBftWaitAfterConnect(self.getProfileSetting("marlinbft_waitafterconnect"))
            self.configMarlinBftTimeout(self.getProfileSetting("marlinbft_timeout"))
            self.configMarlinBftProgressLogging(self.getProfileSetting("marlinbft_progresslogging"))
            self.configMarlinBftNoResetWait(self.getProfileSetting("marlinbft_no_m997_reset_wait"))
            self.configMarlinBftNoRestartWait(self.getProfileSetting("marlinbft_no_m997_restart_wait"))

            // Load the stm32flash settings
            self.configStm32flashPath(self.getProfileSetting("stm32flash_path"))
            self.configStm32flashVerify(self.getProfileSetting("stm32flash_verify"))
            self.configStm32flashBoot0Pin(self.getProfileSetting("stm32flash_boot0pin"))
            self.configStm32flashBoot0Low(self.getProfileSetting("stm32flash_boot0low"))
            self.configStm32flashResetPin(self.getProfileSetting("stm32flash_resetpin"))
            self.configStm32flashResetLow(self.getProfileSetting("stm32flash_resetlow"))
            self.configStm32flashExecute(self.getProfileSetting("stm32flash_execute"))
            self.configStm32flashExecuteAddress(self.getProfileSetting("stm32flash_executeaddress"))
            self.configStm32flashReset(self.getProfileSetting("stm32flash_reset"))

            // Show the modal
            self.configurationDialog.modal();
        };

        /*
        * Compares the profile settings with the defaults and removes any settings which match the default
        * Also forces empty strings to null, null booleans to false, null integers to their default value, and integers as strings to integers
        */
        self.removeProfileDefaultBeforeSave = function(profile) {
            for (const key in profile) {
                var keyValue
                var defaultValue = self.profileDefaults[key];

                keyValue = (profile[key] === '' ? null : profile[key]);
                keyValue = ((defaultValue === true || defaultValue === false) && keyValue == null) ? false : keyValue
                keyValue = (Number.isInteger(defaultValue) && keyValue == null) ? defaultValue : keyValue
                
                if (Number.isInteger(parseInt(keyValue))) {
                    profile[key] = parseInt(keyValue);
                }

                if (keyValue == defaultValue) {
                    delete profile[key]
                }
            }
            return profile;
        }
        
        /*
        * Saves the configuration when the settings are closed
        */
        self.onConfigClose = function() {
            self._saveConfig();
        };

        /*
        * Saves all the plugin settings
        */
        self._saveConfig = function() {
            self.saving(true);
            var index = self.selectedProfileIndex();
            var profiles = ko.toJS(self.profiles())

            // Update the settings in the current profile
            profiles[index]["_name"] = self.configProfileName();
            profiles[index]["flash_method"] = self.configFlashMethod();
            profiles[index]["disable_bootloadercheck"] = self.configDisableBootloaderCheck();

            // Pre and post flash settings
            profiles[index]["no_reconnect_after_flash"] = self.configNoAutoReconnect();
            profiles[index]["enable_preflash_delay"] = self.configEnablePreflashDelay();
            profiles[index]["preflash_delay"] = self.configPreflashDelay();
            profiles[index]["enable_postflash_delay"] = self.configEnablePostflashDelay();
            profiles[index]["postflash_delay"] = self.configPostflashDelay();
            profiles[index]["enable_preflash_commandline"] = self.configEnablePreflashCommandline();
            profiles[index]["preflash_commandline"] = self.configPreflashCommandline();
            profiles[index]["enable_postflash_commandline"] = self.configEnablePostflashCommandline();
            profiles[index]["preflash_commandline"] = self.configPreflashCommandline();
            profiles[index]["enable_preflash_gcode"] = self.configEnablePreflashGcode();
            profiles[index]["preflash_gcode"] = self.configPreflashGcode();
            profiles[index]["enable_postflash_gcode"] = self.configEnablePostflashGcode();
            profiles[index]["postflash_gcode"] = self.configPostflashGcode();

            // Avrdude settings
            profiles[index]["avrdude_path"] = self.configAvrdudePath();
            profiles[index]["avrdude_conf"] = self.configAvrdudeConfigFile();
            profiles[index]["avrdude_avrmcu"] = self.configAvrdudeMcu();
            profiles[index]["avrdude_programmer"] = self.configAvrdudeProgrammer();
            profiles[index]["avrdude_baudrate"] = self.configAvrdudeBaudRate();
            profiles[index]["avrdude_disableverify"] = self.configAvrdudeDisableVerification();
            profiles[index]["avrdude_commandline"] = self.configAvrdudeCommandLine();

            // Bossac settings
            profiles[index]["bossac_path"] = self.configBossacPath();
            profiles[index]["bossac_disableverify"] = self.configBossacDisableVerification();
            profiles[index]["bossac_commandline"] = self.configBossacCommandLine();

            // DFU-Programmer settings
            profiles[index]["dfuprog_path"] = self.configDfuPath();
            profiles[index]["dfuprog_avrmcu"] = self.configDfuMcu();
            profiles[index]["dfuprog_commandline"] = self.configDfuCommandLine();
            profiles[index]["dfuprog_erasecommandline"] = self.configDfuEraseCommandLine();

            // LPC176x settings
            profiles[index]["lpc1768_path"] = self.configLpc1768Path();
            profiles[index]["lpc1768_unmount_command"] = self.configLpc1768UnmountCommand();
            profiles[index]["lpc1768_preflashreset"] = self.configLpc1768ResetBeforeFlash();
            profiles[index]["lpc1768_no_m997_reset_wait"] = self.configLpc1768NoResetWait();
            profiles[index]["lpc1768_no_m997_restart_wait"] = self.configLpc1768NoRestartWait();

            // MarlinBFT Settings
            profiles[index]["marlinbft_waitafterconnect"] = self.configMarlinBftWaitAfterConnect();
            profiles[index]["marlinbft_timeout"] = self.configMarlinBftTimeout();
            profiles[index]["marlinbft_progresslogging"] = self.configMarlinBftProgressLogging();
            profiles[index]["marlinbft_no_m997_reset_wait"] = self.configMarlinBftNoResetWait();
            profiles[index]["marlinbft_no_m997_restart_wait"] = self.configMarlinBftNoRestartWait();

            // STM32Flash Settings
            profiles[index]["stm32flash_path"] = self.configStm32flashPath();
            profiles[index]["stm32flash_verify"] = self.configStm32flashVerify();
            profiles[index]["stm32flash_boot0pin"] = self.configStm32flashBoot0Pin();
            profiles[index]["stm32flash_boot0low"] = self.configStm32flashBoot0Low();
            profiles[index]["stm32flash_resetpin"] = self.configStm32flashResetPin();
            profiles[index]["stm32flash_resetlow"] = self.configStm32flashResetLow();
            profiles[index]["stm32flash_execute"] = self.configStm32flashExecute();
            profiles[index]["stm32flash_executeaddress"] = self.configStm32flashExecuteAddress();
            profiles[index]["stm32flash_reset"] = self.configStm32flashReset();

            // Remove all the settings which are the same as the defaults so we only store what's needed
            profiles[index] = self.removeProfileDefaultBeforeSave(profiles[index]);
          
            // Construct the settings object
            var data = {
                plugins: {
                    firmwareupdater: {
                        enable_navbar: self.configShowNavbarIcon(),
                        enable_profiles: self.configProfilesEnabled(),
                        save_url: self.configSaveUrl(),
                        disable_filefilter: self.configDisableFileFilter(),
                        profiles: profiles,
                    }
                }
            }

            // Save the settings
            self.settingsViewModel.saveData(data).done(function () {
                self.profiles(profiles)
                self.selectedProfileIndex(index)
                self.configurationDialog.modal("hide");
                self.alertMessage(undefined);
                self.showAlert(false);
                self.onConfigHidden();
                self.saving(false);
                self.configProfilesVisible(self.configProfilesEnabled());
            });
        };

        self.selectedProfileOnChange = function(data, event) {
            self._saveSelectedProfile();
        }

        /*
        * Saves the selected profile index
        */
        self._saveSelectedProfile = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        _selected_profile: self.selectedProfileIndex(),
                    }
                }
            };
            self.settingsViewModel.saveData(data);
            // TODO: Disable UI until this finishes
        }

        /*
        * Saves the last URL
        */
        self._saveLastUrl = function() {
            var data = {
                plugins: {
                    firmwareupdater: {
                        last_url: self.firmwareFileURL(),
                    }
                }
            };
            self.settingsViewModel.saveData(data);
        }

        /*
        * Clears any path test status messages when the settings are closed
        */
        self.onConfigHidden = function() {
            self.avrdudePathBroken(false);
            self.avrdudePathOk(false);
            self.avrdudePathText("");
            self.avrdudeConfPathBroken(false);
            self.avrdudeConfPathOk(false);
            self.avrdudeConfPathText("");

            self.bossacPathBroken(false);
            self.bossacPathOk(false);
            self.bossacPathText("");

            self.dfuPathBroken(false);
            self.dfuPathOk(false);
            self.dfuPathText("");

            self.lpc1768PathBroken(false);
            self.lpc1768PathOk(false);
            self.lpc1768PathText("");

            self.stm32flashPathBroken(false);
            self.stm32flashPathOk(false);
            self.stm32flashPathText("");
        };

        self.resetAvrdudeCommandLine = function() {
            self.configAvrdudeCommandLine(self.profileDefaults["avrdude_commandline"]);
        };

        self.resetBossacCommandLine = function() {
            self.configBossacCommandLine(self.profileDefaults["bossac_commandline"]);

        };

        self.resetDfuCommandLine = function() {
            self.configDfuCommandLine(self.profileDefaults["dfuprog_commandline"]);
        };

        self.resetDfuEraseCommandLine = function() {
            self.configDfuEraseCommandLine(self.profileDefaults["dfuprog_erasecommandline"]);
        };

        self.resetLpc1768UnmountCommand = function() {
            self.configLpc1768UnmountCommand(self.profileDefaults["lpc1768_unmount_command"]);
        }

        self.testAvrdudePath = function() {
            var filePathRegEx_Linux = new RegExp("^(\/[^\0/]+)+$");
            var filePathRegEx_Windows = new RegExp("^[A-z]\:\\\\.+.exe$");

            if ( !filePathRegEx_Linux.test(self.configAvrdudePath()) && !filePathRegEx_Windows.test(self.configAvrdudePath()) ) {
                self.avrdudePathText(gettext("The path is not valid"));
                self.avrdudePathOk(false);
                self.avrdudePathBroken(true);
            } else {
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
            }
        };

        self.testBossacPath = function() {
            var filePathRegEx_Linux = new RegExp("^(\/[^\0/]+)+$");
            var filePathRegEx_Windows = new RegExp("^[A-z]\:\\\\.+.exe$");

            if ( !filePathRegEx_Linux.test(self.configBossacPath()) && !filePathRegEx_Windows.test(self.configBossacPath()) ) {
                self.bossacPathText(gettext("The path is not valid"));
                self.bossacPathOk(false);
                self.bossacPathBroken(true);
            } else {
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
            }
        };

        self.testDfuPath = function() {
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configDfuPath())) {
                self.dfuPathText(gettext("The path is not valid"));
                self.dfuPathOk(false);
                self.dfuPathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configDfuPath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.dfuPathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.dfuPathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.dfuPathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.dfuPathText(gettext("The path is valid"));
                        }
                        self.dfuPathOk(response.result);
                        self.dfuPathBroken(!response.result);
                    }
                })
            }
        };

        self.testStm32flashPath = function() {
            var filePathRegEx = new RegExp("^(\/[^\0/]+)+$");

            if (!filePathRegEx.test(self.configStm32flashPath())) {
                self.stm32flashPathText(gettext("The path is not valid"));
                self.stm32flashPathOk(false);
                self.stm32flashPathBroken(true);
            } else {
                $.ajax({
                    url: API_BASEURL + "util/test",
                    type: "POST",
                    dataType: "json",
                    data: JSON.stringify({
                        command: "path",
                        path: self.configStm32flashPath(),
                        check_type: "file",
                        check_access: "x"
                    }),
                    contentType: "application/json; charset=UTF-8",
                    success: function(response) {
                        if (!response.result) {
                            if (!response.exists) {
                                self.stm32flashPathText(gettext("The path doesn't exist"));
                            } else if (!response.typeok) {
                                self.stm32flashPathText(gettext("The path is not a file"));
                            } else if (!response.access) {
                                self.stm32flashPathText(gettext("The path is not an executable"));
                            }
                        } else {
                            self.stm32flashPathText(gettext("The path is valid"));
                        }
                        self.stm32flashPathOk(response.result);
                        self.stm32flashPathBroken(!response.result);
                    }
                })
            }
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

        self.testLpc1768Path = function() {
            $.ajax({
                url: API_BASEURL + "util/test",
                type: "POST",
                dataType: "json",
                data: JSON.stringify({
                    command: "path",
                    path: self.configLpc1768Path(),
                    check_type: "dir",
                    check_writable_dir: "true"
                }),
                contentType: "application/json; charset=UTF-8",
                success: function(response) {
                    if (!response.result) {
                        if (!response.exists) {
                            self.lpc1768PathText(gettext("The path doesn't exist"));
                        } else if (!response.typeok) {
                            self.lpc1768PathText(gettext("The path is not a folder"));
                        } else if (!response.access) {
                            self.lpc1768PathText(gettext("The path is not writeable"));
                        }
                    } else {
                        self.lpc1768PathText(gettext("The path is valid"));
                    }
                    self.lpc1768PathOk(response.result);
                    self.lpc1768PathBroken(!response.result);
                }
            })
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
        ["settingsViewModel", "loginStateViewModel", "connectionViewModel", "printerStateViewModel", "accessViewModel"],
        ["#settings_plugin_firmwareupdater", "#navbar_plugin_firmwareupdater"]
    ]);
});
