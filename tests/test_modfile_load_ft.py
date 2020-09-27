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

class ModFileFTTests(unittest.TestCase):
    """
    Testing importing a FilterTool-formatted file
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test.  FT format is not especially
        structured, so not a lot of work to do here.
        """
        self.modfile = ModFile(0)
        self.df = io.StringIO()

    def set_df_contents(self, cat_name, lines):
        """
        Sets the contents of the "file" that we're gonna read in.  We enforce a bit
        of FilterTool-style formatting in here, though it's quite a bit more freeform
        than BLCMM.  There'll be empty lines inbetween everything, though
        """
        print('#<{}>'.format(cat_name), file=self.df)
        print('', file=self.df)
        for line in lines:
            print(line, file=self.df)
            print('', file=self.df)
        print('#</{}>'.format(cat_name), file=self.df)
        print('', file=self.df)
        print('set Transient.SparkServiceConfiguration_6 Keys ("whatever")', file=self.df)
        self.df.seek(0)

    def test_load_commentless(self):
        self.set_df_contents('Mod Name', [
            'set foo bar baz',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.mod_desc, [])

    def test_one_comment(self):
        self.set_df_contents('Mod Name', [
            'Testing',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_two_comments(self):
        self.set_df_contents('Mod Name', [
            'Testing',
            'Testing 2',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing', 'Testing 2'])

    def test_two_comments_interrupted(self):
        self.set_df_contents('Mod Name', [
            'Testing',
            'set foo bar baz',
            'Testing 2',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_two_comments_interrupted_cat(self):
        self.set_df_contents('Mod Name', [
            'Testing',
            '#<Category>',
            'Testing 2',
            '#</Category>',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_two_comments_interrupted_hotfix(self):
        self.set_df_contents('Mod Name', [
            'Testing',
            '#<hotfix><key>test</key><value>moretest</value></hotfix>',
            'Testing 2',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

    def test_comment_nested_cat(self):
        self.set_df_contents('Mod Name', [
            '#<Category>',
            'Testing',
            '#</Category>',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_comment_nested_cat_description(self):
        self.set_df_contents('Mod Name', [
            '#<Description>',
            'Testing',
            '#</Description>',
            ])
        self.modfile.load_ft(self.df)
        self.assertEqual(self.modfile.mod_desc, ['Testing'])

