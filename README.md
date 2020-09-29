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

