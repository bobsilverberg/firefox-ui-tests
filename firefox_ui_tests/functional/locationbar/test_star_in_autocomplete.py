# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from marionette.errors import NoSuchElementException

from firefox_ui_harness.decorators import skip_under_xvfb
from firefox_ui_harness.testcase import FirefoxTestCase


class TestStarInAutocomplete(FirefoxTestCase):
    """ This replaces
    http://hg.mozilla.org/qa/mozmill-tests/file/default/firefox/tests/functional/testAwesomeBar/testSuggestBookmarks.js
    Check a star appears in autocomplete list for a bookmarked page.
    """

    PREF_LOCATION_BAR_SUGGEST = 'browser.urlbar.default.behavior'

    def setUp(self):
        FirefoxTestCase.setUp(self)

        self.clean_up_state()

        # Location bar suggests 'History and Bookmarks'
        self.prefs.set_pref(self.PREF_LOCATION_BAR_SUGGEST, 0)

    def tearDown(self):
        # Close the autocomplete results
        try:
            self.browser.navbar.locationbar.autocomplete_results.close()
            self.places.restore_default_bookmarks()
        except NoSuchElementException:
            pass
        finally:
            FirefoxTestCase.tearDown(self)

    def clean_up_state(self):
        with self.marionette.using_context('content'):
            self.marionette.navigate('about:blank')

        self.places.remove_all_history()

    @skip_under_xvfb
    def test_star_in_autocomplete(self):
        search_string = 'grants'

        with self.marionette.using_context('content'):
            self.marionette.navigate(self.marionette.absolute_url('layout/mozilla_grants.html'))

        # TODO: Convert to l10n friendly accessor when menu library is available
        self.browser.menubar.select('Bookmarks', 'Bookmark This Page')
        # TODO: Replace hard-coded selector with library method when one is available
        done_button = self.marionette.find_element('id', 'editBookmarkPanelDoneButton')
        self.wait_for_condition(lambda mn: done_button.is_displayed)
        done_button.click()

        self.clean_up_state()

        locationbar = self.browser.navbar.locationbar
        # TODO: Replace with places.wait_for_visited when observers have been implemented
        # https://bugzilla.mozilla.org/show_bug.cgi?id=1121691
        # The data for autocomplete does not load immediately and we cannot wait for an observer
        # until the bug 1121731 is complete
        time.sleep(4)
        locationbar.clear()
        locationbar.urlbar.send_keys(search_string)
        autocomplete_results = locationbar.autocomplete_results

        self.wait_for_condition(lambda mn: locationbar.value == search_string)
        self.wait_for_condition(lambda mn: autocomplete_results.is_open)
        self.wait_for_condition(lambda mn: len(autocomplete_results.visible_results) == 1)

        first_result = autocomplete_results.visible_results[0]
        matching_titles = autocomplete_results.get_matching_text(first_result, 'title')
        for title in matching_titles:
            self.wait_for_condition(lambda mn: search_string.lower() == title.lower())
        self.assertIn('bookmark',
                      first_result.get_attribute('type'),
                      'The auto-complete result is a bookmark')
