# {{ game.title }}: {{ cat.full_title }}

{{ game.wiki_link_back() }}

{% for mod in mods %}
- {{ mod.wiki_link_html() }}, by {{ authors[mod.mod_author].wiki_link_html() }}
{%- endfor %}

