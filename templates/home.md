Welcome!

The BL3 ModCabinet wiki exists to provide a slightly-easier way of browsing through
the Borderlands 3 mods hosted on the
[bl3mods Github](https://github.com/BLCM/bl3mods) -- all nicely arranged in
categories rather than just organized by author.  

This wiki is a resource for users who are just looking to run some mods.
For information on actually building your own mods, the [BLCMods
Wiki](https://github.com/BLCM/BLCMods/wiki/Borderlands-3-Modding-Info) is your best
starting point.

# Mod Categories

{%- for cat in categories %}
{%- if cat.prefix and (not loop.previtem or not loop.previtem.prefix or (loop.previtem.prefix != cat.prefix)) %}
- {{ cat.prefix }}
{%- endif %}
{%- if cat.prefix %}
  - {{ cat.wiki_link() }}
{%- else %}
- {{ cat.wiki_link() }}
{%- endif %}
{%- endfor %}

# Other Pages

- [[About BL3 ModCabinet Wiki]]
- [[Contributing to BL3 ModCabinet]]
- [[Searching on the Wiki|Searching]]
