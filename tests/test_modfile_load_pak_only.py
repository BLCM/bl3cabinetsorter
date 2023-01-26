#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Copyright 2019-2022 Christopher J. Kucera
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

import io
import unittest
from bl3cabinetsorter.app import ModFile, NotAModFile

class ModFileTextPakOnlyTests(unittest.TestCase):
    """
    Testing importing a pakfile-only mod description file.
    """

    valid_categories = {
            'qol': 'Quality of Life',
            }

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.errors = []
        self.modfile = ModFile(0, error_list=self.errors, valid_categories=self.valid_categories)
        self.modfile.full_filename = 'modname.bl3pakinfo'
        self.modfile.is_pak_only = True
        self.df = io.StringIO()

    def set_df_contents(self, lines):
        """
        Sets the contents of the "file" that we're gonna read in.
        """
        for line in lines:
            print(line, file=self.df)
        self.df.seek(0)

    def test_load_no_pakfile(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No pakfile found', str(cm.exception))

    def test_load_minimum_headers(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@pakfile a_mod_9999_p.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.pakfile, 'a_mod_9999_p.pak')
        self.assertFalse(self.modfile.has_errors())

