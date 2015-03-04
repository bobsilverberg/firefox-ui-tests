# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver import By

from firefox_ui_harness.testcase import FirefoxTestCase


class TestAboutWindow(FirefoxTestCase):

    def setUp(self):
        FirefoxTestCase.setUp(self)

        self.about_window = self.browser.open_about_window(trigger='menu')

    def tearDown(self):
        try:
            self.windows.close_all([self.browser])
        finally:
            FirefoxTestCase.tearDown(self)

    def test_basic(self):
        self.assertEqual(self.about_window.window_type, 'Browser:About')

    def test_check_for_updates_and_download(self):
        # testing both of these as they need to occur in this order
        self.about_window.check_for_updates()
        self.assertEqual('downloadAndInstall', self.about_window.wizard_state)
        self.about_window.download()
        self.assertEqual('apply', self.about_window.wizard_state)

    def test_close_window(self):
        """Test closing the About window."""
        self.about_window.close()
        self.assertTrue(self.about_window.closed)

    def test_open_window(self):
        """Test various opening strategies."""
        def opener(win):
            menu = win.marionette.find_element(By.ID, 'aboutName')
            menu.click()

        open_strategies = ('menu',
                           opener,
                           )

        for trigger in open_strategies:
            if not self.about_window.closed:
                self.about_window.close()
            about_window = self.browser.open_about_window(trigger=trigger)
            self.assertEquals(about_window, self.windows.current)
            about_window.close()

    def test_patch_info(self):
        self.assertTrue(self.about_window.patch_info['download_duration'])
        self.assertTrue(self.about_window.patch_info['channel'])

    def test_updates_found(self):
        self.assertTrue(self.about_window.updates_found)

    def test_wizard_state(self):
        self.assertTrue(self.about_window.wizard_state)
