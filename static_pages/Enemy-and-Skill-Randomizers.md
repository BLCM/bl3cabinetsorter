# BL3 Randomizer

Inside the ModCabinet, you can find different [[gear randomizers|General Gameplay and Balance: Randomizers]]
to play with (these are split up by item slot type: [[Weapons|Gear Randomizer: Weapons]],
[[Shields|Gear Randomizer: Shields]], [[Grenades|Gear Randomizer: Grenades]],
[[Artifacts|Gear Randomizer: Artifacts]], and [[Class Mods|Gear Randomizer: Class Mods]]).
If you are looking for the Enemy and Skill Randomizer mods then those are not
stored on BLCM directly but rather generated from programs (both initially and
whenever a different outcome is wanted). You can find the GitHub Repos to those
two programs below. If using the one from SSpyR note that the full GUI window
will take a bit to load up, this is normal. The program exe from SSpyR can also
be found in BLCM alongside where the Gear Randomizer files are (in the actual
Repository Directory itself under SSpyR's folder).

## See Links to Said Repos

- https://github.com/SSpyR/RandomizerPackage
- https://github.com/HackerSmacker/BL3GenRandomizer

## Reasoning for a Re-Gen Randomizer Program

Currently the way the Enemy and Skill Randomizers are made they are set
"Randomizations" that don't automatically adjust to new "Randomizations" upon a
Save/Quit, they are more static (if you would like to learn more why that is
you can ask further in the community Discords, for sake of keeping things brief).
Changing how these Randomizers work is something being looked into but with the
current way it works we have created programs (one in C that may possibly also
turn into a plugin, and one in Python) to allow users to re-generate the Hotfix
files themselves in case they want to change the experience or fix a softlock.

## Usage of Python Re-Gen Program Found Within BLCM

When the program is downloaded (either from BLCM or from the Releases of the
separate Repository) it will be downloaded as a .EXE program (sorry non-Windows
users). How using this program works is whereever you place it (doesn't matter)
launch it by double-clicking (or right click open) and it will launch with a
black Console Debug Window and after a bit of waiting will load a small GUI
window with two buttons on it (as said above, the wait each time is normal).
Whenever you click one of these buttons it will begin re-generating (or
generating for the first time) the Hotfix file for the one you selected (either
Skill and Enemy/Spawn Randomizer) and once the file is completed being
generated the program will create a pop-up window noting such. These files will
be made in the same directory as the program used to create them and if the
file being generated already exists in said directory it will overwrite it with
the new file. Once the file(s) are generated they are ready to use in B3HM via
the Local Path option!

## Reloading after a Re-Gen

Just a quick note and tip that you can re-gen your files while still in game,
simply run the program and generate the files as explained above and as long as
you didn't change where the program is located from the last time you ran it
then it will overwrite the files that were loaded into B3HM via the Local Path
option. Thus all you need to do is simply Quit to Title Screen to reload your
Hotfixes and then you are all set.

## Further Questions and Support

If you still require help or have anything further questions or reports
regarding any of the information or mods stated please reach out on Discord to
SSpyR inside of [the community Discords](http://borderlandsmodding.com/community/).

