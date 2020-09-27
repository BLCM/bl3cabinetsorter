**Wiki Links**

- [[Main Page|Home]]
- [[Searching]]
- [[About ModCabinet Wiki]]
- [[Contributing to ModCabinet]]
- [[Mod Categories]]
- [[Wiki Status]]

**Borderlands 3 Mods**

{%- for cat in seen_cats %}
{%- if cat.prefix and (not loop.previtem or not loop.previtem.prefix or (loop.previtem.prefix != cat.prefix)) %}
- {{ cat.prefix }}
{%- endif %}
{%- if cat.prefix %}
  - {{ cat.wiki_link() }}
{%- else %}
- {{ cat.wiki_link() }}
{%- endif %}
{%- endfor %}

