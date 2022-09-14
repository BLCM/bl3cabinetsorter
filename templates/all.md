# Borderlands 3: All Mods

[[Borderlands 3 Mods]]

{% for mod in mods %}
{%- if mod.is_real -%}
- {{ mod.wiki_link_html() }}, by {{ authors[mod.mod_author].wiki_link_html() }}
{% else -%}
- {{ mod.wiki_link_html() }}, by {{ mod.author_text }}
{% endif -%}
{%- endfor %}

