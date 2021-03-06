---
# salt state file for installing docker

{% if grains['os_family'] == 'Windows' %}

windows_docker:
  test.fail_without_changes:
    - name: 'Aborting install. Docker-desktop installation on Windows will disable VirtualBox, which is needed for salt-bevy.'
    - failhard: True
    - order: 1

{% elif grains['os_family'] == 'MacOS' %}

include:
  - macos.install_homebrew

MacOS_docker:
  pkg.installed:
    - name: docker
    - require:
        - sls: macos.install_homebrew

{% else %}  {# must be Linux #}

  {% if grains['os_family'] == 'Debian' %}

docker_apt:
  pkgrepo.managed:
    - humanname: docker-repo
    - name: "deb https://download.docker.com/linux/ubuntu {{ grains['oscodename'] }} stable"
    - architectures: amd64
    - key_url: https://download.docker.com/linux/ubuntu/gpg

docker_packages:
  pkg.installed:
    - pkgs:
      - apt-transport-https
      - ca-certificates
      - curl
      - gnupg-agent
      - software-properties-common
      - docker-ce
      - docker-ce-cli
      - containerd.io
  {% endif %}

{% set my_user = salt['config.get']('my_linux_user', salt['cmd.run']("python -c \"import os; print(os.getenv(\'SUDO_USER\', 'vagrant'))\"")) %}

docker_group:
  group.present:
    - name: docker
    - addusers:
      - {{ my_user }}
{% endif %}
...
