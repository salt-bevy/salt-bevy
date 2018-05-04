---
# salt state file install Tuxboot

{# not yet (11/14/17) supported for Ubuntu 17.10 artsy #}
{# manual install instructions at https://sourceforge.net/p/tuxboot/git/ci/master/tree/ #}
{# on Artsy, download the source and use: #}
{# $ sudo apt install g++-mingw-w64-x86-64  libqt4-dev g++ #}
{# $ sh INSTALL #}
{# $ ./tuxboot #}

install_tuxboot:
  pkgrepo.managed:
    - ppa: thomas.tsai/ubuntu-tuxboot
  pkg.latest:
    - name: logstash
    - refresh: True

...
