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

class ModFileCommentTests(unittest.TestCase):
    """
    Testing our add_comment_line method
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test
        """
        self.modfile = ModFile(0)

    def test_blank(self):
        self.modfile.add_comment_line('')
        self.assertEqual(self.modfile.mod_desc, [])

    def test_single(self):
        self.modfile.add_comment_line('testing')
        self.assertEqual(self.modfile.mod_desc, ['testing'])

    def test_strips(self):
        for char in ['/', '#', ' ', "\n", "\r", "\t"]:
            with self.subTest(char=char):
                self.modfile = ModFile(0)
                self.modfile.add_comment_line('{}testing{}'.format(char, char))
                self.assertEqual(self.modfile.mod_desc, ['testing'])

    def test_all_strips(self):
        self.modfile.add_comment_line("/#\n\r\t testing/#\n\r\t")
        self.assertEqual(self.modfile.mod_desc, ['testing'])

    def test_two(self):
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line('testing2')
        self.assertEqual(self.modfile.mod_desc, ['testing', 'testing2'])

    def test_double_empty(self):
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line('')
        self.modfile.add_comment_line('')
        self.assertEqual(self.modfile.mod_desc, ['testing', ''])

    def test_initial_ascii_art(self):
        for char in ['_', '/', '\\', '.', ':', '|', '#', '~', ' ', "\t"]:
            with self.subTest(char=char):
                self.modfile = ModFile(0)
                self.modfile.add_comment_line(char)
                self.assertEqual(self.modfile.mod_desc, [])

    def test_after_ascii_art_no_whitespace_or_comments(self):
        for char in ['_', '\\', '.', ':', '|', '~']:
            with self.subTest(char=char):
                self.modfile = ModFile(0)
                self.modfile.add_comment_line('testing')
                self.modfile.add_comment_line(char)
                self.assertEqual(self.modfile.mod_desc, ['testing', char])

    def test_initial_ascii_art_all(self):
        self.modfile.add_comment_line("_/\\.:| \t#~")
        self.assertEqual(self.modfile.mod_desc, [])

    def test_initial_ascii_art_after(self):
        art = "_/\\.:|# \t~"
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line(art)
        self.assertEqual(self.modfile.mod_desc, ['testing', art])

    def test_matched_title(self):
        title = 'Mod Title'
        self.assertEqual(self.modfile.mod_title, None)
        self.modfile.add_comment_line(title, match_title=title)
        self.assertEqual(self.modfile.mod_title, title)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_close_title(self):
        title = 'Mod Title'
        self.assertEqual(self.modfile.mod_title, None)
        self.modfile.add_comment_line(title, match_title='{}z'.format(title))
        self.assertEqual(self.modfile.mod_title, title)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_unmatched_title(self):
        title = 'Mod Title'
        self.assertEqual(self.modfile.mod_title, None)
        self.modfile.add_comment_line(title, match_title='Totally Different')
        self.assertEqual(self.modfile.mod_title, None)
        self.assertEqual(self.modfile.mod_desc, [title])

    def test_matched_title_not_first(self):
        title = 'Mod Title'
        self.assertEqual(self.modfile.mod_title, None)
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line(title, match_title=title)
        self.assertEqual(self.modfile.mod_title, None)
        self.assertEqual(self.modfile.mod_desc, ['testing', title])
