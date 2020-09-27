#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright 2019-2020 Christopher J. Kucera
# <cj@apocalyptech.com>
# <http://apocalyptech.com/contact.php>
#
# This file is part of Borderlands 3 ModCabinet Sorter.
#
# Borderlands 3 ModCabinet Sorter is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3 of
# the License, or (at your option) any later version.
#
# Borderlands 3 ModCabinet Sorter is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Borderlands 3 ModCabinet Sorter.  If not, see
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

    def test_two(self):
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line('testing2')
        self.assertEqual(self.modfile.mod_desc, ['testing', 'testing2'])

    def test_double_empty(self):
        self.modfile.add_comment_line('testing')
        self.modfile.add_comment_line('')
        self.modfile.add_comment_line('')
        self.assertEqual(self.modfile.mod_desc, ['testing', ''])

