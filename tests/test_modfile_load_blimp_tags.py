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

class ModFileTextBlimpTagsTests(unittest.TestCase):
    """
    Testing importing a text-hotfixes-format file with BLIMP
    tags, rather than our original ad-hoc format.
    
    https://github.com/apple1417/blcmm-parsing/tree/master/blimp#tag-intepretation
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
        self.modfile.full_filename = 'modname.bl3hotfix'
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

    def test_load_only_name(self):
        self.set_df_contents([
            '@title Mod Name',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No categories', str(cm.exception))

    def test_load_only_categories(self):
        self.set_df_contents([
            '@categories qol',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No mod title', str(cm.exception))

    def test_load_minimum_headers(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_minimum_headers_comment(self):
        self.set_df_contents([
            '# @title Mod Name',
            '# @categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_minimum_headers_comment_multi(self):
        self.set_df_contents([
            '### @title Mod Name',
            '### @categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_invalid_tags_spaces(self):
        self.set_df_contents([
            '@ title Mod Name',
            '@ categories qol',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)

    def test_load_invalid_tags_colons(self):
        self.set_df_contents([
            '@title: Mod Name',
            '@categories: qol',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)

    def test_load_colon_in_name(self):
        self.set_df_contents([
            '@title Mod Name: The Reckoning',
            '@categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name: The Reckoning')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_atsign_in_name(self):
        self.set_df_contents([
            '@title @Mod Name',
            '@categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, '@Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_load_unknown_key(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@bzort Hi',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('Unknown key', self.errors[0])

    def test_load_bare_key(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@bzort',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('Bare tag', self.errors[0])

    def test_load_full_headers(self):
        self.set_df_contents([
            '@title Mod Name',
            '@version 1.0.0',
            '@categories qol',
            '@author Apocalyptech',
            '@license Public Domain',
            '@license-url https://creativecommons.org/share-your-work/public-domain/',
            '@screenshot https://i.imgur.com/ClUttYw.gif',
            '@screenshot https://i.imgur.com/W5BHeOB.jpg',
            '@video https://www.youtube.com/watch?v=JiEu23G4onM',
            '@video https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '@homepage https://mod.com/',
            '@nexus https://www.nexusmods.com/borderlands3/mods/128',
            '@url https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '@url https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            '@pakfile Z_Mod_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set([u.url for u in self.modfile.screenshots]), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.video_urls]), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.urls]), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertEqual(self.modfile.pakfile, 'Z_Mod_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_multiple_hashes(self):
        self.set_df_contents([
            '### @title Mod Name',
            '### @version 1.0.0',
            '### @categories qol',
            '### @author Apocalyptech',
            '### @license Public Domain',
            '### @license-url https://creativecommons.org/share-your-work/public-domain/',
            '### @screenshot https://i.imgur.com/ClUttYw.gif',
            '### @screenshot https://i.imgur.com/W5BHeOB.jpg',
            '### @video https://www.youtube.com/watch?v=JiEu23G4onM',
            '### @video https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '### @homepage https://mod.com/',
            '### @nexus https://www.nexusmods.com/borderlands3/mods/128',
            '### @url https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '### @url https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            '### @pakfile Z_Mod_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set([u.url for u in self.modfile.screenshots]), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.video_urls]), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.urls]), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertEqual(self.modfile.pakfile, 'Z_Mod_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_mixedcase(self):
        self.set_df_contents([
            '# @Title Mod Name',
            '# @Version 1.0.0',
            '# @Categories qol',
            '# @Author Apocalyptech',
            '# @License Public Domain',
            '# @License-URL https://creativecommons.org/share-your-work/public-domain/',
            '# @Screenshot https://i.imgur.com/ClUttYw.gif',
            '# @Screenshot https://i.imgur.com/W5BHeOB.jpg',
            '# @Video https://www.youtube.com/watch?v=JiEu23G4onM',
            '# @Video https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '# @Homepage https://mod.com/',
            '# @Nexus https://www.nexusmods.com/borderlands3/mods/128',
            '# @Url https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '# @Url https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            '# @pakfile Z_Mod_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set([u.url for u in self.modfile.screenshots]), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.video_urls]), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.urls]), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertEqual(self.modfile.pakfile, 'Z_Mod_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_uppercase(self):
        self.set_df_contents([
            '# @TITLE Mod Name',
            '# @VERSION 1.0.0',
            '# @CATEGORIES qol',
            '# @AUTHOR Apocalyptech',
            '# @LICENSE Public Domain',
            '# @LICENSE-URL https://creativecommons.org/share-your-work/public-domain/',
            '# @SCREENSHOT https://i.imgur.com/ClUttYw.gif',
            '# @SCREENSHOT https://i.imgur.com/W5BHeOB.jpg',
            '# @VIDEO https://www.youtube.com/watch?v=JiEu23G4onM',
            '# @VIDEO https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '# @HOMEPAGE https://mod.com/',
            '# @NEXUS https://www.nexusmods.com/borderlands3/mods/128',
            '# @URL https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '# @URL https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            '# @PAKFILE Z_Mod_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set([u.url for u in self.modfile.screenshots]), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.video_urls]), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.urls]), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertEqual(self.modfile.pakfile, 'Z_Mod_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_full_headers_extra_spaces(self):
        self.set_df_contents([
            '@title        Mod Name',
            '@version      1.0.0',
            '@categories   qol',
            '@author       Apocalyptech',
            '@license      Public Domain',
            '@license-url  https://creativecommons.org/share-your-work/public-domain/',
            '@screenshot   https://i.imgur.com/ClUttYw.gif',
            '@screenshot   https://i.imgur.com/W5BHeOB.jpg',
            '@video        https://www.youtube.com/watch?v=JiEu23G4onM',
            '@video        https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            '@homepage     https://mod.com/',
            '@nexus        https://www.nexusmods.com/borderlands3/mods/128',
            '@url          https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            '@url          https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            '@pakfile      Z_Mod_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/share-your-work/public-domain/')
        self.assertEqual(set([u.url for u in self.modfile.screenshots]), set([
            'https://i.imgur.com/ClUttYw.gif',
            'https://i.imgur.com/W5BHeOB.jpg',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.video_urls]), set([
            'https://www.youtube.com/watch?v=JiEu23G4onM',
            'https://www.youtube.com/watch?v=d9Gu1PspA3Y',
            ]))
        self.assertEqual(set([u.url for u in self.modfile.urls]), set([
            'https://borderlands.com/en-US/news/2020-09-10-borderlands-3-patch-hotfixes-sept-10/',
            'https://borderlands.com/en-US/news/2020-09-17-borderlands-3-hotfixes-sept-17/',
            ]))
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertEqual(self.modfile.pakfile, 'Z_Mod_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_multiple_names(self):
        self.set_df_contents([
            '@title Mod Name',
            '@title Mod Name 2',
            '@categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one mod name', self.errors[0])

    def test_load_multiple_versions(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@version 1.0.0',
            '@version 2.0.0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.version, '1.0.0')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one version', self.errors[0])

    def test_load_multiple_licenses(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@license Public Domain',
            '@license CC BY-SA 4.0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.license, 'Public Domain')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one license', self.errors[0])

    def test_load_multiple_license_urls(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@license-url https://creativecommons.org/publicdomain/',
            '@license-url https://creativecommons.org/licenses/by-sa/4.0/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.license_url, 'https://creativecommons.org/publicdomain/')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one license URL', self.errors[0])

    def test_load_multiple_homepages(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@homepage https://mod.com/',
            '@homepage https://mod.biz/',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.homepage.url, 'https://mod.com/')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one homepage', self.errors[0])

    def test_load_multiple_nexus_urls(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@nexus https://www.nexusmods.com/borderlands3/mods/128',
            '@nexus https://www.nexusmods.com/borderlands2/mods/50',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.nexus_link.url, 'https://www.nexusmods.com/borderlands3/mods/128')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one nexus URL', self.errors[0])

    def test_duplicate_categories(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol, qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol, scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories_on_multi_lines(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@categories scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories_no_spaces(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol,scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol']))
        self.assertFalse(self.modfile.has_errors())

    def test_multiple_categories_extra_spaces(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol   ,     scaling  , char-gunner',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['scaling', 'qol', 'char-gunner']))
        self.assertFalse(self.modfile.has_errors())

    def test_invalid_category(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories bzort',
            ])
        with self.assertRaises(NotAModFile) as cm:
            self.modfile.load_text_hotfixes(self.df)
        self.assertIn('No categories', str(cm.exception))

    def test_one_good_and_one_bad_category(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol, bzort',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('Invalid category', self.errors[0])

    def test_load_pakfile_url(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@pakfile https://geocities.com/pakfiles/Z_One_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.pakfile, 'https://geocities.com/pakfiles/Z_One_P.pak')
        self.assertFalse(self.modfile.has_errors())

    def test_load_multiple_pakfiles(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@pakfile Z_One_P.pak',
            '@pakfile Z_Two_P.pak',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.pakfile, 'Z_One_P.pak')
        self.assertTrue(self.modfile.has_errors())
        self.assertIn('More than one pakfile', self.errors[0])

    def test_set_no_comments(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_set_one_comment(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# This is a mod',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

    def test_set_two_comments(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# This is a mod',
            '# It is dope',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod', 'It is dope'])

    def test_blimp_tags_found_first(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# Name: Another Name',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.mod_desc, ['Name: Another Name'])
        self.assertFalse(self.modfile.has_errors())

    def test_old_tags_found_first(self):
        self.set_df_contents([
            '# Name: Mod Name',
            '# Categories: qol',
            '@title Another Name',
            '@categories scaling',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_title, 'Mod Name')
        self.assertEqual(self.modfile.categories, set(['qol']))
        self.assertEqual(self.modfile.mod_desc, ['@title Another Name', '@categories scaling'])
        self.assertFalse(self.modfile.has_errors())

    def test_load_other_authors_same(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@author Apocalyptech',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, [])

    def test_load_other_authors_same_different_case(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@author APOCALYPTECH',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, [])

    def test_load_other_authors_different(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@author CJ',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, ['CJ'])

    def test_load_other_authors_two(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@author CJ',
            '@author Pseudonym',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, ['CJ', 'Pseudonym'])

    def test_load_other_authors_two_but_same_case(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@author cj',
            '@author CJ',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, ['cj'])

    def test_load_other_authors_main(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '@main-author CJ',
            ])
        self.modfile.mod_author = 'Apocalyptech'
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_author, 'Apocalyptech')
        self.assertEqual(self.modfile.other_authors, ['CJ'])

    def test_set_one_comment_with_code(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# This is a mod',
            'SparkPatchEntry,(1,1,0,),/Path/To/Obj.Obj,Attr,0,,0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

    def test_set_one_comment_with_code_empty_line_inbetween(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# This is a mod',
            '',
            'SparkPatchEntry,(1,1,0,),/Path/To/Obj.Obj,Attr,0,,0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

    def test_set_one_comment_but_for_code(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '',
            "# We want to interpret this as if it's a comment for the next statement",
            'SparkPatchEntry,(1,1,0,),/Path/To/Obj.Obj,Attr,0,,0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, [])

    def test_set_one_comment_and_one_for_code(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '# This is a mod',
            '',
            "# We want to interpret this as if it's a comment for the next statement",
            'SparkPatchEntry,(1,1,0,),/Path/To/Obj.Obj,Attr,0,,0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

    def test_set_one_comment_and_one_for_code_spaces_around(self):
        self.set_df_contents([
            '@title Mod Name',
            '@categories qol',
            '',
            '# This is a mod',
            '',
            "# We want to interpret this as if it's a comment for the next statement",
            'SparkPatchEntry,(1,1,0,),/Path/To/Obj.Obj,Attr,0,,0',
            ])
        self.modfile.load_text_hotfixes(self.df)
        self.assertEqual(self.modfile.mod_desc, ['This is a mod'])

