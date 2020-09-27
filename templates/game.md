# Borderlands 3 Mods

[[← Go Back|Home]]

Categories:
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
