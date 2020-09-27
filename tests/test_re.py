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

import re
import unittest
from bl3cabinetsorter.app import Re

class ReTests(unittest.TestCase):
    """
    Testing our little regex-helper class.  Not especially interesting,
    and it really doesn't even *need* testing, but I've gotten hung up
    on 100% coverage.
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.re = Re()

    def test_match(self):
        compiled = re.compile('^hello$')
        self.assertIsNotNone(self.re.match(compiled, 'hello'))
        self.assertEqual(self.re.last_match.group(0), 'hello')

    def test_no_match(self):
        compiled = re.compile('^hello$')
        self.assertIsNone(self.re.match(compiled, 'goodbye'))
        self.assertEqual(self.re.last_match, None)

    def test_search(self):
        compiled = re.compile('(hello)')
        self.assertIsNotNone(self.re.search(compiled, 'hi hello frotz'))
        self.assertEqual(self.re.last_match.group(1), 'hello')

    def test_no_search(self):
        compiled = re.compile('(hello)')
        self.assertIsNone(self.re.search(compiled, 'hi goodbye frotz'))
        self.assertEqual(self.re.last_match, None)
