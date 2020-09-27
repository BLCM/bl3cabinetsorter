[[← Go Back|Home]]

Contributing to the ModCabinet wiki is quite easy if you've already checked
in your mod to the Github.  Here's how!

- [Adding Your Mod to ModCabinet](#adding-your-mod-to-modcabinet)
- [Assigning Categories](#assigning-categories)
- [Assigning Multiple Categories](#assigning-multiple-categories)
- [Update Frequency / Error Reporting](#update-frequency--error-reporting)
- [Screenshots and Nexus Mods Links](#screenshots-and-nexus-mods-links)
- [Comments](#comments)
- [Mods Whose Filenames Start With A Hash Sign](#mods-whose-filenames-start-with-a-hash-sign-)
- [Formatting your README for Maximum Results](#formatting-your-readme-for-maximum-results)

## Adding Your Mod to ModCabinet

In order to have your mods listed in the ModCabinet, they have to be uploaded
to [the main BLCMods Github repostiory](https://github.com/BLCM/BLCMods).  There
are instructions for doing so [at the BLCMods Wiki](https://github.com/BLCM/BLCMods/wiki/Contribution).

Once you know how to do that, getting your mod in this wiki is easy: you just
need to add another file alongside your mod, named `cabinet.info`.  At its
simplest level, this file just has to contain the category you want to put
your mod into.  Once that file's been uploaded to the BLCMods repo, the
ModCabinet wiki should get updated within ten minutes to include your mod.

## Assigning Categories

The current valid categories that you can use in your `cabinet.info` file
are listed on the [[Mod Categories]] page.

If you have only one mod per directory, the `cabinet.info` file can contain
*just* the category name.  So to put your mod into the "gear-general" category,
the file would just contain the single word:

    gear-general

If you have more than one mod in a directory, you'll have to be a little
more wordy.  For instance, if you've got three files which should all be
in the "gear-general" category, you can list them in `cabinet.info` like so:

    BastardV3.txt: gear-general
    CatO'NineTails.txt: gear-general
    DarlinV2.txt: gear-general

## Assigning Multiple Categories

Mods can also be in multiple categories.  For instance, Apocalyptech's BL2
Better Loot mod fits decently in both the "loot-system" and "cheat" categories,
so its `cabinet.info` file looks like this:

    loot-system, cheat

## Update Frequency / Error Reporting

The process which updates the ModCabinet wiki checks for new/changed files
every ten minutes.  You can see when the wiki was last updated by visiting
the [[Wiki Status]] page.  That page will also show you any errors which
happened during the last update.  If you had a typo in one of your category
names, or something, it will show up on that page.

## Screenshots and Nexus Mods Links

To link to external resources like screenshots, or to provide an alternate
download to Nexus Mods, simply add in URLs, one per line, beneath the line which
specifies the categories.  That means that a single-mod directory might have
a `cabinet.info` file which looks like this:

    gear-general
    https://i.imgur.com/ClUttYw.gif

Or a directory which has multiple mods might look like this:

    BastardV3.txt: gear-general
    CatO'NineTails.txt: gear-general
    https://i.imgur.com/W5BHeOB.jpg
    DarlinV2.txt: gear-general

You can also add in text labels for your URLs by prefixing them with some text
and separating them with a pipe (`|`) character:

    BastardV3.txt: gear-general
    CatO'NineTails.txt: gear-general
    A pic of the new weapon in action|https://i.imgur.com/W5BHeOB.jpg
    DarlinV2.txt: gear-general

If a URL ends in `.jpg`, `.gif`, or `.png`, it will be embedded into the
cabinet page.  Youtube URLs will be displayed separately from other URLs.

## Comments

Any line which starts with a `#` will be ignored, as will empty lines, so you
can format your `cabinet.info` files a little more nicely, if you want.
For instance, this would be a valid file:

    BastardV3.txt: gear-general

    # Include a screenshot for this one...
    CatO'NineTails.txt: gear-general
    A pic of the new weapon in action|https://i.imgur.com/W5BHeOB.jpg

    DarlinV2.txt: gear-general

## Mods Whose Filenames Start With A Hash Sign (#)

If, by chance, you have a filename which starts with a hash sign (`#`),
specifying that file in your `cabinet.info` would make it look like a
comment, so the sorter would totally ignore it.  To make it show up
anyway, prefix the hash with a backslash (`\`).  For instance:

    319: gear-smg
    \#Bast mod ever!!!!!!!: gameplay
    Davud: gear-sniper

Though really, it's easier to just name your files sensibly, instead.

## Formatting your README for Maximum Results

ModCabinet will automatically include information from your README files if
it's able to understand how it's laid out.  You'll have best luck if you
format your README files with [Markdown](https://guides.github.com/features/mastering-markdown/)
(so name them `README.md`, for instance), but it will also understand
plain-text README files.

In a directory with only a single mod, make sure that the main part of
your mod description is in a section with a heading of `Description`, or
that it's at the top of the README file (or in the very first section,
if there's nothing right at the beginning).  That will be imported into
the ModCabinet wiki.  If you have a section named `Changelog`, that will
be imported into the ModCabinet page as well.  For an example of a
ModCabinet page which has pulled in all these elements, see Apocalyptech's
[[Speedier Sandskiffs]], which was generated using
[this README](https://raw.githubusercontent.com/BLCM/BLCMods/master/Borderlands%202%20mods/Apocalyptech/Speedier%20Sandskiffs/README.md).

In a directory with multiple mods, ModCabinet needs to have a clearly-marked
section of the README file which has the same name as the mod.  Sections
in the modfile can be marked with any of the usual Markdown-style section
headings such as hashes (`#`) or underlines (`---` or `===`), even if it's
not Markdown.  You can also use Markdown-style list syntax, where the line
containing the mod name is prefixed by a dash (`-`).  For instance, see [this README from
Akathris](https://raw.githubusercontent.com/BLCM/BLCMods/master/Borderlands%202%20mods/Akathris/README.md),
which applies to mods such as [[No More Moxxi Lifesteal v1.0]].  Note that
mods in directories which contain multiple mods won't be able to read in
Changelogs, so those will never show up in ModCabinet pages.

## That's it!

Just check in your `cabinet.info` file the exact same way you'd check in a mod
file, and it'll get picked up the next time it's run.  If you have problems,
feel free to stop by [Shadow's Evil Hideout](http://borderlandsmodding.com/community/)
and ask for help.  (Apocalyptech is the maintainer of this code at the moment,
if you wanted to @ him specifically.)
