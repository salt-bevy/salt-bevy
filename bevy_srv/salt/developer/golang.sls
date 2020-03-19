---
# Salt state for installing go https://golang.org/doc/install
#
# NOTE: the GO version here is used only for selecting a version to initially load, and only applies to Linux.
#  This script does not check GO versions. If GO is installed at all (any version) no action is taken.
  {# TODO: make version support actually work #}
{% set go_vers = salt['pillar.get']('golang_version', '1.14') %} {# TODO: update this default regularly #}
                                            {# see https://golang.org/dl/ for the recent version number #}

{% if grains['os'] == 'Windows' %}
include:
  - windows.install_chocolatey

golang:
  chocolatey.installed:
    - require:
      - install_chocolatey

{% elif grains['os'] == 'MacOS' %}

include:
  - macos.install_homebrew

golang_mac:
  pkg.installed:
    - name: golang

{% else %}

golang_linux:
  archive.extracted:  {# I could not find a way to install a contemporary Lunux GO that does not use a version number #}
    - source: https://dl.google.com/go/go{{ go_vers }}.linux-amd64.tar.gz
    - skip_verify: True
    - name: /usr/local
    - unless: go version  {# version number not actually checked #}

go_command:
  file.symlink:
    - name: /usr/local/bin/go
    - target: /usr/local/go/bin/go
    - mode: 0755
    - onchanges:
      - golang_linux

gofmt_command:
  file.symlink:
    - name: /usr/local/bin/gofmt
    - target: /usr/local/go/bin/gofmt
    - mode: 0755
    - onchanges:
      - golang_linux

{% endif %}
...
