# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from firefox_ui_harness.testcase import FirefoxTestCase


class TestSoftwareUpdate(FirefoxTestCase):

    def setUp(self):
        FirefoxTestCase.setUp(self)
        self.saved_channel = self.software_update.update_channel.default_channel
        self.saved_mar_channels = self.software_update.mar_channels.channels
        self.software_update.update_channel.set_default_channel('expected_channel')
        self.software_update.mar_channels.set_channels(['expected', 'channels'])

        # Override the update url
        # self.prefs.set_pref(
        #     'app.update.url',
        #     'file:///Users/bsilverberg/gitRepos/firefox-ui-tests/mine/update.xml')

    def tearDown(self):
        self.software_update.update_channel.set_default_channel(self.saved_channel)
        self.software_update.mar_channels.set_channels(self.saved_mar_channels)
        FirefoxTestCase.tearDown(self)

    def test_abi(self):
        self.assertTrue(self.software_update.ABI)

    def test_active_update(self):
        # TODO: I cannot seem to get active_update to work

        self.assertEqual(2, self.software_update.active_update.patch_count)

    def test_allowed(self):
        self.assertEqual(True, self.software_update.allowed)

    def test_build_info(self):
        build_info = self.software_update.build_info
        self.assertEqual(None, build_info['disabled_addons'])
        self.assertIn('Mozilla/', build_info['user_agent'])
        self.assertEqual(build_info['mar_channels'], ['expected', 'channels'])
        self.assertTrue(build_info['version'])
        self.assertTrue(build_info['buildid'].isdigit())
        self.assertTrue(build_info['locale'])
        self.assertIn('force=1', build_info['url_aus'])
        self.assertEqual(self.software_update.update_channel.channel, build_info['channel'])

    # def test_is_complete_update(self):
    #     # TODO: Not sure how to set this up,
    #     # plus active_update isn't currently working
    #
    #     self.assertEqual(True, self.software_update.is_complete_update)

    def test_update_url(self):
        self.assertIn('Firefox', self.software_update.update_url())
        self.assertIn('Firefox', self.software_update.update_url(True))
        self.assertIn('force=1', self.software_update.update_url(True))

    def test_update_channel_channel(self):
        self.assertEqual(self.saved_channel, self.software_update.update_channel.channel)

    def test_update_channel_default_channel(self):
        self.assertEqual('expected_channel', self.software_update.update_channel.default_channel)

    def test_update_channel_set_default_channel(self):
        self.software_update.update_channel.set_default_channel('new_channel')
        self.assertEqual('new_channel', self.software_update.update_channel.default_channel)

    def test_mar_channels_channels(self):
        self.assertEqual(['expected', 'channels'], self.software_update.mar_channels.channels)

    def test_mar_channels_set_channels(self):
        self.software_update.mar_channels.set_channels(['a', 'b', 'c'])
        self.assertEqual(['a', 'b', 'c'], self.software_update.mar_channels.channels)

    def test_mar_channels_add_channels(self):
        self.software_update.mar_channels.add_channels(['some', 'new', 'channels'])
        self.assertEqual(
            ['expected', 'channels', 'some', 'new', 'channels'],
            self.software_update.mar_channels.channels)

    def test_mar_channels_remove_channels(self):
        self.software_update.mar_channels.remove_channels(['expected'])
        self.assertEqual(['channels'], self.software_update.mar_channels.channels)
