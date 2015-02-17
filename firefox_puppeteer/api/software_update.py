# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ConfigParser
import re

import mozinfo
from marionette.errors import TimeoutException

from ..base import BaseLib
from .appinfo import AppInfo
from .prefs import Preferences


class SoftwareUpdate(BaseLib):
    """The SoftwareUpdate API adds support for an easy access to the update process."""

    PREF_APP_DISTRIBUTION = 'distribution.id'
    PREF_APP_DISTRIBUTION_VERSION = 'distribution.version'
    PREF_APP_UPDATE_URL = 'app.update.url'
    PREF_DISABLED_ADDONS = 'extensions.disabledAddons'

    def __init__(self, marionette_getter):
        BaseLib.__init__(self, marionette_getter)

        self.app_info = AppInfo(marionette_getter)
        self.prefs = Preferences(marionette_getter)

        self.update_channel = UpdateChannel(self)
        self.mar_channels = MARChannels(self)
        self.active_update = ActiveUpdate(self)

        self._aus = self.marionette.execute_script("""
            return Cc['@mozilla.org/updates/update-service;1']
                .getService(Ci.nsIApplicationUpdateService);
            """)

    @property
    def ABI(self):
        """Get the customized ABI for the update service.

        :returns: ABI version
        """

        abi = self.app_info.XPCOMABI
        if mozinfo.isMac:
            abi += self.marionette.execute_script("""
                let macutils = Cc['@mozilla.org/xpcom/mac-utils;1']
                    .getService(Ci.nsIMacUtils);
                if (macutils.isUniversalBinary)
                    return '-u-' + macutils.architecturesInBinary;

                return '';
            """)

        return abi

    @property
    def allowed(self):
        """Check if the user has permissions to run the software update

        :returns: Status if the user has the permissions
        """

        return self._aus['canCheckForUpdates'] and self._aus['canApplyUpdates']

    @property
    def build_info(self):
        """Return information of the current build version

        :returns: A dictionary of build information
        """

        return {
            'buildid': self.app_info.appBuildID,
            'channel': self.update_channel.channel,
            'disabled_addons': self.prefs.get_pref('PREF_DISABLED_ADDONS'),
            'locale': self.app_info.locale,
            'mar_channels': self.mar_channels.channels,
            'url_aus': self.update_url(True),
            'user_agent': self.app_info.user_agent,
            'version': self.app_info.version
        }

    def check_for_updates(self):
        """Checks for available updates."""
        try:
            # Version using checkForUpdates which I believe is working, but
            # still doesn't allow us to find an active update
            self.marionette.execute_async_script("""

                let checker = Cc['@mozilla.org/updates/update-checker;1']
                    .createInstance(Ci.nsIUpdateChecker);
                checker.checkForUpdates({
                    onCheckComplete: function(aRequest, aUpdates, aUpdateCount) {
                        return marionetteScriptFinished(true);
                    },
                    onError: function(aRequest, aUpdate) {
                        return marionetteScriptFinished(false);
                    },
                    QueryInterface: function(aIID) {
                      if (!aIID.equals(Components.interfaces.nsIUpdateCheckListener) &&
                          !aIID.equals(Components.interfaces.nsISupports))
                        throw Components.results.NS_ERROR_NO_INTERFACE;
                      return this;
                    }
                  }, true);

            """, script_timeout=10000)
        except TimeoutException:
            pass

    def get_update_at(self, update_index):
        """Use nsIUpdateManager.getUpdateAt() to return an update

        :returns: nsIUpdate object
        """

        return self.marionette.execute_script("""
            let ums = Cc['@mozilla.org/updates/update-manager;1']
                .getService(Ci.nsIUpdateManager);
            let update_index = arguments[0];
            return ums.getUpdateAt(update_index);

        """, script_args=[update_index])

    @property
    def is_complete_update(self):
        """Return true if the offered update is a complete update

        :returns: True if the offered update is a complete update
        """

        # Throw when isCompleteUpdate is called without an update. This should
        # never happen except if the test is incorrectly written.
        patch_count = self.active_update.patch_count
        assert patch_count, 'An active update has been found'

        assert patch_count == 1 or patch_count == 2,\
            'An update must have one or two patches included'

        # Ensure Partial and Complete patches produced have unique urls
        if patch_count == 2:
            patch0_URL = self.active_update.get_patch_at(0)['URL']
            patch1_URL = self.active_update.get_patch_at(1)['URL']
            assert patch0_URL != patch1_URL,\
                'Partial and Complete download URLs are different'

        return self.active_update.selected_patch_type == 'complete'

    def update_url(self, force=False):
        """Retrieve the AUS update URL the update snippet is retrieved from

        :param force: Boolean flag to force an update check

        :returns: The URL of the update snippet
        """

        url = self.prefs.get_pref(self.PREF_APP_UPDATE_URL, '')
        # get the next two prefs from the default branch
        dist = self.prefs.get_pref(self.PREF_APP_DISTRIBUTION, True) or 'default'
        dist_version = self.prefs.get_pref(self.PREF_APP_DISTRIBUTION_VERSION, True) or 'default'

        if not url:
            return None

        # Not all placeholders are getting replaced correctly by formatURL
        url = re.sub(r'%PRODUCT%', self.app_info.name, url)
        url = re.sub(r'%BUILD_ID%', self.app_info.appBuildID, url)
        url = re.sub(r'%BUILD_TARGET%', self.app_info.OS + '_' + self.ABI, url)
        # TODO: I don't think we want this mozinfo.version as it includes spaces,
        # not sure which, if any, mozinfo value we can use
        url = re.sub(r'%OS_VERSION%', mozinfo.version, url)
        url = re.sub(r'%CHANNEL%', self.update_channel.channel, url)
        url = re.sub(r'%DISTRIBUTION%', dist, url)
        url = re.sub(r'%DISTRIBUTION_VERSION%', dist_version, url)

        url = self.marionette.execute_script("""
            Cu.import("resource://gre/modules/Services.jsm");

            var url = arguments[0];
            return Services.urlFormatter.formatURL(url);

            """, script_args=[url])

        if force:
            if '?' in url:
                url += '&'
            else:
                url += '?'
            url += 'force=1'
        return url


class ActiveUpdate(object):

    def __init__(self, software_update):

        self.marionette = software_update.marionette
        # TODO: trying to force a check for updates, but still none are found
        software_update.check_for_updates()

    def get_patch_at(self, patch_index):
        """Use nsIUpdate.getPatchAt to return a patch from an update

        :returns: nsIUpdatePatch object
        """

        return self.marionette.execute_script("""
            let ums = Cc['@mozilla.org/updates/update-manager;1']
                .getService(Ci.nsIUpdateManager);
            let active_update = ums.activeUpdate;
            let patch_index = arguments[0];
            return active_update.getPatchAt(patch_index);

        """, script_args=[patch_index])

    @property
    def patch_count(self):
        """Get the patchCount from the active update

        :returns: The patch count
        """

        return self.marionette.execute_script("""
            let ums = Cc['@mozilla.org/updates/update-manager;1']
                .getService(Ci.nsIUpdateManager);
            let active_update = ums.activeUpdate;
            return active_update.patchCount;

        """)

    @property
    def selected_patch_type(self):
        """Get the type of the selected patch for the active update

        :returns: The patch type
        """

        return self.marionette.execute_script("""
            let ums = Cc['@mozilla.org/updates/update-manager;1']
                .getService(Ci.nsIUpdateManager);
            let active_update = ums.activeUpdate;
            return active_update.selectedPatch.type;

        """)


class MARChannels(object):
    """Class to handle the allowed MAR channels as listed in update-settings.ini
    """

    INI_SECTION = 'Settings'
    INI_OPTION = 'ACCEPTED_MAR_CHANNEL_IDS'

    REGEX_UPDATE_CHANNEL_PREF = re.compile(r'("app\.update\.channel", ")([^"].*)(?=")')

    def __init__(self, software_update):

        self.marionette = software_update.marionette
        self.prefs = software_update.prefs

        self.ini_file_path = self.marionette.execute_script("""
            Cu.import('resource://gre/modules/Services.jsm');

            var file = Services.dirsvc.get('GreD', Ci.nsIFile);
            file.append('update-settings.ini');

            return file.path;

            """)

    @property
    def config(self):
        config = ConfigParser.ConfigParser()
        config.readfp(open(self.ini_file_path))
        return config

    @property
    def channels(self):
        channels = self.config.get(self.INI_SECTION, self.INI_OPTION)
        return channels.split(',')

    def set_channels(self, channels):
        channels = ','.join(channels)
        new_config = self.config
        new_config.set(self.INI_SECTION, self.INI_OPTION, channels)
        with open(self.ini_file_path, 'wb') as f:
            new_config.write(f)

    def add_channels(self, channels):
        new_channels = ','.join(self.channels + channels)
        new_config = self.config
        new_config.set(self.INI_SECTION, self.INI_OPTION, new_channels)
        with open(self.ini_file_path, 'wb') as f:
            new_config.write(f)

    def remove_channels(self, channels):
        current_channels = self.channels
        for channel in channels:
            if channel in current_channels:
                current_channels.remove(channel)
        new_channels = ','.join(current_channels)
        new_config = self.config
        new_config.set(self.INI_SECTION, self.INI_OPTION, new_channels)
        with open(self.ini_file_path, 'wb') as f:
            new_config.write(f)

    @property
    def default_channel(self):
        """Get the default update channel

        :returns: Current default update channel
        """
        matches_list = re.findall(self.REGEX_UPDATE_CHANNEL_PREF, self.config_file_contents)
        assert len(matches_list) == 1, 'Update channel value has been found'
        matches_tuple = matches_list[0]
        assert len(matches_tuple) == 2, 'Update channel value has been found'

        return matches_tuple[1]

    def set_default_channel(self, channel):
        """Set default update channel.

        :param channel: New default update channel
        """

        assert channel, 'Update channel has been specified'
        new_content = re.sub(
            self.REGEX_UPDATE_CHANNEL_PREF, r'\1' + channel, self.config_file_contents)
        with open(self.config_file_path, 'w') as f:
            f.write(new_content)


class UpdateChannel(object):
    """Class to handle the update channel as listed in channel-prefs.js
    """

    REGEX_UPDATE_CHANNEL_PREF = re.compile(r'("app\.update\.channel", ")([^"].*)(?=")')

    def __init__(self, software_update):

        self.marionette = software_update.marionette
        self.prefs = software_update.prefs

        self.config_file_path = self.marionette.execute_script("""
            Cu.import('resource://gre/modules/Services.jsm');

            var file = Services.dirsvc.get('PrfDef', Ci.nsIFile);
            file.append('channel-prefs.js');

            return file.path;

            """)

    @property
    def config_file_contents(self):
        with open(self.config_file_path) as f:
            return f.read()

    @property
    def channel(self):
        return self.prefs.get_pref('app.update.channel', True)

    @property
    def default_channel(self):
        """Get the default update channel

        :returns: Current default update channel
        """
        matches_list = re.findall(self.REGEX_UPDATE_CHANNEL_PREF, self.config_file_contents)
        assert len(matches_list) == 1, 'Update channel value has been found'
        matches_tuple = matches_list[0]
        assert len(matches_tuple) == 2, 'Update channel value has been found'

        return matches_tuple[1]

    def set_default_channel(self, channel):
        """Set default update channel.

        :param channel: New default update channel
        """

        assert channel, 'Update channel has been specified'
        new_content = re.sub(
            self.REGEX_UPDATE_CHANNEL_PREF, r'\1' + channel, self.config_file_contents)
        with open(self.config_file_path, 'w') as f:
            f.write(new_content)
