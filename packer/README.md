# Self-built Ubuntu boxes

HashiCorp is retiring HCP Vagrant (the successor to Vagrant Cloud): new box
creation stops 2026-10-01, and existing box downloads are decommissioned
sometime between 2026-12-31 and 2027-03-15 (see
[the deprecation notice](https://developer.hashicorp.com/hcp/docs/vagrant/hcp-vagrant-eol)).
Rather than depend on a third-party catalog for the plain-Ubuntu-Server
machines in this repo's `Vagrantfile` (`bevymaster`, `quail1`, `quail2`,
`quail22`/`salt22`, `quail24`, and `generic`), this directory builds them
locally, for whichever hypervisor(s) you actually have installed.

## How it works

[chef/bento](https://github.com/chef/bento) is the actively-maintained,
open-source Packer template project that historically built most of the
`bento/*` and `hashicorp/*` boxes on Vagrant Cloud, and already ships
ready-made variable files for Ubuntu 24.04 and 26.04. `build_boxes.py`
shallow-clones it at a pinned commit into `.bento/` (git-ignored, not
committed here), auto-detects which of VirtualBox / VMware Workstation /
Hyper-V are actually installed on this machine, and for each (version,
provider) pair runs bento's Packer template and registers the resulting
`.box` file with Vagrant under the name `salt-bevy/ubuntu-<version>` --
using `--provider` explicitly, so the *same* box name works correctly no
matter which provider `vagrant up` ends up using.

Hyper-V is not in bento's default provider list (it targets
VirtualBox/VMware/Parallels/QEMU/UTM out of the box), so `build_boxes.py`
passes `-var sources_enabled=[...]` to select exactly the one provider it's
building for on each run, plus `-var hyperv_switch_name=...` (matching this
repo's `HYPERV_SWITCH` / `Default Switch` default) when building for
Hyper-V. Building for Hyper-V also requires Administrator privileges (a
Hyper-V limitation, not this script's) -- `build_boxes.py` uses the
`windows-sudo` package (already a dependency of this project) to
self-elevate only when needed.

## Usage

Prerequisites: `git`, [Packer](https://developer.hashicorp.com/packer/install),
`vagrant`, and at least one of VirtualBox / VMware Workstation / Hyper-V.

You normally don't need to run this by hand: `vgr`/`vgr.bat` calls
`../configure_machine/helpers/ensure_vagrant_box.py` before every command,
which builds a missing self-built box on demand (only `DEFAULT_BOX`'s
version needs to exist ahead of time -- e.g. `quail24`'s box gets built the
first time you actually `vgr up quail24`). Run it directly if you want to
pre-build, target a specific version/provider, or refresh an existing box:

```cmd
cd packer
python build_boxes.py                        REM detected providers, Ubuntu 24.04 + 26.04
python build_boxes.py --versions 26.04
python build_boxes.py --providers hyperv virtualbox
```

Each (version, provider) build downloads the official Ubuntu Server ISO
(~3GB) and runs an unattended install; expect 20-40 minutes per
combination. Re-run whenever you want a refreshed box -- it always
overwrites the previous `salt-bevy/ubuntu-<version>` registration for that
provider.

## Why not the other boxes too?

The Windows and macOS machines in the Vagrantfile (`win7`, `win10`, `win12`,
`win16`, `win19`, `mac13`) are a different problem: they're 5-15GB each
(too large to casually rebuild on every clone), and macOS boxes can't be
legally redistributed off Apple hardware regardless of where they're hosted.
Those are being tracked separately.
