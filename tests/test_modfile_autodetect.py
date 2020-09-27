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

import os
import shutil
import unittest
import tempfile
from bl3cabinetsorter.app import ModFile, DirInfo

class ModFileAutodetectTests(unittest.TestCase):
    """
    Testing the file-type autodetection in ModFile initialization
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test
        """
        self.tmpdir = tempfile.mkdtemp()
        self.mod_dir = 'BL2/Author Name'
        self.full_mod_dir = os.path.join(self.tmpdir, self.mod_dir)
        self.dirinfo = DirInfo('/tmp/doesnotexist', self.full_mod_dir, [])
        os.makedirs(self.full_mod_dir, exist_ok=True)

    def tearDown(self):
        """
        Cleanup tasks after every test
        """
        shutil.rmtree(self.tmpdir)

    def make_file(self, filename, lines):
        """
        Creates a file inside `path` named `filename`, containing the
        list of strings `lines` as its contents.
        """
        full_file = os.path.join(self.full_mod_dir, filename)
        with open(full_file, 'w') as df:
            for line in lines:
                print(line, file=df)
        self.dirinfo.lower_mapping[filename.lower()] = os.path.join(self.full_mod_dir, filename)

    def test_blcmm(self):
        # Obviously fudging the format a bit, whatever.
        self.make_file('filename', [
            '<BLCMM v="1">',
            '<category name="Mod Name">',
            '<comment>Testing Mod</comment>',
            '</category>',
            '</BLCMM>',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'Mod Name')
        self.assertEqual(mf.mod_desc, ['Testing Mod'])

    def test_ft(self):
        # Obviously fudging the format a bit, whatever.
        self.make_file('filename', [
            '#<Mod Name>',
            'Testing Mod',
            '#</Mod Name>',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'Mod Name')
        self.assertEqual(mf.mod_desc, ['Testing Mod'])

    def test_blank_first_line(self):
        # Obviously fudging the format a bit, whatever.
        self.make_file('filename', [
            '',
            '#<Mod Name>',
            'Testing Mod',
            '#</Mod Name>',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'Mod Name')
        self.assertEqual(mf.mod_desc, ['Testing Mod'])

    def test_blank_first_two_lines(self):
        # This should actually end up getting classified as an Unknown file,
        # at the moment.
        self.make_file('filename', [
            '',
            '',
            '#<Mod Name>',
            'Testing Mod',
            '#</Mod Name>',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'filename')
        self.assertEqual(mf.mod_desc, ['<Mod Name>', 'Testing Mod', '</Mod Name>'])

    def test_unknown(self):
        # Obviously fudging the format a bit, whatever.
        self.make_file('filename', [
            '# Filename!',
            'Testing Mod',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'Filename!')
        self.assertEqual(mf.mod_desc, ['Testing Mod'])

    def test_blank_line_at_end(self):
        # Obviously fudging the format a bit, whatever.
        self.make_file('filename', [
            '<BLCMM v="1">',
            '<category name="Mod Name">',
            '<comment>Testing Mod</comment>',
            '<comment></comment>',
            '</category>',
            '</BLCMM>',
            ])
        mf = ModFile(0, dirinfo=self.dirinfo, filename='filename')
        self.assertEqual(mf.seen, True)
        self.assertEqual(mf.mod_title, 'Mod Name')
        self.assertEqual(mf.mod_desc, ['Testing Mod'])
