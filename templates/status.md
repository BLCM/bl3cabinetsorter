[[← Go Back|Home]]

# Generation Time

The content of this wiki should be auto-updated within ten minutes of
files being updated at the BLCMods Github.  The last update time for
this site was: **{{ gen_time.strftime('%B %d, %Y %I:%M %p %z (%Z)') }}**

If you've updated your mod within the last ten minutes and the wiki
has not updated yet, be patient and it should show up.  If it's been
more than twenty minutes or so, doublecheck that your mod shows up
properly at [the main BLCMods Github](https://github.com/BLCM/BLCMods),
and ask for help at [Shadow's Evil Hideout](http://borderlandsmodding.com/community/)
in the `#bl-modding` channel.

# Errors

{% if errors|length > 0 %}
{%- for error in errors %}
- {{ error }}
{%- endfor %}
{% else %}
No errors were encountered while generating the wiki.
{% endif %}
