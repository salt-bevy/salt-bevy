---
# Salt state for installing go https://golang.org/doc/install
#
{% set go_vers = salt['pillar.get']('golang_version', '1.13.7') %} {# TODO: update this default regularly #}

{% if grains['os'] == 'Windows' %}
include:
  - windows.install_chocolatey

golang:
  chocolatey.upgraded:
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
  archive.extracted:
    - source: https://dl.google.com/go/go{{ go_vers }}.linux-amd64.tar.gz
    - skip_verify: True
    - name: /usr/local
    - unless: go version

go_command:
  file.symlink:
    - name: /usr/local/bin/go
    - target: /usr/local/go/bin/go
    - mode: 0755
    - require:
      - golang_linux

gofmt_command:
  file.symlink:
    - name: /usr/local/bin/gofmt
    - target: /usr/local/go/bin/gofmt
    - mode: 0755
    - require:
      - golang_linux

{% endif %}
...
