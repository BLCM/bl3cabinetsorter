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

import io
import unittest
from bl3cabinetsorter.app import ModFile, NotAModFile

class ModFileTextHotfixesTests(unittest.TestCase):
    """
    Testing importing a text-hotfixes-format file.
    """

    valid_categories = {
            'qol': 'Quality of Life',
            'scaling': 'Scaling',
            'char-gunner': 'Gunner',
            }

    def setUp(self):
        """
        Initialize some vars we'll need on every test.
        """
        self.errors = []
        self.modfile = ModFile(0, error_list=self.errors, valid_categories=self.valid_categories)
        self.modfile.full_filename = 'modname.txt'
        self.df = io.StringIO()

    def set_df_contents(self, lines, do_contents=True, newline_after=True):
        """
        Sets the contents of the "file" that we're gonna read in.
        """
        for line in lines:
            print(line, file=self.df)
        if do_contents:
            if newline_after:
                print('', file=self.df)
            print('SparkServiceWhatever', file=self.df)
        self.df.seek(0)

    def test_load_empty(self):
        self.set_df_contents([], do_contents=False)
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No mod title', str(cm.exception))

    def test_load_only_comments(self):
        self.set_df_contents([
            '# Testing',
            ], do_contents=False)
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No mod title', str(cm.exception))

    def test_load_commentless(self):
        self.set_df_contents([])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No mod title', str(cm.exception))

    def test_load_only_name(self):
        self.set_df_contents([
            '# Name: Mod Name',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No categories', str(cm.exception))

    def test_load_only_categories(self):
        self.set_df_contents([
            '# Categories: qol',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No mod title', str(cm.exception))

    def test_load_minimum_headers(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_colon_in_name(self):
        self.set_df_contents([
            '# Name: Mod Name: The Reckoning',
            '# Categories: qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name: The Reckoning')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_unknown_key(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# Bzort: Hi',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('Unknown key', self.errors[0])

    def test_load_full_headers(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Version: 1.0.0',
            '# Categories: qol',
            '# Author: Apocalyptech',
            '# License: Public Domain',
            '# License URL: https://creativecommons.org/share-your-work/public-domain/',
            '# Screenshot: https://i.imgur.com/ClUttYw.gif',
            '# Screenshot: https://i.imgur.com/W5BHeOB.jpg',
            '# Video: https://www.youtube.com/watch?v=JiEu23G4onM',
            '# Video: https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '# Nexus: https://www.nexusmods.com/borderlands3/mods/128',
            '# URL: https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '# URL: https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set(self.modfile.screenshots), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set(self.modfile.video_urls), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set(self.modfile.urls), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.nexus_link, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_multiple_hashes(self):
        self.set_df_contents([
            '### Name: Mod Name',
            '### Version: 1.0.0',
            '### Categories: qol',
            '### Author: Apocalyptech',
            '### License: Public Domain',
            '### License URL: https://creativecommons.org/share-your-work/public-domain/',
            '### Screenshot: https://i.imgur.com/ClUttYw.gif',
            '### Screenshot: https://i.imgur.com/W5BHeOB.jpg',
            '### Video: https://www.youtube.com/watch?v=JiEu23G4onM',
            '### Video: https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '### Nexus: https://www.nexusmods.com/borderlands3/mods/128',
            '### URL: https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '### URL: https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set(self.modfile.screenshots), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set(self.modfile.video_urls), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set(self.modfile.urls), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.nexus_link, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_lowercase(self):
        self.set_df_contents([
            '# name: Mod Name',
            '# version: 1.0.0',
            '# categories: qol',
            '# author: Apocalyptech',
            '# license: Public Domain',
            '# license url: https://creativecommons.org/share-your-work/public-domain/',
            '# screenshot: https://i.imgur.com/ClUttYw.gif',
            '# screenshot: https://i.imgur.com/W5BHeOB.jpg',
            '# video: https://www.youtube.com/watch?v=JiEu23G4onM',
            '# video: https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '# nexus: https://www.nexusmods.com/borderlands3/mods/128',
            '# url: https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '# url: https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set(self.modfile.screenshots), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set(self.modfile.video_urls), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set(self.modfile.urls), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.nexus_link, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_extra_spaces(self):
        self.set_df_contents([
            '# Name    :    Mod Name',
            '# Version    :    1.0.0',
            '# Categories    :    qol',
            '# Author    :    Apocalyptech',
            '# License    :    Public Domain',
            '# License URL    :    https://creativecommons.org/share-your-work/public-domain/',
            '# Screenshot    :    https://i.imgur.com/ClUttYw.gif',
            '# Screenshot    :    https://i.imgur.com/W5BHeOB.jpg',
            '# Video    :    https://www.youtube.com/watch?v=JiEu23G4onM',
            '# Video    :    https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '# Nexus    :    https://www.nexusmods.com/borderlands3/mods/128',
            '# URL    :    https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '# URL    :    https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set(self.modfile.screenshots), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set(self.modfile.video_urls), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set(self.modfile.urls), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.nexus_link, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertFalse(self.modfile.has_errors())

    def test_load_multiple_names(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Name: Mod Name 2',
            '# Categories: qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one mod name', self.errors[0])

    def test_load_multiple_versions(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# Version: 1.0.0',
            '# Version: 2.0.0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one version', self.errors[0])

    def test_load_multiple_licenses(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# License: Public Domain',
            '# License: CC BY-SA 4.0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one license', self.errors[0])

    def test_load_multiple_license_urls(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# License URL: https://creativecommons.org/publicdomain/',
            '# License URL: https://creativecommons.org/licenses/by-sa/4.0/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/publicdomain/')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one license URL', self.errors[0])

    def test_load_multiple_nexus_urls(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# Nexus: https://www.nexusmods.com/borderlands3/mods/128',
            '# Nexus: https://www.nexusmods.com/borderlands2/mods/50',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.nexus_link, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one nexus URL', self.errors[0])

    def test_duplicate_categories(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol, qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol, scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories_no_spaces(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol,scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories_extra_spaces(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol   ,     scaling  , char-gunner',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol', 'char-gunner']))
        self.assertFalse(self.modfile.has_errors())

    def test_invalid_category(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: bzort',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No categories', str(cm.exception))

    def test_one_good_and_one_bad_category(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol, bzort',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('Invalid category', self.errors[0])

    def test_set_no_comments(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_set_one_comment(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# This is a mod',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

    def test_set_two_comments(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '# This is a mod',
            '# It is dope',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod', 'It is dope'])

