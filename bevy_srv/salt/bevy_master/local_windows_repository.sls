---
# Salt state for using a local source for Windows software definitions
# - - - this state is to run on the Salt Master or a masterless minion
#
{# -- NOTE -- don't render the templates here. The jinja template is expanded on the minion only. #}

{% if grains['os'] == 'Windows' %}
  {%  set cs = 'c:/srv/salt' %}
{%  elif grains['os'] == 'MacOS'  %}
  {%  set cs = '/opt/saltdata/salt' %}
{%  else  %}
  {%  set cs = '/srv/salt' %}
{% endif %}

{{ cs }}/win/repo-ng:
  file.directory:
    - makedirs: true

{# -- NOTE -- no jinja is used here. The jinja template is expanded on the minion only. #}
# Sample: use a local definition to find Notepad++
{{ cs }}/win/repo-ng/npp.sls:
  file.managed:
    - source: salt://{{ slspath }}/files/windows/npp.sls.source

{{ cs }}/win/repo-ng/git.sls:
  file.managed:
    - source: salt://{{ slspath }}/files/windows/git.sls.source

{{ cs }}/win/repo-ng/VCforPython27.sls:
  file.managed:
    - source: salt://{{ slspath }}/files/windows/VCforPython27.sls.source
...
