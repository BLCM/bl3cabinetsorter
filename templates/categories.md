[[← Go Back|Home]]

# Valid Mod Categories

If you're looking for general information about how to get your mods listed
in the ModCabinet, see the [[Contributing to BL3 ModCabinet]] page.

The current list of valid categories you can put into your mod headers follows:

| Category Name | Description |
| --- | --- |
{%- for catname, cat in categories.items() %}
| `{{ catname }}` | {{ cat.full_title }}
{%- endfor %}

If you're doing a translation for a language which doesn't have a specific
category here yet, please contact Apocalyptech to get it added in.
