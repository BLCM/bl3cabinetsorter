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
from bl3cabinetsorter.app import Readme

class ReadmeReadFileObjTests(unittest.TestCase):
    """
    Testing reading our README files
    """

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.readme = Readme(0)
        self.df = io.StringIO()

    def set_df_contents(self, lines):
        """
        Sets the contents of the "file" that we're gonna read in.
        """
        for line in lines:
            print(line, file=self.df)
        self.df.seek(0)

    def read(self):
        """
        Read in our file.  Note that the `is_markdown` flag is
        currently not actually used, so we're not bothering to
        test for it at all.
        """
        self.readme.read_file_obj(self.df, False)

    def test_load_empty(self):
        self.set_df_contents([])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            })

    def test_initial_comment(self):
        self.set_df_contents([
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_initial_two_comments(self):
        self.set_df_contents([
            'Testing',
            'Testing 2',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing', 'Testing 2'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_hash_section(self):
        for hashes in ['#', '##', '###', '####']:
            with self.subTest(hashes=hashes):
                self.set_df_contents([
                    '{} Section'.format(hashes),
                    'Testing',
                    ])
                self.read()
                self.assertEqual(self.readme.mapping, {
                    '(default)': [],
                    'section': ['Testing'],
                    })
                self.assertEqual(self.readme.first_section, 'section')

    def test_default_and_one_hash_section(self):
        self.set_df_contents([
            'Initial',
            '# Section',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Initial'],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_one_hash_section_two_lines(self):
        self.set_df_contents([
            '# Section',
            'Testing',
            'Testing 2',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing', 'Testing 2'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_double_underline_section(self):
        self.set_df_contents([
            'Section',
            '=======',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_single_underline_section(self):
        self.set_df_contents([
            'Section',
            '-------',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_initial_double_line(self):
        self.set_df_contents([
            '=======',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['=======', 'Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_initial_single_line(self):
        self.set_df_contents([
            '-------',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['-------', 'Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_dash_section(self):
        self.set_df_contents([
            '- Section',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_two_sections(self):
        self.set_df_contents([
            '- Section',
            'Testing',
            '# Section 2',
            'More Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            'section 2': ['More Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_two_sections_multiline(self):
        self.set_df_contents([
            'Initial',
            'Text',
            '- Section',
            'Testing',
            'Foo',
            '# Section 2',
            'More Testing',
            'Bar',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Initial', 'Text'],
            'section': ['Testing', 'Foo'],
            'section 2': ['More Testing', 'Bar'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_initial_default_blank(self):
        self.set_df_contents([
            '',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_initial_default_blank_double(self):
        self.set_df_contents([
            '',
            '',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_initial_section_blank(self):
        self.set_df_contents([
            '- Section',
            '',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_initial_section_blank_double(self):
        self.set_df_contents([
            '- Section',
            '',
            '',
            'Testing',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_trailing_blank(self):
        self.set_df_contents([
            'Testing',
            '',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_trailing_section_blank(self):
        self.set_df_contents([
            '# Section',
            'Testing',
            '',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': [],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, 'section')

    def test_two_trailing_section_blank(self):
        self.set_df_contents([
            'Main',
            '',
            '# Section',
            'Testing',
            '',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Main'],
            'section': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')

    def test_double_trailing_blank(self):
        self.set_df_contents([
            'Testing',
            '',
            '',
            ])
        self.read()
        self.assertEqual(self.readme.mapping, {
            '(default)': ['Testing'],
            })
        self.assertEqual(self.readme.first_section, '(default)')
