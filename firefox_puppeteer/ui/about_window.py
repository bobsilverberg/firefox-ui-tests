# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from datetime import datetime

from marionette import By, Wait

from .windows import BaseWindow
from ..api.software_update import SoftwareUpdate


class AboutWindow(BaseWindow):
    """Representation of the About window."""

    TIMEOUT_UPDATE_APPLY = 300
    TIMEOUT_UPDATE_CHECK = 30
    TIMEOUT_UPDATE_DOWNLOAD = 360

    window_type = 'Browser:About'

    def __init__(self, marionette_getter, window_handle):
        BaseWindow.__init__(self, marionette_getter, window_handle)

        self.software_update = SoftwareUpdate(marionette_getter)
        self.download_duration = -1

    @property
    def patch_info(self):
        """ Returns information about the active update in the queue.

        :returns: A dictionary with information about the active patch
        """
        patch = self.software_update.patch_info
        patch['download_duration'] = self.download_duration
        return patch

    @property
    def updates_found(self):
        """ Checks if updates were found

        :returns: True if updates were found
        """

        return self.wizard_state != 'noUpdatesFound'

    @property
    def wizard_state(self):
        deck = self.marionette.find_element(By.ID, 'updateDeck')
        return self.marionette.execute_script("""
          return arguments[0].selectedPanel.id;
        """, script_args=[deck])

    def check_for_updates(self):
        """Clicks on "Check for Updates" button, and waits for check to complete"""
        Wait(self.marionette).until(
            lambda _: self.wizard_state == 'checkForUpdates')
        check_button = self.marionette.find_element(By.ID, 'checkForUpdatesButton')
        check_button.click()

        # Wait for the update checking to finish
        Wait(self.marionette, self.TIMEOUT_UPDATE_CHECK).until(
            lambda _: self.wizard_state != 'checkingForUpdates')

    def download(self, wait_for_finish=True, timeout=TIMEOUT_UPDATE_DOWNLOAD):
        """ Download the update

        :param wait_for_finish: Should the function wait until the download has finished?
        :param timeout: How long to wait for the download to finish
        """
        assert self.software_update.update_channel.default_channel ==\
               self.software_update.update_channel.channel,\
            'The update channel has been set correctly.'

        if self.wizard_state == 'downloadAndInstall':
            install_button = self.marionette.find_element(By.ID, 'downloadAndInstallButton')
            install_button.click()

        # Wait for the download to start
        Wait(self.marionette).until(
            lambda _: self.wizard_state != 'downloadAndInstall')

        # If there are incompatible addons we fallback on old software update dialog for updating
        if self.wizard_state == 'applyBillboard':
            update_button = self.marionette.find_element(By.ID, 'updateButton')
            update_button.click()

            # The rest of the code inside this `if` uses the update wizard which is
            # not being converted yet
            #
            # The current JS code is:
            #
            #     var wizard = updateWizard.handleUpdateWizardDialog();
            #     wizard.waitForWizardPage(updateWizard.WIZARD_PAGES.updatesfoundbasic);
            #     wizard.download();
            #     wizard.close();
            #     this._downloadDuration = wizard._downloadDuration;
            #
            #     return;

        if wait_for_finish:
            start_time = datetime.now()
            self._wait_for_download_finished(timeout)
            self.download_duration = datetime.now() - start_time

    def _wait_for_download_finished(self, timeout):
        """ Waits until download is completed

        :param timeout: How long to wait for the download to complete
        """

        Wait(self.marionette, timeout).until(
            lambda _: self.wizard_state != 'downloading',
            message='Download has been completed.')

        assert self.wizard_state != 'downloadFailed'

    def wait_for_update_applied(self, timeout=TIMEOUT_UPDATE_APPLY):
        """ Waits until the downloaded update has been applied

        :param timeout: How long to wait for the update to apply
        """

        Wait(self.marionette, timeout).until(
            lambda _: self.wizard_state == 'apply',
            message='Final wizard page has been selected.')

        Wait(self.marionette, timeout).until(
            lambda _: 'applied' in self.software_update.active_update.state,
            message='Update has been applied.')
