Borderlands 3 ModCabinet Sorter
===============================

This is an attempt to create an automated ModCabinet wiki for the BL3
mods housed in the bl3mods github.

The util will attempt to loop through a local github checkout, looking for
mods with the extension `.bl3hotfix`, which contain the necessary metadata
at the top of the mod files.  Specifically they need to have a `Name`,
`Author`, and `Categories` label.  The app should be able to read in mod
summaries both from the mod files themselves, and from README files stored
alongside the mods.

Obviously it's a bit insane to try and write something to parse through a
bunch of effectively freeform text all over the place, but hopefully it
can be wrangled into something useful, which can then be run every 15
minutes or something.

At the moment, the app works quite well, with the caveats of the items
noted in the TODO below.  I will eventually get some better documentation
in here about how to get this running, in case anyone else ever needs/wants
to take over generating these pages.

Requirements
------------

This is a Python 3 app.  It may work in Python 2 but no attempt has been
made to find out.  Required modules (installable via `pip`, of course):

- `gitpython`
- `Jinja2`
- `python-Levenshtein`
- `appdirs`
- `coverage` (only to run coverage on the unit tests, for development
  purposes.  Not needed just to run.)

How To Use
----------

In case Apocalyptech ever gets hit by a bus or something, someone else
might end up wanting to take over running this thing.  Here's how:

1. Set up a Python virtual env for the app, wherever you like, using
   `python3 -m venv bl3cabinetsorter` (or whatever you want to call it).
   That'll create a new `bl3cabinetsorter` dir in your current dir,
   containing the venv.
2. Activate the venv using `. bl3cabinetsorter/bin/activate` (the dot
   at the beginning is important).  Your command prompt should now
   have a `(bl3cabinetsorter)` prefix on it, to indicate that you're
   operating "in" that venv.
3. Run `pip install --upgrade pip` to get on the latest version of the
   python package manager (this step's optional, but it'll nag you
   until it's up-to-date anyway, so you might as well).
4. Go into the dir where you've checked out this project, and install
   the dependencies with: `pip install -r requirements.txt`, or just
   install them one by one with `pip install <module>`, from the list
   above.
  4a. `requirements.txt` doesn't list the `coverage` module since that's
      only used in conjunction with unit tests, so if you care about
      running those, you might want to install `coverage` too.  If you're
      just *running* the sorter, though, don't sweat it.
5. Run `sorter.py` once; it'll complain that you don't have a config
   file set up, but more importantly it'll tell you the path that it's
   looking for, for the file.
6. Copy `bl3cabinetsorter.ini.example` so that the app will find it.
   On a Linux machine that'll likely be `~/.config/bl3cabinetsorter/bl3cabinetsorter.ini`
7. The `mods` section of the INI file describes the mod repo itself.
  7a. `clone_url` can just be the anonymous HTTPS URL used to clone the
     repo.
  7b. `base_url` is the base URL used to link directly to files
      inside the repo (usually the same as `clone_url` but with `.git`
      changed to `/tree/master`).
  7c. `download_url` is the URL used to embed screenshots in our markdown
      files, and will have a `raw.githubusercontent.com` hostname.
  7d. `repo_dir` is the checkout location of the repo on-disk.  I keep
      them inside the `repos` directory right inside the `bl3cabinetsorter`
      checkout.
8. The `wiki` section of the INI file describes the wiki repo itself
   (github project wikis are really just separate github repos themselves.)
  8a. `clone_url` is the URL used to check out the wiki.  github itself will
      not actually show the correct URL here -- it'll only tell you the
      "anonymous" HTTPS url.  You need to use the SSH-based URL which lets
      you push new content, etc.  Its form will be `git@github.com:BLCM/BL3ModCabinet.wiki.git`.
      On my own system, I'm doing some shenanigans where I upload using
      an account different from my "main" github account,  so I actually
      specify the hostname bit there as `github.com-apocalyptechcabinet`,
      which I've configured SSH to use an alternate `IdentityFile`, and
      set the `HostName` to `github.com` and `User` to `git`.  If you don't
      care about using a separate github user for this, don't bother with
      that -- just use the URL mentioned earlier.
  8b. `cabinet_dir` is the checkout location of the wiki repo on-disk.
      Like the mods repo, I keep it inside the `repos` directory right inside
      the `bl3cabinetsorter` checkout.
9. Manually check out both the mods repo and the wiki repo -- the app
   currently doesn't support doing that automatically.  If you're keeping
   them checked out in the `repos` subdir, simply go in there, and do a
   `git clone` using the `clone_url`s for both the "mods" and "wiki" section
   of the INI file you just configured.
  9a. Note that if you're starting this up on a brand *new* github wiki, the
      wiki needs to have at least the main page, so create the first page from
      the web UI and *then* do your checkouts.
  9b. Doublecheck that the resulting `repos/bl3mods` dir contains a checkout of
      the mod archive, and the `repos/BL3ModCabinet.wiki` contains a checkout
      of the current wiki.
10. By default, the sorter will only Do Things if it notices that there's been
    an update to the mods repo.  Since you just checked it out, there probably
    won't be changes yet, to you'll want to use the `-f`/`--force` flag to
    force it to Do Stuff regardless.  Also, for your very first time running
    the app, you'll want to use the `-i`/`--initial` flag, which sets the
    file modification times for all the files in the `bl3mods` checkout.  (This
    is useful because it uses the file modification times to populate the
    "last updated" report on the mod pages.  Otherwise the reported "last
    updated" times will end up being the timestamp when you cloned the repo.)
  10a. If you want to just test things out, you can also use the `-g`/`--no-git`
       flag to prevent the app from trying to interact with github in any way.
       The app also keeps caches of it's "remembered" state of the bl3mods repo
       in the `cache` dir.  You can clean that dir out whenever you like, or just
       use the `-x`/`--ignore-cache` argument to ignore it.  There's a few other
       options which can be used, use `-h`/`--help` to see them all.
11. Once you're confident that it's working properly, you'll want to hook it
    up an automated process which runs it occasionally.  I wouldn't recommend
    doing it more often than every 10 minutes.  My cron line looks like this:
    `5,15,25,35,45,55 * * * * cd /home/pez/git/b2patching/bl3cabinetsorter && /home/pez/virtualenv/mcpbl3cabinetsorter/bin/python /home/pez/git/b2patching/bl3cabinetsorter/sorter.py -q`
  11a. Using the `-q`/`--quiet` option will prevent the app from outputting any
       text unless there's an actual error with processing.  This way your
       system running the cron won't send you an email unless there's a problem
       which might need your attention.

TODO
----

- Support doing initial git clones?
- README/Mod Description parsing could probably use some tweaking,
  but will have to do that carefully, of course.
- Expand unit tests, and fix the couple that we're skipping
  - Make sure to test specifying a filename which doesn't exist
  - Test unicode vs. latin1 mod files
  - ModFile sorting (case-insensitive)
  - `wiki_filename` processing
  - We've moved to always using full HTML HREFs instead of wiki
    links, when calling `wiki_link`
  - Test `__eq__` on ModURL objects for the various tests in there
- The first time the app is run, without caches to read from, mods
  which share the name of an author will error out instead of being
  generated.  That will get fixed on subsequent runs which do read
  from the cache.  I don't care enough to fix that edge case at the
  moment, but it may bear looking into later.  (In the BL2 space,
  vWolvenn's "Tsunami" is the only current case of this actually
  happening.)
- If we get a CRITICAL error midway through processing, the next run
  will *not* try again, because the `git pull` has already happened
  and it looks like there's nothing to do.  I think we'll have to
  cache the git commit at which we last successfully run, and compare
  against that.
- See if we can get rid of our `full_filename` var in ModFile.  I bet
  we can...

License
-------

Borderlands 3 ModCabinet Sorter is licensed under the
[GPLv3 or later](https://www.gnu.org/licenses/quick-guide-gplv3.html).
See [COPYING.txt](COPYING.txt) for the full text of the license.

