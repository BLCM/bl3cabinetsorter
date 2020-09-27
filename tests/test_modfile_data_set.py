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

# TODO: These tests are failing even on the original cabinetsorter.
# Get that sorted out.
@unittest.skip("Skipping broken ModFileDataSetTest tests...")
class ModFileDataSetTests(unittest.TestCase):
    """
    Testing our various ModFile data-setting methods (mostly to make sure
    that we're setting our Cacheable statuses properly.
    """

    def test_readme_unchanged(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UNKNOWN),
                (ModFile.S_CACHED, ModFile.S_CACHED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, initial_status)

                modfile.update_readme_desc([])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, end_status)

    def test_readme_updated(self):
        for (initial_status, end_status) in [
                (ModFile.S_UNKNOWN, ModFile.S_UPDATED),
                (ModFile.S_CACHED, ModFile.S_UPDATED),
                (ModFile.S_NEW, ModFile.S_NEW),
                (ModFile.S_UPDATED, ModFile.S_UPDATED),
                ]:
            with self.subTest(initial_status=initial_status):
                modfile = ModFile(0, initial_status=initial_status)
                self.assertFalse(modfile.seen)
                self.assertEqual(modfile.readme_desc, [])
                self.assertEqual(modfile.status, initial_status)

                modfile.update_readme_desc(['readme'])

                self.assertTrue(modfile.seen)
                self.assertEqual(modfile.readme_desc, ['readme'])
                self.assertEqual(modfile.status, end_status)
