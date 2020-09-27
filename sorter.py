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
import sys
import appdirs
import argparse
from bl3cabinetsorter.app import App

if __name__ == '__main__':

    # Figure out a default INI file location if we weren't passed anything
    default_config_file = os.path.join(
            appdirs.user_config_dir('bl3cabinetsorter', 'Apocalyptech'),
            'bl3cabinetsorter.ini',
            )

    parser = argparse.ArgumentParser(
            description='BLCM BL3 ModCabinet Auto-Sorter',

            # The "defaults" formatter ends up being weird since most of our
            # booleans are setting False rather than True, so don't use it.
            #formatter_class=argparse.ArgumentDefaultsHelpFormatter,

            # Note that all text will get mashed together in a single paragraph
            # regardless of formatting here, so don't sweat that too much.
            epilog="""
                Use the -g/--no-git or -c/--no-commit options to avoid
                git integration, which can be quite useful when you're
                iterating through code/template changes but probably not of
                much use otherwise.

                The -i/--initial argument will also do an initial
                "first-time-run" task of looping through the github repo
                setting all file mtimes to be equal to their most-
                recently-updated timestamp in the git tree.

                By default the app will quit early when no update is found in
                the mods repo, but -f/--force can be used to force it to
                continue regardless.

                -q/--quiet and -v/--verbose can be used to control how much
                information is printed on the console while running.  With
                quiet mode, only critical errors will be printed.

                The default config file location is at `{}`.  To specify an
                alternate config file, use -o/--config.  Use the file
                `bl3cabinetsorter.ini.example` as a basis for the file.

                To ignore any existing caches and make a run from scratch,
                specify -x/--ignore-cache.

                """.format(default_config_file)
            )

    parser.add_argument('-g', '--no-git',
            dest='do_git',
            action='store_false',
            help='Don\'t interact with git in any way while running (implies --no-commit)',
            )

    parser.add_argument('-c', '--no-commit',
            dest='do_git_commit',
            action='store_false',
            help='Don\'t do any git commit actions after processing.',
            )

    parser.add_argument('-i', '--initial',
            dest='do_initial_tasks',
            action='store_true',
            help='Do some first-time-run initial tasks to get the github repo dir ready',
            )

    parser.add_argument('-f', '--force',
            action='store_true',
            help='Force update of wiki even if there have not been any repo changes',
            )

    parser.add_argument('-o', '--config',
            default=default_config_file,
            help='Specify a path to a configuration INI file',
            )

    parser.add_argument('-x', '--ignore-cache',
            dest='load_cache',
            action='store_false',
            help='Ignore any existing cache files and load everything from scratch.',
            )

    loggroup = parser.add_mutually_exclusive_group()

    loggroup.add_argument('-q', '--quiet',
            action='store_true',
            help='Supress all but critical error messages',
            )

    loggroup.add_argument('-v', '--verbose',
            action='store_true',
            help='Print as much information as possible',
            )

    args = parser.parse_args()

    # Check to make sure our config file exists
    if not os.path.exists(args.config):
        raise Exception('Could not find config file {}'.format(args.config))

    app = App(args.config)
    sys.exit(app.run(
            do_git=args.do_git,
            do_git_commit=args.do_git_commit,
            do_initial_tasks=args.do_initial_tasks,
            force_run=args.force,
            quiet=args.quiet,
            verbose=args.verbose,
            load_cache=args.load_cache,
            ))
