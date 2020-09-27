[[← Go Back|Home]]

# Valid Mod Categories

If you're looking for general information about how to get your mods listed
in the ModCabinet, see the [[Contributing to ModCabinet]] page.

The current list of valid categories you can put into your `cabinet.info`
files follows:

| Category Name | Description |
| --- | --- |
{%- for catname, cat in categories.items() %}
| `{{ catname }}` | {{ cat.full_title }}
{%- endfor %}
