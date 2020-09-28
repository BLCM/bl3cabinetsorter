# Borderlands 3 Mods by {{ author.name }}

[(Go directly to {{ author.name }}'s BL3 Mods Github mod directory)]({{ base_url }}/{{ author.rel_url() }})

{% for mod in author.sort_modlist(author.mods) %}
- {{ mod }}
{%- endfor %}

