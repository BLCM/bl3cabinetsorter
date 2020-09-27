# {{ mod.mod_title }}

**Author:** {{ authors[mod.mod_author].wiki_link() }}

**Last Updated:** {{ mod.mod_time.strftime('%B %d, %Y') }}

**In Categories:** {{ mod.get_cat_links(cats) }}

{%- if mod.related_links|length > 0 %}

**Other mods with the same name:**
{% for link in mod.related_links %}
- {{ link }}
{% endfor %}
{%- endif %}

## Download Methods

<table>
<tr>
<td align="center">
<b><a href="{{ dl_base_url }}{{ mod.rel_url() }}">Download from Github</a></b>
<br/>
<em>(right click and "Save Link As")</em>
</td>
</tr>
</table>

<table>
<tr>
<td align="center">
<b><a href="{{ base_url }}{{ mod.rel_url_dir() }}">View on Github</a></b>
<br/>
<em>(after clicking on a mod, right click on "Raw" or<br/>"Download," and then "Save Link As")</em>
</td>
</tr>
</table>

{%- if mod.nexus_link %}

[Download from Nexus]({{ mod.nexus_link.url }}) |
----|
{%- endif %}

{#- -------------------- README -------------------- #}

{%- if mod.readme_desc|length > 0 or mod.readme_rel %}

## README

{{ mod.get_readme_embed() }}

[View whole README on Github]({{ base_url }}{{ mod.rel_readme_url() }})
{%- endif %}

{#- -------------------- In-Mod Description -------------------- #}

{%- if mod.mod_desc|length > 0 %}

## Description (from inside mod)

{{ mod.get_mod_desc_embed() }}
{% endif %}

{#- -------------------- Youtube Links -------------------- #}

{%- if mod.youtube_urls|length > 0 %}

## Youtube Videos

{% for yt in mod.youtube_urls -%}
- {{ yt.wiki_link() }}
{% endfor %}
{%- endif %}

{#- -------------------- Embedded Screenshots -------------------- #}

{%- if mod.screenshots|length > 0 %}

## Screenshots

{% for ss in mod.screenshots -%}
{%- if ss.text %}
{{ ss.text }}:
{%- endif %}
{{ ss.screenshot_embed() }}

{% endfor %}
{%- endif %}

{#- -------------------- Other URLs -------------------- #}

{%- if mod.urls|length > 0 %}

## Other URLs

{% for url in mod.urls -%}
- {{ url.wiki_link() }}
{% endfor %}
{%- endif %}

{#- -------------------- Changelog -------------------- #}

{%- if mod.changelog|length > 0 %}

## Changelog

{{ mod.changelog|join("\n") }}
{% endif %}
