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
from bl3cabinetsorter.app import DirInfo

class DirInfoTests(unittest.TestCase):
    """
    Testing our DirInfo class.  Nearly everything interesting happens
    in the constructor.
    """

    base_dir = '/tmp/doesnotexist'

    def new_dirinfo(self, path, filenames):
        """
        Creates a new DirInfo object based on the given `path`, with the
        specified list of `filenames`.
        """
        full_path = os.path.join(self.base_dir, path)
        return DirInfo(self.base_dir, full_path, filenames)

    def test_no_files(self):
        info = self.new_dirinfo('', [])
        self.assertEqual(list(info.get_all()), [])
        self.assertEqual(info.get_all_no_ext(), [])

    def test_author_level_1(self):
        dirname = 'BL2 Mods'
        info = self.new_dirinfo(dirname, [])
        self.assertEqual(info.dir_author, '(unknown)')

    def test_author_level_2(self):
        author = 'Username'
        dirname = 'BL2 Mods/{}'.format(author)
        info = self.new_dirinfo(dirname, [])
        self.assertEqual(info.dir_author, author)

    def test_author_level_3(self):
        author = 'Username'
        dirname = 'BL2 Mods/{}/Mod Name'.format(author)
        info = self.new_dirinfo(dirname, [])
        self.assertEqual(info.dir_author, author)

    def test_one_file_no_ext(self):
        dirname = 'BL2 Mods/Username'
        filename = 'filename'
        info = self.new_dirinfo(dirname, [filename])
        # Lots of stuff getting tested, actually
        self.assertIn(filename, info)
        self.assertIn(filename.upper(), info)
        self.assertEqual(info[filename], info[filename.upper()])
        self.assertEqual(info[filename], os.path.join(self.base_dir, dirname, filename))
        self.assertEqual(info.get_all_no_ext(), [filename])
        (dirpath, rel_path) = info.get_rel_path(filename)
        self.assertEqual(dirpath, dirname)
        self.assertEqual(rel_path, os.path.join(dirname, filename))
        self.assertEqual(info.extension_map, {})
        self.assertEqual(info.readme, None)
        self.assertEqual(info.get_all_with_ext('txt'), [])

    def test_one_file_with_ext(self):
        dirname = 'BL2 Mods/Username'
        filename = 'filename.txt'
        info = self.new_dirinfo(dirname, [filename])
        self.assertIn(filename, info)
        self.assertEqual(info.get_all_no_ext(), [])
        self.assertEqual(info.get_all_with_ext('txt'), [filename])

    def test_two_files_with_ext(self):
        dirname = 'BL2 Mods/Username'
        filename1 = 'filename1.txt'
        filename2 = 'filename2.txt'
        info = self.new_dirinfo(dirname, [filename1, filename2])
        self.assertIn(filename1, info)
        self.assertIn(filename2, info)
        self.assertEqual(info.get_all_no_ext(), [])
        self.assertEqual(sorted(info.get_all_with_ext('txt')), [filename1, filename2])

    def test_readme(self):
        dirname = 'BL2 Mods/Username'
        filename = 'readme.txt'
        info = self.new_dirinfo(dirname, [filename])
        self.assertIn(filename, info)
        self.assertEqual(info.get_all_with_ext('txt'), [filename])
        self.assertEqual(info.readme, filename)

    def test_readme_inner(self):
        dirname = 'BL2 Mods/Username'
        filename = 'zzzreadmezzz.txt'
        info = self.new_dirinfo(dirname, [filename])
        self.assertIn(filename, info)
        self.assertEqual(info.get_all_with_ext('txt'), [filename])
        self.assertEqual(info.readme, filename)

