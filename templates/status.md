[[← Go Back|Home]]

# Generation Time

The content of this wiki should be auto-updated within ten minutes of
files being updated at the bl3mods Github.  The last update time for
this site was: **{{ gen_time.strftime('%B %d, %Y %I:%M %p %z (%Z)') }}**

If you've updated your mod within the last ten minutes and the wiki
has not updated yet, be patient and it should show up.  If it's been
more than twenty minutes or so, doublecheck that your mod shows up
properly at [the main bl3mods Github](https://github.com/BLCM/bl3mods),
and ask for help at [the community Discords](http://borderlandsmodding.com/community/).

# Errors

{% if errors|length > 0 %}
{%- for error in errors %}
- {{ error }}
{%- endfor %}
{% else %}
No errors were encountered while generating the wiki.
{% endif %}
