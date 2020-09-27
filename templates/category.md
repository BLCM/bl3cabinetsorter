# Borderlands 3: {{ cat.full_title }}

[[Borderlands 3 Mods]]

{% for mod in mods %}
- {{ mod.wiki_link_html() }}, by {{ authors[mod.mod_author].wiki_link_html() }}
{%- endfor %}

