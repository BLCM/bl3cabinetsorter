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
from bl3cabinetsorter.app import ModFile

class ModFileUnknownTests(unittest.TestCase):
    """
    Testing importing an unknown-format file.  The main wrinkle here
    is that the filename is about the only reliable way of determining
    a mod title, and we're going to attempt to Levenshtein-match that
    name versus comment lines we read.
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.modfile = ModFile(0)
        self.modfile.full_filename = 'modname.txt'
        self.df = io.StringIO()

    def set_df_contents(self, lines):
        """
        Sets the contents of the "file" that we're gonna read in.
        """
        for line in lines:
            print(line, file=self.df)
        self.df.seek(0)

    def test_load_commentless(self):
        self.set_df_contents([
            'set foo bar baz',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'modname')
        self.assertEqual(self.modfile.mod_desc, [])

    def test_default_title_no_ext(self):
        self.modfile.full_filename='no_extension'
        self.set_df_contents([])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'no_extension')

    def test_default_title_multiple_ext(self):
        self.modfile.full_filename='filename.txt.txt'
        self.set_df_contents([])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'filename.txt')

    def test_set_title(self):
        self.set_df_contents([
            'Mod Name',
            'set foo bar baz',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.mod_desc, [])

    def test_set_title_and_comment(self):
        # 'Mod Name' matches the default 'modname' set in setUp()
        self.set_df_contents([
            'Mod Name',
            'Testing',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_load_one_comment(self):
        self.set_df_contents([
            'Testing',
            'set foo bar baz',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'modname')
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_load_two_comments(self):
        self.set_df_contents([
            'Testing',
            'Testing 2',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'modname')
        self.assertEqual(self.modfile.mod_desc, ['Testing', 'Testing 2'])

    def test_comment_after_set(self):
        self.set_df_contents([
            'set foo bar baz',
            'Testing',
            ])
        self.modfile.load_unknown(self.df)
        self.assertEqual(self.modfile.mod_title, 'modname')
        self.assertEqual(self.modfile.mod_desc, [])

