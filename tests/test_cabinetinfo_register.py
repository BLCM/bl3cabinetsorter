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

import io
import unittest
from bl3cabinetsorter.app import CabinetInfo

class CabinetInfoRegisterTests(unittest.TestCase):
    """
    Testing registering mods inside CabinetInfo
    """

    valid_cats = {
            'cat1': 'Category One',
            'cat2': 'Category Two',
            }

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.errors = []
        self.df = io.StringIO()
        self.info = CabinetInfo(0)
        self.info.load_from_file(self.df, 'cabinet.info', self.errors, self.valid_cats)

    def test_single_cat(self):
        self.assertEqual(self.info.register('xyzzy', 'cat1'), True)
        self.assertIn('xyzzy', self.info)
        self.assertEqual(self.info['xyzzy'].urls, [])
        self.assertEqual(self.info['xyzzy'].categories, ['cat1'])
        self.assertEqual(len(self.errors), 0)

    def test_two_cats(self):
        self.assertEqual(self.info.register('xyzzy', 'cat1, cat2'), True)
        self.assertIn('xyzzy', self.info)
        self.assertEqual(self.info['xyzzy'].urls, [])
        self.assertEqual(self.info['xyzzy'].categories, ['cat1', 'cat2'])
        self.assertEqual(len(self.errors), 0)

    def test_two_cats_strange_whitespace(self):
        self.assertEqual(self.info.register('xyzzy', '   cat1,   cat2 '), True)
        self.assertIn('xyzzy', self.info)
        self.assertEqual(self.info['xyzzy'].urls, [])
        self.assertEqual(self.info['xyzzy'].categories, ['cat1', 'cat2'])
        self.assertEqual(len(self.errors), 0)

    def test_duplicate_mod(self):
        self.assertEqual(self.info.register('xyzzy', 'cat1'), True)
        self.assertIn('xyzzy', self.info)
        self.assertEqual(len(self.errors), 0)
        self.assertEqual(self.info.register('xyzzy', 'cat2'), False)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('specified twice', self.errors[0])

    def test_invalid_category_no_valid(self):
        self.assertEqual(self.info.register('xyzzy', 'cat3'), False)
        self.assertNotIn('xyzzy', self.info)
        self.assertEqual(len(self.errors), 2)
        self.assertIn('Invalid category', self.errors[0])
        self.assertIn('No categories', self.errors[1])
        self.assertIn('xyzzy', self.errors[1])

    def test_invalid_category_one_valid(self):
        self.assertEqual(self.info.register('xyzzy', 'cat1, cat3'), True)
        self.assertIn('xyzzy', self.info)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('Invalid category', self.errors[0])
        self.assertEqual(self.info['xyzzy'].categories, ['cat1'])

    def test_no_mod_name_no_categories(self):
        """
        This one's weird, just testing that we say "the mod" when there's
        no actual name to report
        """
        self.assertEqual(self.info.register(None, 'cat3'), False)
        self.assertEqual(len(self.errors), 2)
        self.assertIn('the mod', self.errors[1])

    def test_modlist(self):
        """
        This doesn't strictly-speaking belong here, but whatever.  Not
        worth doing its own class for
        """
        self.assertEqual(self.info.register('mod', 'cat1'), True)
        self.assertEqual(len(self.info.modlist()), 1)
        self.assertIn(self.info['mod'], self.info.modlist())
