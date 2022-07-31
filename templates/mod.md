# {{ mod.mod_title }}

**Author:** {{ authors[mod.mod_author].wiki_link() }}

{%- if mod.other_authors %}

**Other Authors:** {{ mod.get_other_authors_report() }}
{%- endif %}

{%- if mod.contact %}

**Contact:** {{ mod.contact }}
{%- endif %}

{%- if mod.contact_email %}

**Contact (email):** {{ mod.get_wiki_email_contact() }}
{%- endif %}

{%- if mod.contact_discord %}

**Contact (Discord):** {{ mod.contact_discord }}
{%- endif %}

**Last Updated:** {{ mod.mod_time.strftime('%B %d, %Y') }}

{%- if mod.version %}

**Most Recent Version:** {{ mod.version }}
{%- endif %}

{%- if mod.homepage %}

**Homepage:** {{ mod.homepage.url }}
{%- endif %}

**In Categories:** {{ mod.get_cat_links(cats) }}

{%- if mod.license %}
{%- if mod.license_url %}

**License:** <a href="{{ mod.license_url }}">{{ mod.license }}</a>
{%- else %}

**License:** {{ mod.license }}
{%- endif %}
{%- else %}
{%- if mod.license_url %}

**License:** <a href="{{ mod.license_url }}">{{ mod.license_url }}</a>
{%- endif %}
{%- endif %}

{%- if mod.related_links|length > 0 %}

**Other mods with the same name:**
{% for link in mod.related_links_sorted() %}
- {{ link }}
{% endfor %}
{%- endif %}

## Download Methods

<table>
<tr>
<td align="center">
<b><a href="{{ dl_base_url }}{{ mod.rel_url() }}">B3HM-Compatible URL / Download from Github</a></b>
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

{%- if mod.video_urls|length > 0 %}

## Video Videos

{% for vid in mod.video_urls -%}
- {{ vid.wiki_link() }}
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
