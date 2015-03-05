# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from marionette_driver import By

from firefox_ui_harness.testcase import FirefoxTestCase


class TestAboutWindow(FirefoxTestCase):

    def setUp(self):
        FirefoxTestCase.setUp(self)

        self.about_window = self.browser.open_about_window()

    def tearDown(self):
        try:
            self.windows.close_all([self.browser])
        finally:
            FirefoxTestCase.tearDown(self)

    def test_basic(self):
        self.assertEqual(self.about_window.window_type, 'Browser:About')

    def test_elements(self):
        """Test correct retrieval of elements."""
        self.assertNotEqual(self.about_window.dtds, [])

        self.assertEqual(
            self.about_window.deck.element.get_attribute('localName'),
            'deck')

        # apply panel
        panel = self.about_window.deck.apply
        self.assertEqual(panel.element.get_attribute('localName'), 'hbox')
        self.assertEqual(panel.update_button.get_attribute('localName'), 'button')

        # apply_billboard panel
        panel = self.about_window.deck.apply_billboard
        self.assertEqual(panel.element.get_attribute('localName'), 'hbox')
        self.assertEqual(
            panel.apply_billboard_button.get_attribute('localName'),
            'button')

        # check_for_updates panel
        panel = self.about_window.deck.check_for_updates
        self.assertEqual(panel.element.get_attribute('localName'), 'hbox')
        self.assertEqual(
            panel.check_for_updates_button.get_attribute('localName'),
            'button')

        # checking_for_updates panel
        self.assertEqual(
            self.about_window.deck.checking_for_updates.element.get_attribute('localName'),
            'hbox')

        # download_and_install panel
        panel = self.about_window.deck.download_and_install
        self.assertEqual(panel.element.get_attribute('localName'), 'hbox')
        self.assertEqual(panel.download_button.get_attribute('localName'), 'button')

        # download_failed panel
        self.assertEqual(
            self.about_window.deck.download_failed.element.get_attribute('localName'),
            'hbox')

        # downloading panel
        self.assertEqual(
            self.about_window.deck.downloading.element.get_attribute('localName'),
            'hbox')

    def test_open_window(self):
        """Test various opening strategies."""
        def opener(win):
            menu = win.marionette.find_element(By.ID, 'aboutName')
            menu.click()

        open_strategies = ('menu',
                           opener,
                           )

        self.about_window.close()
        for trigger in open_strategies:
            about_window = self.browser.open_about_window(trigger=trigger)
            self.assertEquals(about_window, self.windows.current)
            about_window.close()

    def test_patch_info(self):
        self.assertEqual(self.about_window.patch_info['download_duration'], -1)
        self.assertNotEqual(self.about_window.patch_info['channel'], None)
