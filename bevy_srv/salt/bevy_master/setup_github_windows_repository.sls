---
# salt state file for installing the SaltStack Windows software repository
#    https://docs.saltstack.com/en/latest/topics/windows/windows-package-manager.html
{# TODO: this feature is broken.
#
# salt issue #35993 https://github.com/saltstack/salt/issues/35993
# git cannot read an https: URL using pygit2 on Ubuntu 16.04
{{ salt_config_directory }}/minion.d/98_pygit2_patch.conf:
  file.managed:
    - contents:
    {%- if grains['os'] == 'Ubuntu' and grains['osrelease'] == '16.04' %}
      - '# salt issue #35993 bug in pygit2 on Ubuntu 16.04'
      - 'winrepo_provider: gitpython'
    {% endif -%}
      - 'winrepo_remotes_ng: []'
      - "  - 'https://github.com/vernondcole/salt-winrepo-ng.git'"
{{ salt_config_directory }}/master.d/98_pygit2_patch.conf:
  file.managed:
    - contents:
    {%- if grains['os'] == 'Ubuntu' and grains['osrelease'] == '16.04' %}
      - '# salt issue #35993 bug in pygit2 on Ubuntu 16.04'
      - 'winrepo_provider: gitpython'
    {% endif -%}
      - 'winrepo_remotes_ng:' []

winrepo.update_git_repos:
  salt.runner
 -- end TODO: broken #}

{# genrepo is only needed for Windows minions before Salt version 2015.8 -- do not use
winrepo.genrepo:
  salt.runner:
    - require:
      - winrepo.update_git_repos
-- end old Windows minions #}
