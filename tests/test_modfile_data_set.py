#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright 2019 Christopher J. Kucera
# <cj@apocalyptech.com>
# <http://apocalyptech.com/contact.php>
#
# This file is part of Borderlands ModCabinet Sorter.
#
# Borderlands ModCabinet Sorter is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Borderlands ModCabinet Sorter is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Borderlands ModCabinet Sorter.  If not, see
# <https://www.gnu.org/licenses/>.

import unittest
from bl3cabinetsorter.app import ModFile

class ModFileDataSetTests(unittest.TestCase):
    """
    Testing our various ModFile data-setting methods (mostly to make sure
    that we're setting our Cacheable statuses properly.
    """

    def test_categories_unchanged(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(list(modfile.categories), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_categories([])

                self.assertTrue(modfile.seen)
                self.assertEqual(list(modfile.categories), [])
                self.assertEqual(modfile.status, end_status)

    def test_categories_updated(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(list(modfile.categories), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_categories(['cat1'])

                self.assertTrue(modfile.seen)
                self.assertEqual(list(modfile.categories), ['cat1'])
                self.assertEqual(modfile.status, end_status)

    def test_urls_unchanged_empty(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([])

                self.assertTrue(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, end_status)

    def test_urls_unchanged_nexus(self):
        nexus_url = 'https://nexusmods.com/borderlands/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                modfile.nexus_link = nexus_url
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([nexus_url])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, end_status)

    def test_urls_updated_nexus(self):
        nexus_url = 'https://nexusmods.com/borderlands/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([nexus_url])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, end_status)

    def test_urls_unchanged_screenshot(self):
        screen_url = 'https://imgur.com/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                modfile.screenshots = [screen_url]
                self.assertFalse(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([screen_url])

                self.assertTrue(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, end_status)

    def test_urls_updated_screenshot(self):
        screen_url = 'https://imgur.com/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([screen_url])

                self.assertTrue(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, end_status)

    def test_urls_unchanged_both(self):
        nexus_url = 'https://nexusmods.com/borderlands/whatever'
        screen_url = 'https://imgur.com/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                modfile.screenshots = [screen_url]
                modfile.nexus_link = nexus_url
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([nexus_url, screen_url])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, end_status)

    def test_urls_updated_both(self):
        nexus_url = 'https://nexusmods.com/borderlands/whatever'
        screen_url = 'https://imgur.com/whatever'
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertIsNone(modfile.nexus_link)
                self.assertEqual(list(modfile.screenshots), [])
                self.assertEqual(modfile.status, initial_status)

                modfile.set_urls([nexus_url, screen_url])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.nexus_link, nexus_url)
                self.assertEqual(list(modfile.screenshots), [screen_url])
                self.assertEqual(modfile.status, end_status)

    def test_readme_unchanged(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, initial_status)

                modfile.update_readme_desc([])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, end_status)

    def test_readme_updated(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, initial_status)

                modfile.update_readme_desc(['readme'])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.readme_desc, ['readme'])
                self.assertEqual(modfile.status, end_status)
