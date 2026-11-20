# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
It describes the repo as it is now. This is a **public** repository: keep private hostnames,
addresses and credentials out of it. Operational notes go in the notes file imported at the end.

## What it is

salt-bevy builds a "bevy": a group of machines (Vagrant VMs on VirtualBox, Hyper-V or VMware, plus
real computers) run by its own Salt master, `bevymaster`, as a sandbox for learning Salt and for
running small real networks. Lessons are in the sibling repo `salt-bevy/training`. `README.md` is
the user-facing introduction.

## Layout

- `Vagrantfile` — defines every VM (bevymaster and the example minions) and picks the provider; box
  names, memory, MAC addresses (`bevy_mac`) and networking per provider. Each `:salt` provisioner
  pins the minion id with `-i <name>` (Salt caches the id it derives at first bootstrap for good).
- `join-bevy.sh` / `join-bevy.bat` and `configure_machine/` — interactive setup of a workstation or
  bevy member: writes the bevy's settings (`bevy_srv/pillar` plus local settings files), installs
  Salt, joins the master. The bevy named `local` means masterless.
- `bevy_srv/salt/` — the Salt state tree the master serves (`top.sls`, `bevy_master/`,
  `common.sls`, `interactive_user.sls`, `windows/`, `macos/`, …); `bevy_srv/pillar/` — its pillar.
- `packer/build_boxes.py` — builds local Vagrant boxes with Packer (bento templates), per provider.
- `vgr` / `vgr.bat` — wrapper around `vagrant` that sets the bevy's environment.
- Windows helpers: `windows_bootstrap_salt.ps1`, `windows_install_python.ps1`, `install_*.bat`.

## Working in this repo

- Changes go through pull requests on GitHub (`gh pr create`), from a topic branch; `master` is the
  default branch.
- No automated tests: check a change by bringing the affected VM up (`vagrant up <name>`, or
  `--provision` for one that already exists — Vagrant runs non-`always` provisioners only when a
  machine is first created) and running a highstate on the master.
- Python: `python3` on Linux and macOS, `py` on Windows.
- Keep the lessons in `salt-bevy/training` in step when behaviour they describe changes.

## Notes

The operator's own setup (which machines run the bevy, its master VM, provider quirks met, open
work) is in a private notes file in their Nextcloud, imported here. It isn't part of the public repo.

@~/Nextcloud/claude-notes/salt-bevy/NOTES.md
