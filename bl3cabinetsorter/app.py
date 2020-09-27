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
# Borderlands ModCabinet Sorter is distributed in the hope that it will
# be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Borderlands ModCabinet Sorter.  If not, see
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
        if len(path_components) > 1:
            self.dir_author = path_components[1]
        else:
            self.dir_author = '(unknown)'
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
        self.mods = {}
        self.cur_mods = {}

    def _serialize(self):
        return {
                'n': self.name,
                'g': dict([(game, list(modset)) for (game, modset) in self.mods.items()]),
                }

    def _unserialize(self, input_dict):
        self.name = input_dict['n']
        for (game, modlist) in input_dict['g'].items():
            self.mods[game] = set(modlist)

    def add_mod(self, mod):
        if mod.game not in self.cur_mods:
            self.cur_mods[mod.game] = set()
        self.cur_mods[mod.game].add(mod.wiki_link())

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

class ModFile(Cacheable):
    """
    Class to pull info out of a mod file.
    """

    cache_key = 'mods'

    def __init__(self, mtime, dirinfo=None, filename=None, initial_status=Cacheable.S_UNKNOWN, game=None):
        super().__init__(mtime, initial_status)
        self.mod_time = datetime.datetime.fromtimestamp(mtime)
        self.mod_title = None
        self.mod_title_display = None
        self.wiki_filename_base = None
        self.mod_desc = []
        self.readme_rel = None
        self.readme_desc = []
        self.nexus_link = None
        self.screenshots = []
        self.youtube_urls = []
        self.urls = []
        self.categories = set()
        self.changelog = []
        self.related_links = []
        self.re = Re()
        self.game = game

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
                if first_line.strip() == '':
                    first_line = df.readline()
                if '<BLCMM' in first_line:
                    self.load_blcmm(df)
                elif first_line.startswith('#<'):
                    self.load_ft(df)
                else:
                    self.load_unknown(df)
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
                'd': self.mod_desc,
                'r': self.readme_desc,
                'l': self.readme_rel,
                'o': self.changelog,
                'e': sorted(self.related_links),
                'n': nl,
                's': [str(s) for s in self.screenshots],
                'y': [str(y) for y in self.youtube_urls],
                'u': [str(u) for u in self.urls],
                'c': list(self.categories),
                'g': self.game,
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
        self.youtube_urls = [ModURL(u) for u in input_dict['y']]
        self.urls = [ModURL(u) for u in input_dict['u']]
        self.categories = set(input_dict['c'])
        self.game = input_dict['g']

    def get_full_rel_filename(self):
        """
        Returns our "full" relative filename
        """
        return os.path.join(self.rel_path, self.rel_filename)

    def set_categories(self, categories):
        """
        Sets our categories, updating our status if need be
        """
        self.seen = True
        new_cats = set(categories)
        if new_cats != self.categories:
            if self.status != Cacheable.S_NEW:
                self.status = Cacheable.S_UPDATED
            self.categories = new_cats

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

    def set_urls(self, urls):
        """
        Finalize our URLs, which will put them into the appropriate
        data structures, and also update our status to S_UPDATED if
        need be.
        """
        self.seen = True
        nexus_link = None
        screenshots = []
        youtube_urls = []
        new_urls = []
        for url in urls:
            url_lower = url.lower()
            if 'nexusmods.com' in url_lower:
                nexus_link = ModURL(url)
            elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
                youtube_urls.append(ModURL(url))
            elif url_lower.endswith('.jpg') or url_lower.endswith('.png') or url_lower.endswith('.gif'):
                screenshots.append(ModURL(url))
            else:
                new_urls.append(ModURL(url))
        if (self.status != Cacheable.S_NEW
                and (nexus_link != self.nexus_link
                    or screenshots != self.screenshots
                    or youtube_urls != self.youtube_urls
                    or new_urls != self.urls
                    )):
            self.status = Cacheable.S_UPDATED
        self.screenshots = screenshots
        self.nexus_link = nexus_link
        self.youtube_urls = youtube_urls
        self.urls = new_urls

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

    def load_blcmm(self, df):
        """
        Loads in a BLCMM-formatted file.  The idea is to grab the first category
        name, as the title of the mod, and then the first comment block we find.
        """
        finding_main_cat = True
        reading_comments = False
        cat_re = re.compile('<category name="(.*?)"(>| MUT=)')
        comment_re = re.compile('<comment>(.*)</comment>')
        for line in df.readlines():
            if finding_main_cat:
                if self.re.search(cat_re, line):
                    self.mod_title = self.re.last_match.group(1).strip().replace('\\"', '"')
                    finding_main_cat = False
            elif reading_comments:
                if self.re.search(comment_re, line):
                    self.add_comment_line(self.re.last_match.group(1))
                else:
                    # If we got here, we had some comments but found Something Else.
                    # Stop processing at this point
                    return
            else:
                if self.re.search(comment_re, line):
                    reading_comments = True
                    self.add_comment_line(self.re.last_match.group(1))

    def load_ft(self, df):
        """
        Loads in a FilterTool-formatted file.  The idea is to grab the first category
        name, as the title of the mod, and then the first comment block we find.  This
        is a bit trickier than BLCMM files since comments are just plaintext inline
        with everything else.
        """
        df.seek(0)
        temp_mod_name = os.path.split(self.full_filename)[-1].rsplit('.', 1)[0]
        finding_main_cat = True
        reading_comments = False
        cat_re = re.compile('#<(.*?)>')
        for line in df.readlines():
            if finding_main_cat:
                if self.re.search(cat_re, line):
                    self.mod_title = self.re.last_match.group(1).strip()
                    if self.mod_title.lower() == 'patch' or self.mod_title.lower() == 'mod':
                        self.mod_title = temp_mod_name
                    finding_main_cat = False
            else:
                stripped = line.strip()
                if '#<hotfix>' not in line and self.re.search(cat_re, line):
                    # Unlike the BLCMM processing, at the moment, we're not allowing
                    # comments after nested categories, though we *are* if there's
                    # a "description" folder, since that's a real common way that
                    # FT files get laid out.
                    if 'description' not in self.re.last_match.group(1).lower():
                        return
                elif stripped.startswith('set '):
                    return
                elif stripped.startswith('#<hotfix>'):
                    return
                elif stripped != '':
                    self.add_comment_line(line)

    def load_unknown(self, df):
        """
        Loads in a presumably freeform-text mod.  Mostly just assume everything up to
        the first `set` statement is a comment, I guess.  Initially take the filename
        (minus extension) to be the mod name, but if the first comment line we
        find happens to match close enough to the filename, we'll use that for the 
        title instead.
        """
        temp_mod_name = os.path.split(self.full_filename)[-1].rsplit('.', 1)[0]
        df.seek(0)
        for line in df.readlines():
            if line.strip().startswith('set ') or line.strip().startswith('#<'):
                break
            else:
                self.add_comment_line(line, match_title=temp_mod_name)
        if not self.mod_title:
            self.mod_title = temp_mod_name

        # Some really-badly-formatted files are nearly FT-compatible but
        # are missing the hash mark in front of the XMLish stuff.  Check
        # to see if our name happens to be enclosed in angle-brackets, and
        # strip them out if so.
        if self.mod_title[0] == '<' and self.mod_title[-1] == '>':
            self.mod_title = self.mod_title[1:-1]

    def add_comment_line(self, comment_line, match_title=None):
        """
        Adds a comment line to our description, attempting to strip out some common
        comment prefixes and do some general data massaging.  If `match_title` isn'
        `None`, and this is the first comment line to be inserted, check to see if
        the line is similar to the given title, and set the mod title to be that
        comment line.
        """

        # Take off any whitespace and comment characters
        line = comment_line.strip("/#\n\r\t ")
        
        # Prevent adding an empty line at the beginning
        if line == '' and len(self.mod_desc) == 0:
            return

        # Prevent adding more than one empty line in a row
        if len(self.mod_desc) > 0 and self.mod_desc[-1] == '' and line == '':
            return

        # Attempt to prevent adding in header ASCII art
        if len(self.mod_desc) == 0 and line.strip("[]_/\\.:|#~ \t") == '':
            return

        # Attempt to match on a title, if we can (and return without adding,
        # if that's the case)
        if not self.mod_title and match_title and len(self.mod_desc) == 0:
            if Levenshtein.ratio(match_title.lower(), line.lower()) > .8:
                self.mod_title = line
                return

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
            self.mapping[full_filename] = self.cache_class(mtime, dirinfo, filename, initial_status, **extra)
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

class CabinetModInfo(object):
    """
    A little class to hold info about a single mod definition inside
    a `cabinet.info` file.  Just a glorified dictionary, really.  I'd
    use a namedtuple, but we need to be able to dynamically add to
    the 'urls' array
    """

    def __init__(self, filename, categories):
        self.filename = filename
        self.categories = categories
        self.urls = []
    
    def add_url(self, url):
        self.urls.append(url)

    def serialize(self):
        """
        Returns a dict which describes this entry
        """
        return {
                'f': self.filename,
                'c': self.categories,
                'u': self.urls,
                }

    def unserialize(self, input_dict):
        """
        Unserialize ourselves from an input dictionary
        """
        self.filename = input_dict['f']
        self.categories = input_dict['c']
        self.urls = input_dict['u']

class CabinetInfo(Cacheable):
    """
    Simple little class to read in and parse our `cabinet.info` files
    """

    cache_key = 'info'

    def __init__(self, mtime, dirinfo=None, filename=None, initial_status=Cacheable.S_UNKNOWN,
            rel_filename=None, error_list=None, valid_categories=None):
        """
        Initialize with the given `mtime` and a bunch of other optional info.  In
        general this will only really be called from the `FileCache` class, when
        it encounters a situation where a newer (or just new) file is found on
        disk.  To initialize an object just for testing, all that's needed is `mtime`.
        Optionally, though, pass in:
            `dirinfo` - A DirInfo object describing the directory we're found in
            `filename` - Our filename (without path)
            `initial_status` - Our initial cache status
            `rel_filename` - The relative filename to report to the user in errors
            `error_list` - An array we can append load errors to
            `valid_categories` - A dict describing the valid categories which can be
                found in the info file
        """
        super().__init__(mtime, initial_status)
        self.rel_filename = None
        self.error_list = None
        self.valid_categories = None
        self.mods = {}
        self.single_mod = False
        self.errors = False
        if rel_filename:
            full_filename = dirinfo[filename]
            self.load_from_filename(full_filename, rel_filename, error_list, valid_categories)

    def has_errors(self):
        """
        Return whether or not we have errors
        """
        return self.errors

    def _serialize(self):
        """
        Returns a serializable dict describing ourselves
        """
        return {
                'r': self.rel_filename,
                's': self.single_mod,
                'o': dict([(k, v.serialize()) for k, v in self.mods.items()]),
                }

    def _unserialize(self, input_dict):
        """
        Populates ourself given the specified serialized dict
        """
        self.rel_filename = input_dict['r']
        self.single_mod = input_dict['s']
        self.mods = {}
        for k, mod_dict in input_dict['o'].items():
            # 'null' is usually converted automatically to None when loading
            # JSON, but JSON dicts can't have null as the key, so it becomes
            # a string rather than a keyword, and we have to check for it.
            if k == 'null':
                k = None
            self.mods[k] = CabinetModInfo(None, [])
            self.mods[k].unserialize(mod_dict)

    def load_from_filename(self, filename, rel_filename, error_list, valid_categories):
        """
        Load from the given filename
        """
        with open(filename) as df:
            self.load_from_file(df, rel_filename, error_list, valid_categories)

    def load_from_file(self, df, rel_filename, error_list, valid_categories):
        """
        Loads our information from the given `filename`.  `rel_filename` will
        be the filename reported in errors, if we run into any, and should have
        any unneeded prefixes already shaved off.
        """
        prev_modfile = None
        single_mod = False

        self.rel_filename = rel_filename
        self.error_list = error_list
        self.valid_categories = valid_categories

        # Now read cabinet.info to find mod files
        for line in df.readlines():
            if line.strip() == '' or line.startswith('#'):
                pass
            elif line.startswith('http://') or line.startswith('https://') or '|http' in line:
                if prev_modfile in self.mods:
                    self.mods[prev_modfile].add_url(line.strip())
                else:
                    self.errors = True
                    self.error_list.append('ERROR: Did not find previous modfile but got URL, in `{}`'.format(
                        self.rel_filename))
            else:
                if ': ' in line:
                    if self.single_mod:
                        self.errors = True
                        self.error_list.append('ERROR: Unknown line "{}" found in single-mod info file `{}`'.format(
                            line.strip(), self.rel_filename))
                    else:
                        if line[0] == '\\':
                            line = line[1:]
                        (mod_filename, mod_categories) = line.split(': ', 1)
                        if self.register(mod_filename, mod_categories):
                            prev_modfile = mod_filename
                else:
                    if len(self.mods) > 0:
                        self.errors = True
                        self.error_list.append('ERROR: Unknown line "{}" inside `{}`'.format(
                            line.strip(), self.rel_filename))
                    else:
                        self.single_mod = True
                        if self.register(None, line.strip()):
                            prev_modfile = None

    def register(self, mod_name, mod_categories):
        """
        Registers a mod line that we've found in a `cabinet.info` file.
        Will double-check against the list of valid categories and return
        False if the mod was not registered.
        """

        # First check to make sure we don't already have this mod
        if mod_name in self.mods:
            self.errors = True
            self.error_list.append('ERROR: {} specified twice inside `{}`'.format(
                mod_name, self.rel_filename))
            return False

        # Split up the category list and assign it
        real_cats = []
        cats = [c.strip() for c in mod_categories.lower().split(',')]
        for cat in cats:
            if cat in self.valid_categories:
                real_cats.append(cat)
            else:
                self.errors = True
                self.error_list.append('WARNING: Invalid category "{}" in `{}`'.format(
                    cat, self.rel_filename,
                    ))

        # If we have categories which are valid, continue!
        if len(real_cats) > 0:
            self.mods[mod_name] = CabinetModInfo(mod_name, real_cats)
            return True
        else:
            if mod_name:
                report = mod_name
            else:
                report = 'the mod'
            self.errors = True
            self.error_list.append('ERROR: No categories found for {} in `{}`'.format(report, self.rel_filename))
            return False

    def modlist(self):
        """
        Returns our list if CabinetModInfo objects
        """
        return self.mods.values()

    def __getitem__(self, key):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return self.mods[key]

    def __contains__(self, key):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return key in self.mods

    def __len__(self):
        """
        Convenience function to be able to use this sort of like a dict
        """
        return len(self.mods)

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

    def wiki_filename(self, game):
        global wiki_filename
        return wiki_filename('{} {}'.format(game.abbreviation, self.full_title))

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

    def __init__(self, abbreviation, dir_name, title):
        self.abbreviation = abbreviation
        self.dir_name = dir_name
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

    # Games that we support
    games = collections.OrderedDict([
            ('BL2', Game('BL2', 'Borderlands 2 mods', 'Borderlands 2')),
            ('TPS', Game('TPS', 'Pre Sequel Mods', 'Pre-Sequel')),
            ])

    # Valid Categories
    categories = collections.OrderedDict([

        # Major Modpacks
        ('major-pack', Category('Major Overhauls and Mod Packs')),

        # General Gameplay and Balance
        ('mode-balance', Category('General Gameplay and Balance: Game Mode Balance')),
        ('scaling', Category('General Gameplay and Balance: Scaling Changes')),
        ('element', Category('General Gameplay and Balance: Elements and Damage Types')),
        ('quest-changes', Category('General Gameplay and Balance: Quest Changes')),
        ('currency', Category('General Gameplay and Balance: Currencies')),
        ('gameplay', Category('General Gameplay and Balance: Other Gameplay Changes')),

        # Characters and Skills
        ('char-overhaul', Category('Characters and Skills: Full Character Overhauls')),
        ('skill-system', Category('Characters and Skills: Skill System Changes')),
        ('char-axton', Category('Characters and Skills: Axton Changes')),
        ('char-gaige', Category('Characters and Skills: Gaige Changes')),
        ('char-krieg', Category('Characters and Skills: Krieg Changes')),
        ('char-maya', Category('Characters and Skills: Maya Changes')),
        ('char-sal', Category('Characters and Skills: Salvador Changes')),
        ('char-zero', Category('Characters and Skills: Zer0 Changes')),
        ('char-athena', Category('Characters and Skills: Athena Changes')),
        ('char-aurelia', Category('Characters and Skills: Aurelia Changes')),
        ('char-claptrap', Category('Characters and Skills: Claptrap Changes')),
        ('char-jack', Category('Characters and Skills: Jack Changes')),
        ('char-nisha', Category('Characters and Skills: Nisha Changes')),
        ('char-wilhelm', Category('Characters and Skills: Wilhelm Changes')),
        ('char-other', Category('Characters and Skills: Other Character Changes')),

        # Weapons/Gear
        ('gear-general', Category('Weapons/Gear: General')),
        ('gear-brand', Category('Weapons/Gear: Brand Overhauls')),
        ('gear-pack', Category('Weapons/Gear: Packs')),
        ('gear-ar', Category('Weapons/Gear: Assault Rifles')),
        ('gear-laser', Category('Weapons/Gear: Lasers')),
        ('gear-pistol', Category('Weapons/Gear: Pistols')),
        ('gear-launcher', Category('Weapons/Gear: Rocket Launchers')),
        ('gear-shotgun', Category('Weapons/Gear: Shotguns')),
        ('gear-smg', Category('Weapons/Gear: SMGs')),
        ('gear-sniper', Category('Weapons/Gear: Sniper Rifles')),
        ('gear-grenade', Category('Weapons/Gear: Grenade Mods')),
        ('gear-com', Category('Weapons/Gear: COMs')),
        ('gear-shield', Category('Weapons/Gear: Shields')),
        ('gear-relic', Category('Weapons/Gear: Relics')),
        ('gear-ozkit', Category('Weapons/Gear: Oz Kits')),

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
        self.info_cache_filename = os.path.join(self.cache_dir, 'infocache.json.xz')
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
        self.info_cache = FileCache(CabinetInfo, self.info_cache_filename, do_load=load_cache)
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
        for game in self.games.values():
            seen_cats[game.abbreviation] = {}

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
        for game in self.games.values():
            reserved_pages.add(game.wiki_filename())
            for cat in self.categories.values():
                reserved_pages.add(cat.wiki_filename(game))

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
        for game in self.games.values():
            game_dir = os.path.join(self.repo_dir, game.dir_name)
            for (dirpath, dirnames, filenames) in os.walk(game_dir):

                # Make a mapping of files by lower-case, so that we can
                # match case-insensitively
                dirinfo = DirInfo(self.repo_dir, dirpath, filenames)

                # Read our info file, if we have it.
                if 'cabinet.info' in dirinfo:

                    # Load in readme info, if we can.
                    readme = None
                    if dirinfo.readme:
                        readme = self.readme_cache.load(dirinfo, dirinfo.readme)

                    # Read the file info
                    cabinet_filename = dirinfo['cabinet.info']
                    rel_cabinet_filename = cabinet_filename[len(self.repo_dir)+1:]
                    cabinet_info = self.info_cache.load(dirinfo, 'cabinet.info',
                            rel_filename=rel_cabinet_filename,
                            error_list=self.error_list,
                            valid_categories=self.categories,
                            )

                    # Loop through the mods described by cabinet.info and load them
                    processed_files = []
                    if cabinet_info.single_mod:
                        # Make sure that a valid category was found
                        if None in cabinet_info.mods:
                            cabinet_info_mod = cabinet_info.mods[None]
                            # Scan for which file to use -- just a single mod file in
                            # this dir.  First look for .blcm files.
                            for blcm_file in dirinfo.get_all_with_ext('blcm'):
                                processed_files.append((cabinet_info_mod, self.mod_cache.load(dirinfo, blcm_file, game=game.abbreviation)))
                                # We're just going to always take the very first .blcm file we find
                                break
                            if len(processed_files) == 0:
                                for txt_file in dirinfo.get_all_with_ext('txt'):
                                    if 'readme' not in txt_file.lower():
                                        processed_files.append((cabinet_info_mod, self.mod_cache.load(dirinfo, txt_file, game=game.abbreviation)))
                                        # Again, just grab the first one
                                        break
                            if len(processed_files) == 0:
                                for random_file in dirinfo.get_all():
                                    if 'readme' not in random_file.lower() and 'changelog' not in random_file.lower() and 'cabinet.info' not in random_file.lower():
                                        processed_files.append((cabinet_info_mod, self.mod_cache.load(dirinfo, random_file, game=game.abbreviation)))
                                        # Again, just grab the first one
                                        break
                    else:
                        for cabinet_info_mod in cabinet_info.modlist():
                            try:
                                processed_files.append((cabinet_info_mod, self.mod_cache.load(dirinfo, cabinet_info_mod.filename, game=game.abbreviation)))
                            except KeyError:
                                self.error_list.append('ERROR: Invalid modfile `{}` specified in `{}`'.format(
                                    cabinet_info_mod.filename,
                                    rel_cabinet_filename,
                                    ))

                    # Do Stuff with each file we got
                    for (cabinet_info_mod, processed_file) in processed_files:

                        # See if we've got a "better" description in a readme
                        if readme:
                            readme_info = readme.find_matching(processed_file.mod_title, cabinet_info.single_mod)
                            if cabinet_info.single_mod:
                                changelog = readme.find_matching('changelog', False)
                            else:
                                changelog = []
                        else:
                            readme_info = []
                            changelog = []
                        processed_file.update_readme_desc(readme, readme_info)
                        processed_file.update_changelog(changelog)

                        # Set our categories (if we'd read from cache, they may have changed)
                        processed_file.set_categories(cabinet_info_mod.categories)
                        for cat in cabinet_info_mod.categories:
                            if cat not in seen_cats[game.abbreviation]:
                                seen_cats[game.abbreviation][cat] = []
                            seen_cats[game.abbreviation][cat].append(processed_file)

                        # Set our URLs (likewise, if from cache then they may have changed)
                        processed_file.set_urls(cabinet_info_mod.urls)

                        # Previously we were adding mods to our author cache here, but we need
                        # to wait until we resolve any potential mod name conflicts first, so
                        # that's now happening later...

                        # Add to our name_resolution object for later processing
                        title_lower = processed_file.mod_title.lower()
                        if title_lower not in name_resolution:
                            name_resolution[title_lower] = {}
                        if game not in name_resolution[title_lower]:
                            name_resolution[title_lower][game] = {}
                        author_lower = processed_file.mod_author.lower()
                        if author_lower not in name_resolution[title_lower][game]:
                            name_resolution[title_lower][game][author_lower] = {}
                        name_resolution[title_lower][game][author_lower][processed_file.rel_filename] = processed_file.full_filename

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
        for (mod_title, mod_games) in name_resolution.items():
            shared_set = set()
            need_game = (len(mod_games) > 1)
            for (game, mod_authors) in mod_games.items():
                if need_game:
                    game_suffix = ' - {}'.format(game.abbreviation)
                else:
                    game_suffix = ''
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
                            new_filename = '{}{}{}{}'.format(
                                    mod_obj.mod_title,
                                    filename_suffix,
                                    author_suffix,
                                    game_suffix,
                                    )
                            new_title_display = '{}{}{}'.format(
                                    mod_obj.mod_title,
                                    filename_suffix,
                                    game_suffix,
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
        multi_game_cats = {}
        for game in self.games.values():
            game_cats = []
            multi_game_cats[game.abbreviation] = game_cats
            for (cat_key, cat) in self.categories.items():
                if cat_key in seen_cats[game.abbreviation]:
                    game_cats.append(cat)

                    # Write out the category page
                    cat_filename = cat.wiki_filename(game)
                    created_pages.add(cat_filename)
                    self.write_wiki_file(wiki_files,
                            cat_filename,
                            self.cat_template.render({
                                'game': game,
                                'cat': cat,
                                'mods': sorted(seen_cats[game.abbreviation][cat_key]),
                                'authors': self.author_cache,
                                }),
                            )

            # Write out the game page, linking to all categories which have mods
            game_filename = game.wiki_filename()
            created_pages.add(game_filename)
            self.write_wiki_file(wiki_files,
                    game_filename,
                    self.game_template.render({
                        'game': game,
                        'categories': game_cats,
                        })
                    )

        # Write out sidebar
        self.logger.debug('Writing sidebar')
        self.write_wiki_file(wiki_files,
                sidebar_filename,
                self.sidebar_template.render({
                    'games': self.games.values(),
                    'cats': self.categories,
                    'seen_cats': multi_game_cats,
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
                            'games': self.games,
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
