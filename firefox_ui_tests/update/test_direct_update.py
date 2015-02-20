# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
import time

from marionette import By

from firefox_ui_harness.decorators import skip_under_xvfb
from firefox_ui_harness.testcase import FirefoxTestCase


class TestDirectUpdate(FirefoxTestCase):
    """ This replaces
    http://hg.mozilla.org/qa/mozmill-tests/file/e16ab8d3d62d/firefox/tests/update/testDirectUpdate/testUpdate.js
    Tests for direct updates
    """

    # The name of the Firefox app
    APP_NAME = 'Nightly'

    # preferences
    PREF_UPDATE_AUTO = 'app.update.auto'
    PREF_UPDATE_LOG = 'app.update.log'
    PREF_UPDATE_URL_OVERRIDE = 'app.update.url.override'

    def setUp(self):
        FirefoxTestCase.setUp(self)


        self.software_update.init_update_tests(False)

        # Turn on software update logging
        self.prefs.set_pref(self.PREF_UPDATE_LOG, True)
        self.prefs.set_pref(self.PREF_UPDATE_AUTO, False)

        # If requested force a specific update URL
        # TODO: Not sure how we're going to address this `persisted` stuff yet
        # if (persisted.update.update_url):
        #     self.prefs.set_pref(self.PREF_UPDATE_URL_OVERRIDE, persisted.update.update_url)

    def tearDown(self):
        # Close the autocomplete results
        try:
            pass
            # self.browser.navbar.locationbar.autocomplete_results.close()
            # self.places.restore_default_bookmarks()
        finally:
            FirefoxTestCase.tearDown(self)

    def test_check_and_download_update(self):

        # Check if the user has permissions to run the update
        self.assertTrue(self.software_update.allowed, 'User has permissions to update the build')

        # Open the about dialog and check for updates

        # I couldn't figure out how to open the about menu item via self.browser.menubar.select()
        # TODO: Hardcoded selector

        def open_about():
            about_menu = self.marionette.find_element(By.ID, 'aboutName')
            about_menu.click()

        import pdb
        pdb.set_trace()

        open_about()
        self.windows.switch_to(self.windows.focused_chrome_window_handle)
        time.sleep(5)

        # self.windows.open_window(open_about)

        check_for_updates_button = self.marionette.find_element(By.ID, 'checkForUpdatesButton')
        check_for_updates_button.click()

        time.sleep(5)

        download_updates_button = self.marionette.find_element(By.ID, 'downloadAndInstallButton')
        download_updates_button.click()

        time.sleep(5)

        print self.software_update.active_update.patch_count

        #
        # self.browser.menubar.select(self.APP_NAME, 'About %s' % self.APP_NAME)
        # # aboutWindow.checkForUpdates();
        #
        # # Bookmark the current page using the bookmark menu
        # # TODO: Convert to l10n friendly accessor when menu library is available
        # self.browser.menubar.select('Bookmarks', 'Bookmark This Page')
        # # TODO: Replace hard-coded selector with library method when one is available
        # self.wait_for_condition(lambda mn: done_button.is_displayed)
        # done_button.click()
        #
        # # We must open the blank page so the autocomplete result isn't "Switch to tab"
        # with self.marionette.using_context('content'):
        #     self.marionette.navigate('about:blank')
        #
        # self.places.remove_all_history()
        #
        # # Focus the locationbar, delete any contents there, and type the search string
        # locationbar = self.browser.navbar.locationbar
        # locationbar.clear()
        # locationbar.urlbar.send_keys(search_string)
        # autocomplete_results = locationbar.autocomplete_results
        #
        # # Wait for the search string to be present, for the autocomplete results to appear
        # # and for there to be exactly one autocomplete result
        # self.wait_for_condition(lambda mn: locationbar.value == search_string)
        # self.wait_for_condition(lambda mn: autocomplete_results.is_open)
        # self.wait_for_condition(lambda mn: len(autocomplete_results.visible_results) == 1)
        #
        # # Compare the highlighted text in the autocomplete result to the search string
        # first_result = autocomplete_results.visible_results[0]
        # matching_titles = autocomplete_results.get_matching_text(first_result, 'title')
        # for title in matching_titles:
        #     self.wait_for_condition(lambda mn: title.lower() == search_string)
        #
        # self.assertIn('bookmark',
        #               first_result.get_attribute('type'),
        #               'The auto-complete result is a bookmark')
