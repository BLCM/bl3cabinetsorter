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

import os
import re
import sys
import git
import json
import lzma
import html
import jinja2
import logging
import datetime
import traceback
import collections
import Levenshtein
import configparser
import urllib.parse

class Re(object):
    """
    Class to allow us to use a Perl-like regex-comparison idiom
    such as:

    if $line =~ /(foo)/ { ... }
    elsif $line =~ /(bar)/ { ... }
    elsif $line =~ /(baz)/ { ... }

    Taken from http://stackoverflow.com/questions/597476/how-to-concisely-cascade-through-multiple-regex-statements-in-python
    """

    def __init__(self):
        self.last_match = None

    def match(self, regex, text):
        self.last_match = regex.match(text)
        return self.last_match

    def search(self, regex, text):
        self.last_match = regex.search(text)
        return self.last_match

class DirInfo(object):
    """
    Class to hold some info about all the files in the current dir,
    and provide some useful methods to get at it.
    """

    def __init__(self, repo_dir, dirpath, filenames):
        """
        Initialize given our current dir path, and a list of filenames
        """
        self.repo_dir = repo_dir
        self.dirpath = dirpath
        self.rel_dirpath = dirpath[len(self.repo_dir)+1:]
        path_components = self.rel_dirpath.split(os.sep)
        if path_components:
            self.dir_author = path_components[0]
        self.cur_path = path_components[-1]
        self.lower_mapping = {}
        self.extension_map = {}
        self.no_extension = []
        self.readme = None
        for n in filenames:
            lower = n.lower()
            if '.' in lower:
                ext = lower.split('.')[-1]
                if ext not in self.extension_map:
                    self.extension_map[ext] = [lower]
                else:
                    self.extension_map[ext].append(lower)
            else:
                self.no_extension.append(lower)
            self.lower_mapping[lower] = os.path.join(dirpath, n)

            # We're assuming there'll only be one README in any given
            # dir, which is probably safe enough, and I don't think I
            # care enough to try and prioritize, in dirs where there
            # might be more than one
            if 'readme' in lower:
                self.readme = lower

    def __getitem__(self, key):
        """
        Pretend to be a dict
        """
        return self.lower_mapping[key.lower()]

    def __contains__(self, key):
        """
        Return whether or not we contain the given filename
        """
        return key.lower() in self.lower_mapping

    def get_all(self):
        """
        Returns all files
        """
        return self.lower_mapping.keys()

    def get_all_with_ext(self, extension):
        """
        Returns all files with the given extension
        """
        if extension in self.extension_map:
            return self.extension_map[extension]
        else:
            return []

    def get_all_no_ext(self):
        """
        Returns all entries without extensions
        """
        return self.no_extension

    def get_rel_path(self, filename):
        """
        Returns a tuple with the relative path to the directory containing
        the given file, and the relative path to the file itself
        """
        return (
            self.rel_dirpath,
            self[filename][len(self.repo_dir)+1:],
            )

class Cacheable(object):
    """
    A class which is intended to be used with our FileCache.  In order to
    be used properly by FileCache, an implementing class needs to do the
    following:

    1) Define cache_key
    2) Support the proper constructor (see the `__init__` docs)
    3) Implement `_serialize` and `_unserialize`

    Cacheable objects which do not have a file backend can omit the constructor,
    though you'll have to cope with having a "pretend" mtime with each object.
    """

    cache_key = None

    (S_UNKNOWN,
            S_CACHED,
            S_NEW,
            S_UPDATED) = range(4)

    S_ENG = {
            S_UNKNOWN: 'Unknown',
            S_CACHED: 'Cached',
            S_NEW: 'New',
            S_UPDATED: 'Updated',
            }

    def __init__(self, mtime, initial_status=S_UNKNOWN):
        """
        Note that implementing classes, in order to be used with FileCache,
        need to support a constructor with the following arguments:
            - mtime
            - dirinfo
            - filename
            - initial_status
        Don't forget to call super().__init__(mtime, initial_status) in your
        own constructor.
        """
        self.mtime = mtime
        self.status = initial_status

    def has_errors(self):
        """
        Reimplement this in the inheriting class if you want to be able to
        pretend that the file's mtime is in the past, in the event of
        errors.
        """
        return False

    def serialize(self):
        """
        Returns a serializable dict describing ourselves
        """
        d = self._serialize()
        if self.has_errors():
            d['m'] = 0
        else:
            d['m'] = self.mtime
        return d

    def _serialize(self): # pragma: nocover
        """
        Returns a serializable dict describing ourselves
        """
        raise Exception('Not implemented')

    @staticmethod
    def unserialize(cache_class, input_dict):
        """
        Creates a new ModFile given the specified serialized dict
        """
        obj = cache_class(input_dict['m'], initial_status=Cacheable.S_CACHED)
        obj._unserialize(input_dict)
        return obj

    def _unserialize(self, input_dict): # pragma: nocover
        """
        Populates ourself given the specified serialized dict
        """
        raise Exception('Not implemented')

class TemplateMTime(Cacheable):
    """
    Info about a template's mtime, so we can regen if need be.  This is
    basically the bare minimum-implementable Cacheable - literally all
    we care about is the mtime.
    """

    cache_key = 'template'

    def __init__(self, mtime, dirinfo=None, filename=None, initial_status=Cacheable.S_UNKNOWN):
        super().__init__(mtime, initial_status)

    def _serialize(self):
        return {}

    def _unserialize(self, input_dict):
        pass

class Author(Cacheable):
    """
    Info about a mod author.
    """

    cache_key = 'author'

    regular_modlink_re = re.compile('^\[\[(.*?)\|.*\]\].*$')
    html_modlink_re = re.compile('^<a href=.*?>(.*)</a>.*$')

    def __init__(self, mtime, initial_status=Cacheable.S_UNKNOWN, name=None):
        super().__init__(mtime, initial_status)
        self.name = name
        self.mods = set()
        self.cur_mods = set()

    def _serialize(self):
        return {
                'n': self.name,
                'g': list(self.mods),
                }

    def _unserialize(self, input_dict):
        self.name = input_dict['n']
        self.mods = set(input_dict['g'])

    def add_mod(self, mod):
        self.cur_mods.add(mod.wiki_link())

    def check_modlist(self):
        if self.cur_mods != self.mods:
            self.mods = self.cur_mods
            self.status = self.S_UPDATED
        return self.status

    def wiki_filename(self):
        global wiki_filename
        return wiki_filename(self.name)

    def wiki_link_html(self):
        global wiki_link_html
        return wiki_link_html(self.name, self.name)

    def wiki_link(self):
        global wiki_link
        return wiki_link(self.name, self.name)

    def rel_url(self, game):
        return urllib.parse.quote('{}/{}'.format(game.dir_name, self.name))

    def sort_modlist(self, modlist):
        """
        Convenience function to work around both some annoying github wiki markdown
        link behavior, and my own pig-headedness.  We're rendering links to mod
        pages with ampersands in the names as HTML but leaving all other links as
        "pure" wiki links.  That means that those links no longer sort properly.
        So...
        """
        return sorted(modlist, key=self._sort_modlist_key)

    def _sort_modlist_key(self, modlist_link):
        """
        Key to use when sorting between two different wiki link syntaxes
        """
        ml_lower = modlist_link.lower()
        match = Author.regular_modlink_re.match(ml_lower)
        if match:
            return match.group(1)
        match = Author.html_modlink_re.match(ml_lower)
        if match:
            return match.group(1)
        return ml_lower

class ModURL(object):
    """
    Real simple object to support 'annotated' URLs in cabinet.info files, so
    users can attach text labels to their links, if they want.  Annotated
    URLs are formatted like:

        Text Label|http://url.com/

    ie: a single pipe to separate the text label on the left from the URL
    to the right.
    """

    def __init__(self, link_text):
        if '|' in link_text:
            (self.text, self.url) = link_text.split('|', 1)
        else:
            self.url = link_text
            self.text = None

    def wiki_link(self):
        global wiki_link
        if self.text:
            return wiki_link(self.text, self.url, external=True)
        else:
            return self.url

    def screenshot_embed(self, label='screenshot'):
        if self.text:
            label = self.text
        return '[![{}]({})]({})'.format(
                label, self.url, self.url,
                )

    def __str__(self):
        if self.text:
            return '{}|{}'.format(self.text, self.url)
        else:
            return self.url

    def __eq__(self, other):
        if not other:
            return False
        if self.url and not other.url:
            return False
        if other.url and not self.url:
            return False
        return self.url == other.url and self.text == other.text

class NotAModFile(Exception):
    """
    Custom exception to throw when we try to parse a modfile which turns out to not
    actually be a properly-formatted mod file.
    """

class ModFile(Cacheable):
    """
    Class to pull info out of a mod file.
    """

    cache_key = 'mods'

    def __init__(self, mtime, dirinfo=None, filename=None, initial_status=Cacheable.S_UNKNOWN,
            error_list=None, valid_categories=None):
        super().__init__(mtime, initial_status)
        self.error_list = error_list
        self.valid_categories = valid_categories
        self.mod_time = datetime.datetime.fromtimestamp(mtime)
        self.mod_title = None
        self.mod_title_display = None
        self.version = None
        self.license = None
        self.license_url = None
        self.wiki_filename_base = None
        self.mod_desc = []
        self.readme_rel = None
        self.readme_desc = []
        self.nexus_link = None
        self.screenshots = []
        self.video_urls = []
        self.urls = []
        self.categories = set()
        self.changelog = []
        self.related_links = []
        self.re = Re()
        self.errors = False

        if dirinfo:
            # This is when we're actually loading from a file
            self.seen = True
            self.full_filename = dirinfo[filename]
            (self.rel_path, temp_rel_filename) = dirinfo.get_rel_path(filename)
            self.rel_filename = temp_rel_filename.split(os.path.sep)[-1]
            self.mod_author = dirinfo.dir_author

            # We're going to do a preload here as utf-8 (the default),
            # to see if we can read it as utf-8.  There are a number of
            # base Borderlands objects which are latin1, so we can't
            # use utf-8 for those, but other mod files use unicode chars
            # in their category names, and I'd like to be able to read
            # those properly.
            try:
                with open(self.full_filename, encoding='utf-8') as df:
                    df.read()
                encoding = 'utf-8'
            except UnicodeDecodeError:
                encoding = 'latin1'

            with open(self.full_filename, encoding=encoding) as df:
                first_line = df.readline()
                while first_line.strip() == '':
                    first_line = df.readline()
                    if first_line == '':
                        raise NotAModFile('Empty file found')
                self.load_text_hotfixes(df)
        else:
            # This is used when deserializing
            self.seen = False
            self.full_filename = None
            self.rel_path = None
            self.rel_filename = None
            self.mod_author = None

        # Clean up any empty lines at the end of our comments
        if len(self.mod_desc) > 0:
            while self.mod_desc[-1] == '':
                self.mod_desc.pop()

    def has_errors(self):
        """
        Return whether or not we have errors
        """
        return self.errors

    def _serialize(self):
        """
        Returns a serializable dict describing ourselves
        """
        if self.nexus_link:
            nl = str(self.nexus_link)
        else:
            nl = None
        return {
                'ff': self.full_filename,
                'rp': self.rel_path,
                'rf': self.rel_filename,
                'w': self.wiki_filename_base,
                'a': self.mod_author,
                't': self.mod_title,
                'i': self.mod_title_display,
                'v': self.version,
                'li': self.license,
                'lu': self.license_url,
                'd': self.mod_desc,
                'r': self.readme_desc,
                'l': self.readme_rel,
                'o': self.changelog,
                'e': sorted(self.related_links),
                'n': nl,
                's': [str(s) for s in self.screenshots],
                'y': [str(y) for y in self.video_urls],
                'u': [str(u) for u in self.urls],
                'c': list(self.categories),
                }

    def _unserialize(self, input_dict):
        """
        Populates ourself given the specified serialized dict
        """
        self.full_filename = input_dict['ff']
        self.rel_path = input_dict['rp']
        self.rel_filename = input_dict['rf']
        self.wiki_filename_base = input_dict['w']
        self.mod_author = input_dict['a']
        self.mod_title = input_dict['t']
        self.mod_title_display = input_dict['i']
        self.version = input_dict['v']
        self.license = input_dict['li']
        self.license_url = input_dict['lu']
        self.mod_desc = input_dict['d']
        self.readme_desc = input_dict['r']
        self.readme_rel = input_dict['l']
        self.changelog = input_dict['o']
        self.related_links = set(input_dict['e'])
        if input_dict['n']:
            self.nexus_link = ModURL(input_dict['n'])
        else:
            self.nexus_link = None
        self.screenshots = [ModURL(u) for u in input_dict['s']]
        self.video_urls = [ModURL(u) for u in input_dict['y']]
        self.urls = [ModURL(u) for u in input_dict['u']]
        self.categories = set(input_dict['c'])

    def get_full_rel_filename(self):
        """
        Returns our "full" relative filename
        """
        return os.path.join(self.rel_path, self.rel_filename)

    def set_title_display(self, mod_title_display):
        """
        Sets our display title (for links), updating our status if need be
        """
        self.seen = True
        if mod_title_display != self.mod_title_display:
            if self.status != Cacheable.S_NEW:
                self.status = Cacheable.S_UPDATED
            self.mod_title_display = mod_title_display

    def set_wiki_filename_base(self, wiki_filename_base):
        """
        Sets our wiki filename base, updating our status if need be
        """
        self.seen = True
        if wiki_filename_base != self.wiki_filename_base:
            if self.status != Cacheable.S_NEW:
                self.status = Cacheable.S_UPDATED
            self.wiki_filename_base = wiki_filename_base

    def set_related_links(self, related_mods):
        """
        Sets our new related links given a set of other mods
        """
        new_links = sorted(
            ['{}, by {}'.format(m.wiki_link(), m.mod_author) for m in related_mods]
            )
        if new_links != self.related_links:
            if self.status != Cacheable.S_NEW:
                self.status = Cacheable.S_UPDATED
            self.related_links = new_links

    def update_readme_desc(self, readme, new_desc):
        """
        Updates our README description with the given array
        """
        if readme:
            new_readme_rel = readme.rel_filename
        else:
            new_readme_rel = None
        self.seen = True
        if (self.status != Cacheable.S_NEW and
                (new_desc != self.readme_desc
                    or new_readme_rel != self.readme_rel)):
            self.status = Cacheable.S_UPDATED
        self.readme_desc = new_desc
        self.readme_rel = new_readme_rel

    def update_changelog(self, new_changelog):
        """
        Updates our changelog data with the given array
        """
        self.seen = True
        if self.status != Cacheable.S_NEW and new_changelog != self.changelog:
            self.status = Cacheable.S_UPDATED
        self.changelog = new_changelog

    def load_text_hotfixes(self, df):
        """
        This is currently the only known form of mod file - it's a text-based format
        which uses # for comments at the top, where we're expecting a series of key-value
        based pairs, probably followed by some more freeform explanations, and then
        finally a series of nearly-raw hotfix statements, all starting the line with
        the characters `Spark`.

        Everything up to our first instance of `Spark` will be processed for those
        keywords, and also text descriptions.

        Required keys up at the top:
         - Name
         - Categories
        Other keys which can be specified:
         - Author (actually ignored, in favor of the directory name)
         - Version
         - License
         - License URL
         - Screenshot (can be specified multiple times)
         - Video (can be specified multiple times)
         - Nexus (URL to mod at nexus)
         - URL (other URL)

        We do some processing here to try and separate out any freeform "global"
        mod description text in the header, and a comment that might precede a
        hotfix statement.  This'll fail in various cases (like if someone's using
        some stronger "header" statements) but I feel it's better than nothing.
        That's why we do all the cur_section nonsense in here.
        """
        df.seek(0)
        cur_section = []
        found_raw_comment = False
        for line in df.readlines():
            # If we get to a `Spark` line, break
            if line.startswith('Spark'):
                break

            stripped = line.strip()
            if stripped == '':
                # Found an empty line
                if found_raw_comment and cur_section:
                    # If we're reading "raw" comments and have been reading in
                    # a comment section, append it to our full description
                    self.add_comment_line('')
                    for line in cur_section:
                        self.add_comment_line(line)
                    cur_section = []
            else:
                # I guess let's not actually care if comments have hashes or not.
                # My hfinject.py probably complains and refuses to load the mod if
                # a "bare" comment is specified, but other processors might not, and
                # in the end, who cares?
                if stripped.startswith('#'):
                    stripped = stripped.lstrip('#')
                    # Only strip a single space char after hashes, in case the in-mod
                    # description is using some indents
                    if stripped[0] == ' ':
                        stripped = stripped[1:]

                if found_raw_comment:
                    cur_section.append(stripped)
                else:
                    if ': ' in stripped:
                        key, val = stripped.split(': ')
                        key = key.strip().lower()
                        val = val.strip()
                        if key == 'name':
                            if not self.mod_title:
                                self.mod_title = val
                            else:
                                self.errors = True
                                self.error_list.append('WARNING: More than one mod name specified in `{}`'.format(
                                    self.rel_filename,
                                    ))
                        elif key == 'author':
                            # Ignoring this; we actually take it from the directory
                            pass
                        elif key == 'version':
                            if not self.version:
                                self.version = val
                            else:
                                self.errors = True
                                self.error_list.append('WARNING: More than one version specified in `{}`'.format(
                                    self.rel_filename,
                                    ))
                        elif key == 'categories':
                            for cat in [c.strip().lower() for c in val.split(',')]:
                                if cat in self.valid_categories:
                                    self.categories.add(cat)
                                else:
                                    self.errors = True
                                    self.error_list.append('WARNING: Invalid category "{}" in `{}`'.format(
                                        cat,
                                        self.rel_filename,
                                        ))
                        elif key == 'license':
                            # TODO: Honestly, we should probably allow multiple licenses...
                            if not self.license:
                                self.license = val
                            else:
                                self.errors = True
                                self.error_list.append('WARNING: More than one license specified in `{}`'.format(
                                    self.rel_filename,
                                    ))
                        elif key == 'license url':
                            if not self.license_url:
                                self.license_url = val
                            else:
                                self.errors = True
                                self.error_list.append('WARNING: More than one license URL specified in `{}`'.format(
                                    self.rel_filename,
                                    ))
                        elif key == 'screenshot':
                            self.screenshots.append(val)
                        elif key == 'video':
                            self.video_urls.append(val)
                        elif key == 'nexus':
                            if not self.nexus_link:
                                self.nexus_link = val
                            else:
                                self.errors = True
                                self.error_list.append('WARNING: More than one nexus URL specified in `{}`'.format(
                                    self.rel_filename,
                                    ))
                        elif key == 'url':
                            self.urls.append(val)
                        else:
                            self.errors = True
                            self.error_list.append('WARNING: Unknown key in "{} in `{}`'.format(
                                key,
                                self.rel_filename,
                                ))
                    elif stripped != '':
                        # Okay, we got something that wasn't a `Key: Value` type thing, so
                        # let's just assume we're processing comments now.
                        cur_section.append(stripped)
                        found_raw_comment = True

        if not self.mod_title:
            raise NotAModFile('No mod title found')
        if not self.categories:
            raise NotAModFile('No categories found')

    def add_comment_line(self, line):
        """
        Adds a comment line to our description, attempting to strip out some common
        comment prefixes and do some general data massaging.
        """

        # Take off any whitespace and comment characters
        # (this should already be done)
        #line = comment_line.strip("/#\n\r\t ")
        
        # Prevent adding an empty line at the beginning
        if line == '' and len(self.mod_desc) == 0:
            return

        # Prevent adding more than one empty line in a row
        if len(self.mod_desc) > 0 and self.mod_desc[-1] == '' and line == '':
            return

        # Attempt to prevent adding in header ASCII art
        # (I don't actually expect much of this, but we'll see)
        #if len(self.mod_desc) == 0 and line.strip("[]_/\\.:|#~ \t") == '':
        #    return

        # Finally, add it in.
        self.mod_desc.append(line)

    def __lt__(self, other):
        """
        Sort by mod title
        """
        return self.mod_title.lower() < other.mod_title.lower()

    def wiki_filename(self):
        global wiki_filename
        return wiki_filename(self.wiki_filename_base)

    def wiki_link_html(self):
        global wiki_link_html
        return wiki_link_html(self.mod_title_display, self.wiki_filename_base)

    def wiki_link(self):
        global wiki_link
        return wiki_link(self.mod_title_display, self.wiki_filename_base)

    def rel_url(self):
        """
        Returns a relative URL which we can add to our base_url to
        construct a full link to the mod.
        """
        return urllib.parse.quote('/'.join([self.rel_path, self.rel_filename]))

    def rel_url_dir(self):
        """
        Returns a relative URL which we can add to our base_url to
        construct a full link to the directory which contains the mod.
        """
        return urllib.parse.quote(self.rel_path)

    def rel_readme_url(self):
        """
        Returns a relative URL pointing to our README file
        """
        return urllib.parse.quote(self.readme_rel)

    def is_readme_markdown(self):
        """
        Returns `True` if our README is markdown (or at least has a
        `.md` extension)
        """
        if self.readme_rel:
            return self.readme_rel.lower().endswith('.md')
        return False

    def get_readme_embed(self):
        """
        Returns an appropriately-formatted README for inclusion on
        the page.  (If markdown, return it largely as-is, but if
        plaintext, indent so that it's <pre>-formatted.)
        """
        if self.is_readme_markdown():
            return "\n".join(self.readme_desc)
        else:
            return "\n".join(['    {}'.format(r) for r in self.readme_desc])

    def get_mod_desc_embed(self):
        """
        Returns an appropriately-formatted in-mod description for inclusion
        on the page.
        """
        return "\n".join(['    {}'.format(d) for d in self.mod_desc])

    def get_cat_links(self, categories):
        """
        Convenience function for wiki page - generates a set of links
        to category pages which this mod belongs in.
        """
        return ', '.join([
            c.wiki_link_abbrev(self.game) for c in [
                categories[catname] for catname in sorted(self.categories)
                ]
            ])

class Readme(Cacheable):
    """
    Class to hold information about README files.  We're mostly just trying
    to find anything that might be a heading or list entry, so we can
    match on it later.  Trying to make this work more or less equally
    well whether it's markdown or plaintext.
    """

    cache_key = 'readmes'

    def __init__(self, mtime, dirinfo=None, filename=None, initial_status=Cacheable.S_UNKNOWN):
        super().__init__(mtime, initial_status)
        self.mapping = {'(default)': []}
        self.first_section = None
        if filename:
            full_filename = dirinfo[filename]
            self.read_file(full_filename)
            self.filename = full_filename
            (_, self.rel_filename) = dirinfo.get_rel_path(filename)
        else:
            self.filename = None
            self.rel_filename = None

    def find_matching(self, mod_name, single_mod=True):
        """
        Tries to find a matching section in the readme, given the specified
        `mod_name`.  If `single_mod` is True, the README is expected to be
        for a single mod in the dir.  If False, it is assumed to be in a dir
        containing multiple mods
        """
        mod_name_lower = mod_name.lower()
        if single_mod:
            if 'overview' in self.mapping:
                return self.mapping['overview']
            for section in self.mapping.keys():
                if Levenshtein.ratio(mod_name_lower, section) > .8:
                    return self.mapping[section]
            if self.first_section:
                return self.mapping[self.first_section]
            else:
                return self.mapping['(default)']
        else:
            for section in self.mapping.keys():
                if Levenshtein.ratio(mod_name_lower, section) > .8:
                    return self.mapping[section]
            return []


    def serialize(self):
        """
        Returns a serializable dict describing ourselves (since we're
        basically just a glorified dict anyway, this is pretty trivial)
        """
        return {
                'f': self.filename,
                'r': self.rel_filename,
                'm': self.mtime,
                'd': self.mapping,
                's': self.first_section,
                }

    def _unserialize(self, input_dict):
        """
        Populates ourself given the specified serialized dict
        """
        self.filename = input_dict['f']
        self.rel_filename = input_dict['r']
        self.mapping = input_dict['d']
        self.first_section = input_dict['s']

    def read_file(self, filename):
        """
        Attempt to parse the given filename
        """
        if filename.lower().endswith('.md'):
            is_markdown = True
        else:
            is_markdown = False
        with open(filename) as df:
            self.read_file_obj(df, is_markdown)

    def read_file_obj(self, df, is_markdown):
        """
        Read our file from an open filehandle.  At the
        moment `is_markdown` isn't actually used anymore,
        though we may want to do that at some point.  This
        was split off from `read_file` mostly just for ease
        of unit-testing.
        """
        prev_line = None
        cur_section = '(default)'
        for line in df.readlines():
            line = line.strip()
            if line.startswith('#'):
                cur_section = line.lstrip("# \t").lower()
                self.mapping[cur_section] = []
            elif line.startswith('==='):
                # Multiline markdown section highlighting.  Annoying!  A
                # shame I personally use it all the time, eh?
                if prev_line:
                    if len(self.mapping[cur_section]) > 0:
                        self.mapping[cur_section].pop()
                        if self.first_section == cur_section and len(self.mapping[cur_section]) == 0:
                            self.first_section = None
                        cur_section = prev_line.strip().lower()
                        self.mapping[cur_section] = []
                else:
                    if not self.first_section:
                        self.first_section = cur_section
                    self.mapping[cur_section].append(line)
            elif line.startswith('---'):
                # Multiline markdown section highlighting.  Annoying!  A
                # shame I personally use it all the time, eh?
                if prev_line:
                    if len(self.mapping[cur_section]) > 0:
                        self.mapping[cur_section].pop()
                        if self.first_section == cur_section and len(self.mapping[cur_section]) == 0:
                            self.first_section = None
                        cur_section = prev_line.strip().lower()
                        self.mapping[cur_section] = []
                else:
                    if not self.first_section:
                        self.first_section = cur_section
                    self.mapping[cur_section].append(line)
            elif line.startswith('-'):
                cur_section = line.lstrip("- \t").lower()
                self.mapping[cur_section] = []
            else:
                if len(self.mapping[cur_section]) > 0 or line != '':
                    if not self.first_section:
                        self.first_section = cur_section
                    self.mapping[cur_section].append(line)
            prev_line = line

        # Get rid of any trailing empty lines in each section
        for (section, data) in self.mapping.items():
            while len(data) > 0 and data[-1] == '':
                data.pop()

class FileCache(object):
    """
    Base caching class which we'll use for both mod files and READMEs.
    This can be used as a pure-data caching class by avoiding the use
    of the `load()` method.
    """

    cache_version = 1

    def __init__(self, cache_class, filename, do_load=True):
        """
        Initialize a FileCache using the given `cache_class` and `filename`.
        `cache_class` should be a `Cacheable` object, or at least one which
        pretends to be.  If `do_load` is `False`, we will not actually
        attempt to read anything from the cache, instead pretending that
        we have a totally clean slate.
        """
        self.cache_class = cache_class
        self.filename = filename
        self.mapping = {}
        if do_load and os.path.exists(filename):
            with lzma.open(filename, 'rt', encoding='utf-8') as df:
                serialized_dict = json.load(df)
                if serialized_dict['version'] > self.cache_version:
                    raise Exception('{} is a version {} cache.  We only support up to version {}'.format(
                        filename, serialized_dict['version'], self.cache_version,
                        ))
                for (inner_filename, inner_dict) in serialized_dict[self.cache_class.cache_key].items():
                    self.mapping[inner_filename] = self.cache_class.unserialize(self.cache_class, inner_dict)

    def save(self):
        """
        Saves ourself
        """
        save_dict = {'version': self.cache_version, self.cache_class.cache_key: {}}
        for mod_filename, mod in self.mapping.items():
            save_dict[self.cache_class.cache_key][mod_filename] = mod.serialize()
        with lzma.open(self.filename, 'wt', encoding='utf-8') as df:
            json.dump(save_dict, df)

    def load(self, dirinfo, filename, **extra):
        """
        Loads an entry from the given `filename` (using `dirinfo` as its base),
        if its mtime has been changed or was not previously known.  Otherwise
        return our previously-cached version.  Extra dict arguments, if specified,
        will be passed in to the constructor.
        """
        full_filename = dirinfo[filename]
        mtime = os.stat(full_filename).st_mtime
        if full_filename not in self.mapping or mtime != self.mapping[full_filename].mtime:
            if full_filename not in self.mapping:
                initial_status = Cacheable.S_NEW
            else:
                initial_status = Cacheable.S_UPDATED
            try:
                self.mapping[full_filename] = self.cache_class(mtime, dirinfo, filename, initial_status, **extra)
            except NotAModFile:
                # Eh, whatever
                pass
        return self.mapping[full_filename]

    def items(self):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return self.mapping.items()

    def values(self):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return self.mapping.values()

    def keys(self):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return self.mapping.keys()

    def __setitem__(self, key, value):
        """
        Convenience function to be able to use this sort of like a dict
        """
        self.mapping[key] = value

    def __getitem__(self, key):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return self.mapping[key]

    def __contains__(self, key):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return key in self.mapping

    def __delitem__(self, key):
        """
        Convenience function to be able to use this sort of like a dict
        """
        del self.mapping[key]

    def __len__(self):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return len(self.mapping)

def wiki_filename(page_title, with_ext=True):
    """
    Given a page title, generate a valid wiki filename.  Every char except forward
    slashes are theoretically valid, and spaces become dashes.
    """
    if with_ext:
        format_str = '{}.md'
    else:
        format_str = '{}'
    return format_str.format(page_title.replace(' ', '-').replace('/', '-'))

def wiki_link_html(text, link, external=False):
    """
    Construct a wiki link *specifically* as an HTML link, rather than markdown.
    Doing this appears to make page rendering take fewer resources, which has
    become a problem on our larger category pages like Pistols.
    """
    if external:
        href = link
    else:
        href = urllib.parse.quote(link.replace('/', ' '))
    return '<a href="{}">{}</a>'.format(
            #html.escape(link.replace('/', ' ')),
            href,
            html.escape(text),
            )

def wiki_link(text, link, external=False):
    """
    Redirects to wiki_link_html.  "Real" wiki links are just too dangerous on
    Github wiki -- too many and pages become unrenderable.
    """
    return wiki_link_html(text, link, external)

def wiki_link_disabled(text, link, external=False):
    """
    Construct a link to another page on the wiki, given the human-readable `text`
    and the page title `link`.  If `external` is true, will generate an external
    full-URL link, rather than the in-wiki link style
    """
    if external:
        format_str = '[{}]({})'
    else:
        # Putting ampersands in "pure" markdown links just doesn't work, at least
        # when they're part of the wiki page name (see: Aaron0000's `S&S Forever`
        # and `S&S Lite` mods, for instance).  This trick here is a bit cheap, but
        # it's the only way I've found so far to link to these pages without
        # having to hardcode a fullly-qualified URL, which I'd *really* rather
        # not do.
        if ('&' in link
                or '[' in link
                or ']' in link
                or link.endswith('+_')
                or link.endswith('-')
                or '*' in link):
            return wiki_link_html(text, link)
        format_str = '[[{}|{}]]'
        link = link.replace('/', ' ')
    return format_str.format(
            text,
            link,
            )

class Category(object):
    """
    Class to hold a bit of info about categories.  Very little
    information here, really - just a wrapper around some wiki-
    linking functions, really.
    """

    def __init__(self, title):
        self.full_title = title
        if ': ' in title:
            (self.prefix, self.title) = title.split(': ', 1)
        else:
            self.prefix = None
            self.title = title

    def wiki_filename(self):
        global wiki_filename
        return wiki_filename(self.full_title)

    def wiki_link(self, game):
        global wiki_link_html
        return wiki_link_html(self.title, '{} {}'.format(game.abbreviation, self.full_title))

    def wiki_link_abbrev(self, game_abbrev):
        global wiki_link
        return wiki_link(self.title, '{} {}'.format(game_abbrev, self.full_title))

    def __lt__(self, other):
        return self.full_title < other.full_title

class Game(object):
    """
    Class to hold a bit of info about a game.  Basically just a
    glorified dict.
    """

    def __init__(self, abbreviation, title):
        self.abbreviation = abbreviation
        self.title = title

    def wiki_filename(self):
        global wiki_filename
        return wiki_filename(self.title)

    def wiki_link_back(self):
        global wiki_link
        return wiki_link('← Go Back', self.title)

class App(object):
    """
    Main app
    """

    # Valid Categories
    categories = collections.OrderedDict([

        # Major Modpacks
        ('major-pack', Category('Major Overhauls and Mod Packs')),

        # General Gameplay and Balance
        ('mode-balance', Category('General Gameplay and Balance: Game Mode Balance')),
        ('scaling', Category('General Gameplay and Balance: Scaling Changes')),
        ('mayhem', Category('General Gameplay and Balance: Mayhem Mode Changes')),
        ('element', Category('General Gameplay and Balance: Elements and Damage Types')),
        ('quest-changes', Category('General Gameplay and Balance: Quest Changes')),
        ('economy', Category('General Gameplay and Balance: Economy Changes')),
        ('event', Category('General Gameplay and Balance: Timed Event Changes')),
        ('gameplay', Category('General Gameplay and Balance: Other Gameplay Changes')),

        # Characters and Skills
        ('char-overhaul', Category('Characters and Skills: Full Character Overhauls')),
        ('skill-system', Category('Characters and Skills: Skill System Changes')),
        ('char-beastmaster', Category('Characters and Skills: Beastmaster Changes')),
        ('char-gunner', Category('Characters and Skills: Gunner Changes')),
        ('char-operative', Category('Characters and Skills: Operative Changes')),
        ('char-siren', Category('Characters and Skills: Siren Changes')),
        ('char-other', Category('Characters and Skills: Other Character Changes')),

        # Weapons/Gear
        ('gear-general', Category('Weapons/Gear: General')),
		('gear-anointments', Category('Weapons/Gear: Anointments')),
        ('gear-brand', Category('Weapons/Gear: Brand Overhauls')),
        ('gear-pack', Category('Weapons/Gear: Packs')),
        ('gear-ar', Category('Weapons/Gear: Assault Rifles')),
        ('gear-pistol', Category('Weapons/Gear: Pistols')),
        ('gear-heavy', Category('Weapons/Gear: Heavy Weapons')),
        ('gear-shotgun', Category('Weapons/Gear: Shotguns')),
        ('gear-smg', Category('Weapons/Gear: SMGs')),
        ('gear-sniper', Category('Weapons/Gear: Sniper Rifles')),
        ('gear-grenade', Category('Weapons/Gear: Grenade Mods')),
        ('gear-com', Category('Weapons/Gear: COMs')),
        ('gear-shield', Category('Weapons/Gear: Shields')),
        ('gear-artifact', Category('Weapons/Gear: Artifacts')),

        # Farming and Looting
        ('loot-system', Category('Farming and Looting: Loot System Overhauls')),
        ('enemy-drops', Category('Farming and Looting: Enemy Drop Changes')),
        ('chests', Category('Farming and Looting: Chest and Container Changes')),
        ('vendor', Category('Farming and Looting: Vending Machines')),
        ('slots', Category('Farming and Looting: Slot Machines')),
        ('quest-rewards', Category('Farming and Looting: Quest Rewards')),
        ('loot-sources', Category('Farming and Looting: Other Loot Sources')),

        # Enemies
        ('spawns', Category('Enemies: Enemy Spawns')),
        ('enemy', Category('Enemies: Enemy Changes')),

        # Maps and Public Transport
        ('vehicle', Category('Maps and Public Transport: Vehicles')),
        ('fast-travel', Category('Maps and Public Transport: Fast Travel')),
        ('maps', Category('Maps and Public Transport: Map Alterations')),

        # Audio and Visual
        ('av', Category('Audio and Visual: General A/V Settings')),
        ('ui', Category('Audio and Visual: UI Changes')),
        ('av-gear', Category('Audio and Visual: Weapon and Gear Visuals')),
        ('av-char', Category('Audio and Visual: Character Visuals')),
        ('av-enemy', Category('Audio and Visual: Enemy Visuals')),
        ('audio', Category('Audio and Visual: Audio Changes')),
        ('text', Category('Audio and Visual: Text Changes')),

        # Quality of Life
        ('qol', Category('Quality of Life: General QoL')),
        ('qol-ui', Category('Quality of Life: UI QoL Changes')),
        ('inventory', Category('Quality of Life: Inventory/Bank Changes')),

        # Other
        ('bugfix', Category('Other: Bugfixes')),
        ('cheat', Category('Other: Cheat Mods')),
        ('modpack', Category('Other: Mod Packs')),
        ('translation', Category('Other: Translations')),
        ('joke', Category('Other: Joke Mods')),
        ('resource', Category('Other: Resource Mods')),

        ])

    def __init__(self, ini_file):

        # Read config values from the INI file
        self.config = configparser.ConfigParser()
        if isinstance(ini_file, str):
            self.config.read(ini_file)
        else:
            self.config.read_file(ini_file)
        self.base_url = self.config['mods']['base_url']
        self.dl_base_url = self.config['mods']['download_url']
        self.repo_dir = self.config['mods']['repo_dir']
        self.cabinet_dir = self.config['wiki']['cabinet_dir']
        self.cache_dir = self.config['cache']['cache_dir']
        self.cache_filename = os.path.join(self.cache_dir, 'modcache.json.xz')
        self.readme_cache_filename = os.path.join(self.cache_dir, 'readmecache.json.xz')
        self.author_cache_filename = os.path.join(self.cache_dir, 'authorcache.json.xz')
        self.templatemtime_cache_filename = os.path.join(self.cache_dir, 'templatemtime.json.xz')
        self.log_dir = self.config['logging']['log_dir']
        self.log_file = os.path.join(self.log_dir, 'bl3cabinetsorter.log')
        self.default_log_level = self.config['logging']['default_level']

        # Create our logging dir, if it doesn't already exist
        if not os.path.isdir(self.log_dir):
            os.mkdir(self.log_dir)

        # Set up a logging object
        logging.basicConfig(
                format='%(asctime)-15s - %(levelname)s - %(message)s',
                filename=self.log_file,
                )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.default_log_level))
        self.console = logging.StreamHandler()
        self.console.setFormatter(logging.Formatter('%(levelname)-8s | %(message)s'))
        self.console.setLevel(getattr(logging, self.default_log_level))
        self.logger.addHandler(self.console)

        # Grab Jinja templates
        jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
        self.game_template = jinja_env.get_template('game.md')
        self.cat_template = jinja_env.get_template('category.md')
        self.mod_template = jinja_env.get_template('mod.md')
        self.status_template = jinja_env.get_template('status.md')
        self.sidebar_template = jinja_env.get_template('sidebar.md')
        self.author_template = jinja_env.get_template('author.md')
        self.category_template = jinja_env.get_template('categories.md')

    def run(self, load_cache=True, quiet=False, verbose=False, **args):
        """
        Run the app
        """

        retval = 0

        # Set our console loglevel.
        if quiet:
            self.console.setLevel(logging.ERROR)
        elif verbose:
            self.console.setLevel(logging.DEBUG)
            self.logger.setLevel(logging.DEBUG)
        else:
            self.console.setLevel(logging.INFO)

        # Make a note that we're starting
        self.logger.info('------------------------')
        self.logger.info('Starting Cabinet Sorter!')

        # Initialize our caches
        if not load_cache:
            self.logger.info('Skipping cache loading')
        self.mod_cache = FileCache(ModFile, self.cache_filename, do_load=load_cache)
        self.readme_cache = FileCache(Readme, self.readme_cache_filename, do_load=load_cache)
        self.author_cache = FileCache(Author, self.author_cache_filename, do_load=load_cache)
        self.templatemtime_cache = FileCache(TemplateMTime, self.templatemtime_cache_filename, do_load=load_cache)
        self.error_list = []

        # Initialize templatemtime_cache.  We don't have to do this for
        # most of our templates because they get generated every time,
        # but we want it for mods and authors since those otherwise only
        # get generated if other caches have noticed changes.  We're fudging
        # some DirInfo stuff a bit, since that class is built with a BLCM
        # repo in mind.
        temp_info = DirInfo('', 'templates', ['mod.md', 'author.md'])
        self.mod_template_mtime = self.templatemtime_cache.load(temp_info, 'mod.md')
        self.author_template_mtime = self.templatemtime_cache.load(temp_info, 'author.md')

        # Continue
        try:
            self._run(**args)
        except Exception as e:
            self.logger.critical('Unhandled exception: {}'.format(str(e)))
            for tb_line in traceback.format_exception(*sys.exc_info()):
                for nibble in tb_line.split("\n"):
                    if nibble != '':
                        self.logger.critical(nibble.rstrip())
            retval = 1

        # Make a note that we're ending
        self.logger.info('Cabinet Sorter has finished')

        # Exit
        return retval

    def _run(self,
            do_git=True,
            do_git_commit=True,
            do_initial_tasks=False,
            force_run=False,
            ):
        """
        Actual function to do most of the work.
        """

        # If we've been told to do initial tasks, do those first
        if do_initial_tasks:
            self.logger.info('Performing initial setup tasks.  This may take awhile')
            self.do_initial_tasks()
            self.logger.info('Done with initial setup tasks')

        # Keep track of which categories we've seen
        seen_cats = {}

        # Set up a reserved and created pages set
        status_filename = 'Wiki-Status.md'
        sidebar_filename = '_Sidebar.md'
        category_filename = 'Mod-Categories.md'
        reserved_pages = set([status_filename, sidebar_filename, category_filename])
        created_pages = set([status_filename, sidebar_filename, category_filename])

        # Anything in our static_pages dir should be reserved
        self.logger.debug('Reading in static pages')
        static_pages = {}
        for filename in os.listdir('static_pages'):
            full_filename = os.path.join('static_pages', filename)
            reserved_pages.add(filename)
            with open(full_filename) as df:
                static_pages[filename] = df.read()

        # Add all game/category pages to our reserved_pages list
        reserved_pages.add('Borderlands 3 Mods')
        for cat in self.categories.values():
            reserved_pages.add(cat.wiki_filename())

        # Pull down the latest repo
        if do_git:
            self.logger.debug('Pulling mods repo from git')
            modsrepo = git.Repo(self.repo_dir)
            before_hash = modsrepo.head.object.hexsha
            modsrepo.git.pull()
            after_hash = modsrepo.head.object.hexsha
            if before_hash == after_hash:
                if force_run:
                    self.logger.info('No update found for mods repo, continuing anyway')
                else:
                    self.logger.info('No update found for mods repo')
                    return
            else:
                self.logger.debug('Update found, continuing')
        else:
            self.logger.info('Skipping mods repo pull')

        # Loop through our game dirs
        self.logger.debug('Beginning walkthrough of repo directory')
        name_resolution = {}

        game_dir = self.repo_dir
        for (dirpath, dirnames, filenames) in os.walk(game_dir):

            # Make a mapping of files by lower-case, so that we can
            # match case-insensitively
            dirinfo = DirInfo(self.repo_dir, dirpath, filenames)

            # Load in readme info, if we can.
            readme = None
            if dirinfo.readme:
                readme = self.readme_cache.load(dirinfo, dirinfo.readme)

            # Loop through the mods found in the dir and load 'em, if we can
            processed_files = []
            for txt_file in dirinfo.get_all_with_ext('txt'):
                if 'readme' not in txt_file.lower():
                    try:
                        processed_files.append(self.mod_cache.load(dirinfo, txt_file,
                            error_list=self.error_list,
                            valid_categories=self.categories,
                            ))
                    except NotAModFile:
                        # Whatever, if we're processing *.txt we're bound to have this pop up.
                        pass

            # If we only processed a single mod, then it's a single-mod dir
            if len(processed_files) == 1:
                single_mod = True
            else:
                single_mod = False

            # Do Stuff with each file we got
            for processed_file in processed_files:

                # See if we've got a "better" description in a readme
                if readme:
                    readme_info = readme.find_matching(processed_file.mod_title, single_mod)
                    changelog = readme.find_matching('changelog', False)
                else:
                    readme_info = []
                    changelog = []
                processed_file.update_readme_desc(readme, readme_info)
                processed_file.update_changelog(changelog)

                # Make sure that `seen_cats` is up to date
                for cat in processed_file.categories:
                    if cat not in seen_cats:
                        seen_cats[cat] = []
                    seen_cats[cat].append(processed_file)

                # Previously we were adding mods to our author cache here, but we need
                # to wait until we resolve any potential mod name conflicts first, so
                # that's now happening later...

                # Add to our name_resolution object for later processing
                title_lower = processed_file.mod_title.lower()
                if title_lower not in name_resolution:
                    name_resolution[title_lower] = {}
                author_lower = processed_file.mod_author.lower()
                if author_lower not in name_resolution[title_lower]:
                    name_resolution[title_lower][author_lower] = {}
                name_resolution[title_lower][author_lower][processed_file.rel_filename] = processed_file.full_filename

        # Report that we're done
        self.logger.debug('Finished looping through mods directory')
        for e in self.error_list:
            self.logger.warning('Processing error while looping: {}'.format(e))

        # Some console reporting, for interactive testing.
        if False:
            for mod in self.mod_cache.values():
                if mod.status == Cacheable.S_NEW or mod.status == Cacheable.S_UPDATED:
                    print('{} ({})'.format(mod.get_full_rel_filename(), Cacheable.S_ENG[mod.status]))
                    print(mod.mod_title)
                    print(mod.mod_author)
                    print(mod.mod_time)
                    print(mod.mod_desc)
                    print(mod.readme_desc)
                    print('Categories: {}'.format(mod.categories))
                    if mod.nexus_link:
                        print('Nexus Link: {}'.format(mod.nexus_link))
                    if len(mod.screenshots) > 0:
                        print('Screenshots:')
                        for ss in mod.screenshots:
                            print(' * {}'.format(ss))
                    print('--')

            # Report on any errors
            if len(self.error_list) > 0:
                print('Errors encountered during run:')
                for e in self.error_list:
                    print(' * {}'.format(e))
            else:
                print('No errors encountered during run.')

        # Find any deleted mods.
        to_delete = []
        for filename, mod in self.mod_cache.items():
            if not mod.seen:
                to_delete.append(filename)
        for filename in to_delete:
            self.logger.info('Marking for deletion: {}'.format(filename))
            del self.mod_cache[filename]

        # We have one instance of a mod name which happens to also be an author
        # name (vWolvenn's "Tsunami").  This is silly, and causes us to loop through
        # authors twice while processing, but I think I'm fine with that.
        # NOTE: If running without caches, this will be empty on the very first run,
        # and you'll get an error for any mod which shares the name of a mod author.
        # That'll go away on subsequent runs, though.
        author_names = set()
        for author in self.author_cache.values():
            author_names.add(author.name)

        # Resolve any mod names -- needed in case more than one mod has the same name.
        # This happens a *bit* within a game itself, and quite a bit across game
        # boundaries.  Note that this needs to happen *before* any categories or
        # author pages are written out.
        self.logger.debug('Resolving mod name conflicts')
        for (mod_title, mod_authors) in name_resolution.items():
            shared_set = set()
            need_author = (len(mod_authors) > 1)
            for (author_name, mod_files) in mod_authors.items():
                need_filename = (len(mod_files) > 1)
                for (mod_filename, mod_full_filename) in mod_files.items():
                    if mod_full_filename in self.mod_cache:
                        mod_obj = self.mod_cache[mod_full_filename]

                        # Filename suffix
                        if need_filename:
                            filename_suffix = ' (from {})'.format(mod_filename)
                        else:
                            filename_suffix = ''

                        # Construct author suffix.  We don't do this until now because
                        # our name_resolution dict is all lowercase, which may not be
                        # appropriate.
                        if need_author:
                            author_suffix = ' by {}'.format(mod_obj.mod_author)
                        else:
                            author_suffix = ''

                        # Construct wiki filename and display title
                        new_filename = '{}{}{}'.format(
                                mod_obj.mod_title,
                                filename_suffix,
                                author_suffix,
                                )
                        new_title_display = '{}{}'.format(
                                mod_obj.mod_title,
                                filename_suffix,
                                )

                        # This is kind of ridiculous, but it happens once; doublecheck
                        # to see if the filename conflicts with an author filename.
                        if new_filename in author_names:
                            new_filename = '{} by {}'.format(new_filename, author_name)

                        # Now set our information
                        mod_obj.set_wiki_filename_base(new_filename)
                        mod_obj.set_title_display(new_title_display)
                        shared_set.add(mod_obj)

                        # Add this mod to an author obj
                        if mod_obj.mod_author:
                            if mod_obj.mod_author not in self.author_cache:
                                self.author_cache[mod_obj.mod_author] = Author(0,
                                        initial_status=Author.S_NEW,
                                        name=mod_obj.mod_author)
                            self.author_cache[mod_obj.mod_author].add_mod(mod_obj)

            # Now, have each of the mods with a shared name link over to each other.
            for mod_obj in shared_set:
                mod_obj.set_related_links(shared_set - {mod_obj})

        # Pull down the most recent wiki revision (nobody "should" be editing this
        # manually, but I'm sure it'll happen eventually)
        if do_git:
            self.logger.debug('Pulling wiki repo from git')
            wikirepo = git.Repo(self.cabinet_dir)
            wikirepo.git.pull()
        else:
            self.logger.info('Skipping wiki repo pull')

        # Get a list of files currently in the wiki
        self.logger.debug('Getting current list of wiki files')
        wiki_files = set()
        for filename in os.listdir(self.cabinet_dir):
            if os.path.isfile(os.path.join(self.cabinet_dir, filename)):
                wiki_files.add(filename)

        # Write out updated static pages, if need be
        self.logger.debug('Writing out static pages')
        for (filename, content) in static_pages.items():
            created_pages.add(filename)
            self.write_wiki_file(wiki_files,
                    filename,
                    content,
                    )

        # Write out game and category pages
        self.logger.debug('Writing out game and category pages')
        game_cats = []
        for (cat_key, cat) in self.categories.items():
            if cat_key in seen_cats:
                game_cats.append(cat)

                # Write out the category page
                cat_filename = cat.wiki_filename()
                created_pages.add(cat_filename)
                self.write_wiki_file(wiki_files,
                        cat_filename,
                        self.cat_template.render({
                            'cat': cat,
                            'mods': sorted(seen_cats[cat_key]),
                            'authors': self.author_cache,
                            }),
                        )

            # Write out the game page, linking to all categories which have mods
            game_filename = 'Borderlands 3 Mods'
            created_pages.add(game_filename)
            self.write_wiki_file(wiki_files,
                    game_filename,
                    self.game_template.render({
                        'categories': game_cats,
                        })
                    )

        # Write out sidebar
        self.logger.debug('Writing sidebar')
        self.write_wiki_file(wiki_files,
                sidebar_filename,
                self.sidebar_template.render({
                    'cats': self.categories,
                    'seen_cats': game_cats,
                    })
                )

        # Write out 'categories' page
        self.logger.debug('Writing categories page')
        self.write_wiki_file(wiki_files,
                category_filename,
                self.category_template.render({
                    'categories': self.categories,
                    })
                )

        # Write out Author pages
        self.logger.debug('Writing author pages')
        for author in self.author_cache.values():
            author_filename = author.wiki_filename()
            if author_filename in reserved_pages:
                e = 'ERROR: Author `{}` uses a reserved name'.format(author_filename)
                self.logger.warning('Processing error: {}'.format(e))
                self.error_list.append(e)
            elif author_filename in created_pages:
                e = 'ERROR: Author `{}` has the same name as an already-created file'.format(
                        author_filename)
                self.logger.warning('Processing error: {}'.format(e))
                self.error_list.append(e)
            else:
                created_pages.add(author_filename)
                # Make sure that author.check_modlist() gets called regardless of any
                # other check, else author data won't get populated on the very first
                # run.  (Subsequent runs *would* fix it, though...)
                if (author.check_modlist() != Author.S_CACHED
                        or self.author_template_mtime.status != TemplateMTime.S_CACHED
                        or author_filename not in wiki_files):
                    full_author = os.path.join(self.cabinet_dir, author_filename)
                    with open(full_author, 'w') as df:
                        df.write(self.author_template.render({
                            'author': author,
                            'base_url': self.base_url,
                            }))

        # Write out our individual mods
        self.logger.debug('Writing individual mod pages')
        for mod in self.mod_cache.values():
            mod_filename = mod.wiki_filename()
            if mod_filename in reserved_pages:
                e = 'ERROR: `{}` uses a reserved name'.format(mod.get_full_rel_filename())
                self.logger.warning('Processing error: {}'.format(e))
                self.error_list.append(e)
            elif mod_filename in created_pages:
                e = 'ERROR: `{}` has the same name as an already-created file'.format(mod.get_full_rel_filename())
                self.logger.warning('Processing error: {}'.format(e))
                self.error_list.append(e)
            else:
                created_pages.add(mod_filename)
                if (self.mod_template_mtime.status != TemplateMTime.S_CACHED
                        or mod.status != ModFile.S_CACHED
                        or mod_filename not in wiki_files):
                    content = self.mod_template.render({
                        'mod': mod,
                        'base_url': self.base_url,
                        'dl_base_url': self.dl_base_url,
                        'cats': self.categories,
                        'authors': self.author_cache,
                        })
                    full_filename = os.path.join(self.cabinet_dir, mod_filename)
                    with open(full_filename, 'w') as df:
                        df.write(content)

        # Finally, our 'Status' page.  This always gets written.
        self.logger.debug('Writing status page')
        with open(os.path.join(self.cabinet_dir, status_filename), 'w') as df:
            content = self.status_template.render({
                'gen_time': datetime.datetime.now(datetime.timezone(datetime.timedelta())),
                'errors': self.error_list,
                })
            df.write(content)

        # Commit-related git actions
        if do_git and do_git_commit:

            self.logger.debug('Prepping for wiki repo commit')

            # Delete pages which no longer exist
            for filename in wiki_files:
                if filename not in created_pages:
                    try:
                        self.logger.debug('Marking file for deletion: {}'.format(filename))
                        wikirepo.git.rm('--', filename)
                    except git.exc.GitCommandError as e:
                        # If I have a file open or whatever in here with a .swp file, or
                        # if some file exists which is outside the repo, we'll get this
                        # error.  Let's not die just because of that.
                        self.logger.error('Could not "git rm" on filename: {}'.format(filename))

            # Mark any new files as to-be-added
            for filename in wikirepo.untracked_files:
                self.logger.debug('Marking file for addition: {}'.format(filename))
                wikirepo.git.add('--', filename)

            # Commit all wiki changes and push, if we need to (which we should, since About
            # always gets updated)
            if wikirepo.is_dirty():
                self.logger.debug('Committing wiki repo changes')
                wikirepo.git.commit('-a', '-m', 'Auto-update from bl3cabinetsorter')
                wikirepo.git.push()
            else:
                self.logger.debug('No git changes to commit')
        else:
            self.logger.info('Skipping wiki repo commit')

        # Write out our mod cache
        self.logger.debug('Writing caches')
        self.mod_cache.save()
        self.readme_cache.save()
        self.info_cache.save()
        self.author_cache.save()
        self.templatemtime_cache.save()

    def write_wiki_file(self, wiki_files, filename, content):
        """
        Write out a file to the wiki, so long as the content has changed
        """
        # TODO: is this method, um, dumb?  It's only used on staticish pages, so
        # we should maybe just write indiscriminately.  Or maybe use a FileCache?
        full_filename = os.path.join(self.cabinet_dir, filename)
        do_write = True
        if filename in wiki_files:
            with open(full_filename) as df:
                cur_content = df.read()
                if cur_content == content:
                    do_write = False
        if do_write:
            with open(full_filename, 'w') as df:
                df.write(content)

    def do_initial_tasks(self):
        """
        Initial first-time-run tasks which need to happen.  Namely: update
        all the file mtimes in the git repo checkout to match their git-tree
        mtimes.  This is something which we could also just do as we loop
        through the repo, instead, but I don't really care enough to figure
        out how to use the more-efficient low-level gitpython functions to
        do the lookups, as opposed to the higher-level API that we're using.
        """

        repo = git.Repo(self.repo_dir)
        for (dirpath, dirnames, filenames) in os.walk(self.repo_dir):
            if '.git' not in dirpath:
                for filename in filenames:
                    full_filename = os.path.join(dirpath, filename)
                    try:
                        git_mtime = int(repo.git.log('-n', '1', '--format=%ct', full_filename))
                        os.utime(full_filename, (git_mtime, git_mtime))
                    except ValueError as e:
                        print('ERROR: Invalid mtime returned for {}'.format(full_filename))
