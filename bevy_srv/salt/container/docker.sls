---
# salt state file for installing docker

{% if grains['os_family'] == 'Windows' %}

include:
  - windows.install_chocolatey

windows_docker:
  chocolatey.installed:
    - name: docker-desktop
    - require:
      - sls: windows.install_chocolatey

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
    - humanname: mono-project
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
