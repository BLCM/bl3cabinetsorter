**Wiki Links**

- [[Main Page|Home]]
- [[Searching]]
- [[About ModCabinet Wiki]]
- [[Contributing to ModCabinet]]
- [[Mod Categories]]
- [[Wiki Status]]

{%- for game in games %}

**{{ game.title }} Mods**

{%- for cat in seen_cats[game.abbreviation] %}
{%- if cat.prefix and (not loop.previtem or not loop.previtem.prefix or (loop.previtem.prefix != cat.prefix)) %}
- {{ cat.prefix }}
{%- endif %}
{%- if cat.prefix %}
  - {{ cat.wiki_link(game) }}
{%- else %}
- {{ cat.wiki_link(game) }}
{%- endif %}
{%- endfor %}

{% endfor %}

