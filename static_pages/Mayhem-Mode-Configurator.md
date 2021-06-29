# Mayhem Mode Configurator

The Borderlands 3 Mayhem Mode Configurator isn't a mod *itself*, but rather
a web app which is used to *generate* hotfix mods.  It lets you alter which
Mayhem Modifier pools are used in which mayhem levels, all the various
scaling values are in those levels, and which mayhem modifiers are active
in each of the pools.

The scaling values in particular that it lets you edit are:

- Enemy Scaling (does Health/Shields/Armor all at once)
- XP Scaling
- Cash/Eridium Scaling
- Loot Scaling
- Pet/Companion Health
- Drop Weight Scaling
- Damage Scaling
- Drop Number Scaling *(honestly not sure what exactly this controls)*
- Eridium Drop Chance Scaling

# Where To Find It

The BL3 Mayhem Mode Configurator lives at: https://apocalyptech.com/games/bl3-mayhem/

Sourcecode for the configurator (should you wish to host it yourself, elsewhere)
is available at: https://github.com/apocalyptech/bl3mayhem

# Licenses

The main code for the Configurator is licensed under the
[New/Modified (3-Clause) BSD License](https://opensource.org/licenses/BSD-3-Clause).

The project also makes use of, and includes a partial PHP port of
[pieroxy's lz-string project](https://pieroxy.net/blog/pages/lz-string/index.html),
which is licensed under the [MIT License](https://opensource.org/licenses/MIT).

The mods which this app generates are licensed under
[CC0 1.0 (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/),
so feel free to do whatever you like with those.
