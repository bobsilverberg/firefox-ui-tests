# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver import By

from ...base import UIBaseLib


class Deck(UIBaseLib):

    def _click_deck_button(self, element_id):
        button = self.marionette.find_element(By.ID, element_id)
        button.click()

    @property
    def wizard_state(self):
        """ Returns the current state of the update wizard."""
        return self.marionette.execute_script("""
          return arguments[0].selectedPanel.id;
        """, script_args=[self.element])

    def click_check_for_updates_button(self):
        """Clicks on "Check for Updates" button."""
        self._click_deck_button('checkForUpdatesButton')

    def click_update_button(self):
        """Clicks on "Update" button."""
        self._click_deck_button('updateButton')

    def click_download_button(self):
        """Clicks on "Download" button."""
        self._click_deck_button('downloadAndInstallButton')
