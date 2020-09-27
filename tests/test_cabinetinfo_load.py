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

class CabinetInfoLoadTests(unittest.TestCase):
    """
    Testing loading files in CabinetInfo
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
        self.info = CabinetInfo(0)
        self.df = io.StringIO()

    def load(self, lines):
        """
        Loads the given lines as if they were a CabinetInfo file
        """
        # Set up the "file"
        for line in lines:
            print(line, file=self.df)
        self.df.seek(0)

        # Read from it
        self.info.load_from_file(self.df, 'cabinet.info', self.errors, self.valid_cats)

    def test_single_unnamed_mod(self):
        self.load([
            'cat1',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn(None, self.info)
        self.assertEqual(self.info[None].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, True)
        self.assertEqual(len(self.errors), 0)

    def test_single_named_mod(self):
        self.load([
            'modname: cat1',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn('modname', self.info)
        self.assertEqual(self.info['modname'].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, False)
        self.assertEqual(len(self.errors), 0)

    def test_comment_lines(self):
        self.load([
            '# Comment!',
            'cat1',
            '# Comment!',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn(None, self.info)
        self.assertEqual(self.info[None].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, True)
        self.assertEqual(len(self.errors), 0)

    def test_empty_lines(self):
        self.load([
            '',
            'cat1',
            '',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn(None, self.info)
        self.assertEqual(self.info[None].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, True)
        self.assertEqual(len(self.errors), 0)

    def test_empty_file(self):
        self.load([
            ])
        self.assertEqual(len(self.info), 0)
        self.assertEqual(len(self.errors), 0)

    def test_double_one_mod_definitions(self):
        self.load([
            'cat1',
            'cat2',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn(None, self.info)
        self.assertEqual(self.info[None].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, True)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('Unknown line', self.errors[0])

    def test_specific_after_unnamed(self):
        self.load([
            'cat1',
            'modname: cat2',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn(None, self.info)
        self.assertEqual(self.info[None].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, True)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('Unknown line', self.errors[0])

    def test_unnamed_after_specific(self):
        self.load([
            'modname: cat1',
            'cat2',
            ])
        self.assertEqual(len(self.info), 1)
        self.assertIn('modname', self.info)
        self.assertEqual(self.info['modname'].categories, ['cat1'])
        self.assertEqual(self.info.single_mod, False)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('Unknown line', self.errors[0])

    def test_two_named(self):
        self.load([
            'modname: cat1',
            'mod2: cat2',
            ])
        self.assertEqual(len(self.info), 2)
        self.assertIn('modname', self.info)
        self.assertIn('mod2', self.info)
        self.assertEqual(self.info['modname'].categories, ['cat1'])
        self.assertEqual(self.info['mod2'].categories, ['cat2'])
        self.assertEqual(self.info.single_mod, False)
        self.assertEqual(len(self.errors), 0)

    def test_single_url(self):
        for modname in [None, 'modname']:
            with self.subTest(modname=modname):
                for proto in 'http', 'https':
                    with self.subTest(proto=proto):
                        self.setUp()
                        url = '{}://site.com/foo'.format(proto)
                        if modname:
                            line = '{}: cat1'.format(modname)
                        else:
                            line = 'cat1'
                        self.load([
                            line,
                            url,
                            ])
                        self.assertEqual(len(self.info), 1)
                        self.assertEqual(len(self.errors), 0)
                        self.assertIn(modname, self.info)
                        self.assertEqual(self.info[modname].urls, [url])

    def test_multiple_urls(self):
        urls = [
                'http://site1.com/foo',
                'https://site2.net/bar',
                ]
        self.load([
            'modname: cat1',
            urls[0],
            urls[1],
            ])
        self.assertEqual(len(self.info), 1)
        self.assertEqual(len(self.errors), 0)
        self.assertIn('modname', self.info)
        self.assertEqual(self.info['modname'].urls, [urls[0], urls[1]])

    def test_only_url(self):
        self.load([
            'http://site.com/foo'
            ])
        self.assertEqual(len(self.info), 0)
        self.assertEqual(len(self.errors), 1)
        self.assertIn('previous modfile', self.errors[0])

    def test_url_interleaved_comments(self):
        url = 'http://site.com/foo'
        self.load([
            'modname: cat1',
            '',
            '# URL follows:',
            '',
            url,
            ''
            'modname2: cat2',
            ])
        self.assertEqual(len(self.errors), 0)
        self.assertEqual(len(self.info), 2)
        self.assertIn('modname', self.info)
        self.assertIn('modname2', self.info)
        self.assertEqual(self.info['modname'].categories, ['cat1'])
        self.assertEqual(self.info['modname2'].categories, ['cat2'])
        self.assertEqual(self.info['modname'].urls, [url])
        self.assertEqual(self.info['modname2'].urls, [])
