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
import io
import lzma
import json
import shutil
import unittest
import tempfile
from bl3cabinetsorter.app import FileCache, ModFile, Readme, DirInfo, CabinetInfo, CabinetModInfo

class FileCacheTests(unittest.TestCase):
    """
    Test our FileCache class.  We're mostly not testing any ModFile or
    Readme functionality in here, though we do load+save both, just
    to be sure.
    """

    valid_cats = {
            'cat1': 'Category One',
            'cat2': 'Category Two',
            }

    def setUp(self):
        """
        Things we need to do to start up every test in here
        """
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        """
        Cleanup tasks after every test
        """
        shutil.rmtree(self.tmpdir)

    def create_cache(self, filename, cache_dict):
        """
        Creates the cache `filename` inside our tmpdir, with the
        given dictionary.  We've got to duplicate a bit of structure
        to write these out, but that feels better than relying on
        its own functions to save out.
        """
        file_path = os.path.join(self.tmpdir, filename)
        with lzma.open(file_path, 'wt', encoding='utf-8') as df:
            json.dump(cache_dict, df)
        return file_path

    def make_path(self, path):
        """
        Creates the `path` inside our tmpdir, and return the full
        path
        """
        file_path = os.path.join(self.tmpdir, path)
        os.makedirs(file_path, exist_ok=True)
        return file_path

    def make_file(self, path, filename, lines, mtime=None):
        """
        Creates a file inside `path` named `filename`, containing the
        list of strings `lines` as its contents.
        """
        file_path = self.make_path(path)
        full_file = os.path.join(file_path, filename)
        with open(full_file, 'w') as df:
            for line in lines:
                print(line, file=df)
        if mtime is not None:
            stat_result = os.stat(full_file)
            os.utime(full_file, times=(stat_result.st_atime, mtime))
        return full_file

    def test_mod_construct(self):
        filename = self.create_cache('cache', {'version': 1, ModFile.cache_key: {}})
        self.assertIsNotNone(FileCache(ModFile, filename))

    def test_readme_construct(self):
        filename = self.create_cache('cache', {'version': 1, Readme.cache_key: {}})
        self.assertIsNotNone(FileCache(Readme, filename))

    def test_cabinetinfo_construct(self):
        filename = self.create_cache('cache', {'version': 1, CabinetInfo.cache_key: {}})
        self.assertIsNotNone(FileCache(CabinetInfo, filename))

    def test_old_version(self):
        filename = self.create_cache('cache', {'version': 9999, ModFile.cache_key: {}})
        with self.assertRaises(Exception) as cm:
            FileCache(ModFile, filename)
        self.assertIn('up to version', str(cm.exception))

    def test_mod_single(self):
        mod = ModFile(0)
        mod.mod_title = 'Testing Mod'
        filename = self.create_cache('cache', {
            'version': 1,
            ModFile.cache_key: {
                'filename': mod.serialize(),
                }
            })
        cache = FileCache(ModFile, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 1)
        self.assertIn('filename', cache)
        self.assertEqual(cache['filename'].mod_title, 'Testing Mod')

    def test_mod_two(self):
        mod = ModFile(0)
        mod.mod_title = 'Testing Mod'
        mod2 = ModFile(0)
        mod2.mod_title = 'Testing Mod 2'
        filename = self.create_cache('cache', {
            'version': 1,
            ModFile.cache_key: {
                'filename': mod.serialize(),
                'filename2': mod2.serialize(),
                }
            })
        cache = FileCache(ModFile, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 2)
        self.assertIn('filename', cache)
        self.assertIn('filename2', cache)
        self.assertEqual(cache['filename'].mod_title, 'Testing Mod')
        self.assertEqual(cache['filename2'].mod_title, 'Testing Mod 2')

    def test_readme_single(self):
        readme = Readme(0)
        readme.mapping['(default)'].append('Testing Readme')
        filename = self.create_cache('cache', {
            'version': 1,
            Readme.cache_key: {
                'filename': readme.serialize(),
                }
            })
        cache = FileCache(Readme, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 1)
        self.assertIn('filename', cache)
        self.assertEqual(cache['filename'].mapping['(default)'], ['Testing Readme'])

    def test_readme_two(self):
        readme = Readme(0)
        readme.mapping['(default)'].append('Testing Readme')
        readme2 = Readme(0)
        readme2.mapping['(default)'].append('Testing Readme 2')
        filename = self.create_cache('cache', {
            'version': 1,
            Readme.cache_key: {
                'filename': readme.serialize(),
                'filename2': readme2.serialize(),
                }
            })
        cache = FileCache(Readme, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 2)
        self.assertIn('filename', cache)
        self.assertIn('filename2', cache)
        self.assertEqual(cache['filename'].mapping['(default)'], ['Testing Readme'])
        self.assertEqual(cache['filename2'].mapping['(default)'], ['Testing Readme 2'])

    def test_cabinetinfo_single(self):
        info = CabinetInfo(0)
        info.rel_filename = 'cabinet.info'
        info.single_mod = True
        filename = self.create_cache('cache', {
            'version': 1,
            CabinetInfo.cache_key: {
                'filename': info.serialize(),
                }
            })
        cache = FileCache(CabinetInfo, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 1)
        self.assertIn('filename', cache)
        self.assertEqual(cache['filename'].rel_filename, 'cabinet.info')

    def test_cabinetinfo_two(self):
        info = CabinetInfo(0)
        info.rel_filename = 'cabinet.info'
        info.single_mod = True
        info2 = CabinetInfo(0)
        info2.rel_filename = 'cabinet2.info'
        info2.single_mod = True
        filename = self.create_cache('cache', {
            'version': 1,
            CabinetInfo.cache_key: {
                'filename': info.serialize(),
                'filename2': info2.serialize(),
                }
            })
        cache = FileCache(CabinetInfo, filename)
        self.assertIsNotNone(cache)
        self.assertEqual(len(cache), 2)
        self.assertIn('filename', cache)
        self.assertIn('filename2', cache)
        self.assertEqual(cache['filename'].rel_filename, 'cabinet.info')
        self.assertEqual(cache['filename2'].rel_filename, 'cabinet2.info')

    def test_save_mod_empty(self):
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, filename)
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved, {
                'version': FileCache.cache_version,
                ModFile.cache_key: {},
                })

    def test_save_mod_single(self):
        mod = ModFile(0)
        mod.mod_title = 'Testing Mod'
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, filename)
        cache.mapping['filename'] = mod
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[ModFile.cache_key]), 1)
            self.assertIn('filename', saved[ModFile.cache_key])

    def test_save_mod_two(self):
        mod = ModFile(0)
        mod.mod_title = 'Testing Mod'
        mod2 = ModFile(0)
        mod2.mod_title = 'Testing Mod 2'
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, filename)
        cache.mapping['filename'] = mod
        cache.mapping['filename2'] = mod2
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[ModFile.cache_key]), 2)
            self.assertIn('filename', saved[ModFile.cache_key])
            self.assertIn('filename2', saved[ModFile.cache_key])

    def test_save_readme_empty(self):
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, filename)
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved, {
                'version': FileCache.cache_version,
                Readme.cache_key: {},
                })

    def test_save_readme_single(self):
        readme = Readme(0)
        readme.mapping['(default)'].append('Testing Readme')
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, filename)
        cache.mapping['filename'] = readme
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[Readme.cache_key]), 1)
            self.assertIn('filename', saved[Readme.cache_key])

    def test_save_readme_two(self):
        readme = Readme(0)
        readme.mapping['(default)'].append('Testing Readme')
        readme2 = Readme(0)
        readme2.mapping['(default)'].append('Testing Readme 2')
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, filename)
        cache.mapping['filename'] = readme
        cache.mapping['filename2'] = readme2
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[Readme.cache_key]), 2)
            self.assertIn('filename', saved[Readme.cache_key])
            self.assertIn('filename2', saved[Readme.cache_key])

    def test_save_cabinetinfo_empty(self):
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, filename)
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved, {
                'version': FileCache.cache_version,
                CabinetInfo.cache_key: {},
                })

    def test_save_cabinetinfo_single(self):
        info = CabinetInfo(0)
        info.rel_filename = 'cabinet.info'
        info.single_mod = True
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, filename)
        cache.mapping['filename'] = info
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[CabinetInfo.cache_key]), 1)
            self.assertIn('filename', saved[CabinetInfo.cache_key])

    def test_save_cabinetinfo_two(self):
        info = CabinetInfo(0)
        info.rel_filename = 'cabinet.info'
        info.single_mod = True
        info2 = CabinetInfo(0)
        info2.rel_filename = 'cabinet2.info'
        info2.single_mod = True
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, filename)
        cache.mapping['filename'] = info
        cache.mapping['filename2'] = info2
        cache.save()
        self.assertTrue(os.path.exists(filename))
        with lzma.open(filename, 'rt', encoding='utf-8') as df:
            saved = json.load(df)
            self.assertEqual(saved['version'], FileCache.cache_version)
            self.assertEqual(len(saved[CabinetInfo.cache_key]), 2)
            self.assertIn('filename', saved[CabinetInfo.cache_key])
            self.assertIn('filename2', saved[CabinetInfo.cache_key])

    def test_load_mod_not_found(self):
        """
        Not actually sure if this is what we should do here; for now we're
        just letting the eventual file open fail.  Given that while running
        we should only be getting filenames that have come from os.walk(),
        this shouldn't be a big deal anyway, really.
        """
        mod = ModFile(0)
        mod.mod_title = 'Testing Mod'
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, filename)
        cache.mapping['filename'] = mod
        cache.save()
        dirinfo = DirInfo(self.tmpdir, '', ['filename'])
        with self.assertRaises(FileNotFoundError) as cm:
            cache.load(dirinfo, 'filename')

    def test_load_readme_not_found(self):
        """
        Ditto above
        """
        readme = Readme(0)
        readme.mapping['(default)'].append('Testing Readme')
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, filename)
        cache.mapping['filename'] = readme
        cache.save()
        dirinfo = DirInfo(self.tmpdir, '', ['filename'])
        with self.assertRaises(FileNotFoundError) as cm:
            cache.load(dirinfo, 'filename')

    def test_load_cabinetinfo_not_found(self):
        """
        Ditto above.
        """
        info = CabinetInfo(0)
        info.rel_filename = 'cabinet.info'
        info.single_mod = True
        filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, filename)
        cache.mapping['filename'] = info
        cache.save()
        dirinfo = DirInfo(self.tmpdir, '', ['filename'])
        with self.assertRaises(FileNotFoundError) as cm:
            cache.load(dirinfo, 'filename')

    def test_load_mod_new_file(self):
        mod_filename = self.make_file('', 'filename', ['testing'], mtime=42)
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, cache_filename)
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(ModFile, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_mod = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_mod)
        self.assertEqual(loaded_mod.status, ModFile.S_NEW)
        self.assertIn(mod_filename, cache)
        self.assertEqual(loaded_mod.mod_desc, ['testing'])

    def test_load_mod_same_mtimes(self):
        mod_filename = self.make_file('', 'filename', ['testing'], mtime=42)
        mod = ModFile(42)
        mod.mod_title = 'Testing Mod'
        mod.mod_desc = ['no overwrite']
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, cache_filename)
        cache.mapping[mod_filename] = mod
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(ModFile, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_mod = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_mod)
        self.assertEqual(loaded_mod.status, ModFile.S_CACHED)
        self.assertIn(mod_filename, cache)
        self.assertEqual(loaded_mod.mod_desc, ['no overwrite'])

    def test_load_mod_newer(self):
        mod_filename = self.make_file('', 'filename', ['testing'], mtime=84)
        mod = ModFile(42)
        mod.mod_title = 'Testing Mod'
        mod.mod_desc = ['overwrite']
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(ModFile, cache_filename)
        cache.mapping[mod_filename] = mod
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(ModFile, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_mod = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_mod)
        self.assertEqual(loaded_mod.status, ModFile.S_UPDATED)
        self.assertIn(mod_filename, cache)
        self.assertEqual(loaded_mod.mod_desc, ['testing'])

    def test_load_readme_new_file(self):
        readme_filename = self.make_file('', 'filename', ['testing'], mtime=42)
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, cache_filename)
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(Readme, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_readme = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_readme)
        self.assertEqual(loaded_readme.status, ModFile.S_NEW)
        self.assertIn(readme_filename, cache)
        self.assertEqual(loaded_readme.mapping['(default)'], ['testing'])

    def test_load_readme_same_mtimes(self):
        readme_filename = self.make_file('', 'filename', ['testing'], mtime=42)
        readme = Readme(42)
        readme.mapping['(default)'].append('no overwrite')
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, cache_filename)
        cache.mapping[readme_filename] = readme
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(Readme, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_readme = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_readme)
        self.assertEqual(loaded_readme.status, ModFile.S_CACHED)
        self.assertIn(readme_filename, cache)
        self.assertEqual(loaded_readme.mapping['(default)'], ['no overwrite'])

    def test_load_readme_newer(self):
        readme_filename = self.make_file('', 'filename', ['testing'], mtime=84)
        readme = Readme(42)
        readme.mapping['(default)'].append('overwrite')
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(Readme, cache_filename)
        cache.mapping[readme_filename] = readme
        cache.save()
        
        # Reload from disk, just in case anything's weird
        cache = FileCache(Readme, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        loaded_readme = cache.load(dirinfo, 'filename')
        self.assertIsNotNone(loaded_readme)
        self.assertEqual(loaded_readme.status, ModFile.S_UPDATED)
        self.assertIn(readme_filename, cache)
        self.assertEqual(loaded_readme.mapping['(default)'], ['testing'])

    def test_load_cabinetinfo_new_file(self):
        info_filename = self.make_file('', 'filename', ['cat1'], mtime=42)
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, cache_filename)
        cache.save()

        # Reload from disk, just in case anything's weird
        cache = FileCache(CabinetInfo, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        errors = []
        loaded_info = cache.load(dirinfo, 'filename',
                rel_filename='filename', error_list=errors, valid_categories=self.valid_cats)
        self.assertIsNotNone(loaded_info)
        self.assertEqual(loaded_info.status, CabinetInfo.S_NEW)
        self.assertIn(info_filename, cache)
        self.assertTrue(loaded_info.single_mod)
        self.assertIn(None, loaded_info.mods)
        self.assertEqual(loaded_info[None].categories, ['cat1'])

    def test_load_cabinetinfo_same_mtimes(self):
        info_filename = self.make_file('', 'filename', ['cat1'], mtime=42)
        info = CabinetInfo(42)
        info.single_mod = True
        info.rel_filename = 'filename'
        info.mods[None] = CabinetModInfo('modname', ['cat1'])
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, cache_filename)
        cache.mapping[info_filename] = info
        cache.save()

        # Reload from disk, just in case anything's weird
        cache = FileCache(CabinetInfo, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        errors = []
        loaded_info = cache.load(dirinfo, 'filename',
                rel_filename='filename', error_list=errors, valid_categories=self.valid_cats)
        self.assertIsNotNone(loaded_info)
        self.assertEqual(loaded_info.status, CabinetInfo.S_CACHED)
        self.assertIn(info_filename, cache)
        self.assertTrue(loaded_info.single_mod)
        self.assertIn(None, loaded_info.mods)
        self.assertEqual(loaded_info[None].categories, ['cat1'])

    def test_load_cabinetinfo_newer(self):
        info_filename = self.make_file('', 'filename', ['cat1'], mtime=84)
        info = CabinetInfo(42)
        info.single_mod = True
        info.rel_filename = 'filename'
        info.mods[None] = CabinetModInfo('modname', ['cat1'])
        cache_filename = os.path.join(self.tmpdir, 'cache')
        cache = FileCache(CabinetInfo, cache_filename)
        cache.mapping[info_filename] = info
        cache.save()

        # Reload from disk, just in case anything's weird
        cache = FileCache(CabinetInfo, cache_filename)
        dirinfo = DirInfo('/tmp/doesnotexist', self.tmpdir, ['filename'])
        errors = []
        loaded_info = cache.load(dirinfo, 'filename',
                rel_filename='filename', error_list=errors, valid_categories=self.valid_cats)
        self.assertIsNotNone(loaded_info)
        self.assertEqual(loaded_info.status, CabinetInfo.S_UPDATED)
        self.assertIn(info_filename, cache)
        self.assertTrue(loaded_info.single_mod)
        self.assertIn(None, loaded_info.mods)
        self.assertEqual(loaded_info[None].categories, ['cat1'])
