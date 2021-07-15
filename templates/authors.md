# Authors

{% for author_name, author in authors -%}
- {{ author.wiki_link_html() }}
{% endfor -%}
