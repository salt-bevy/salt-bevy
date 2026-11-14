#!/usr/bin/env python3
"""
Build self-hosted Ubuntu Vagrant boxes for salt-bevy, using the chef/bento
Packer templates (the same project that built most of the boxes historically
found on Vagrant Cloud) -- see packer/README.md for why.

By default this builds every requested Ubuntu version for every hypervisor
provider actually installed on this machine (auto-detected), so a
Vagrantfile using "salt-bevy/ubuntu-26.04" works regardless of which
provider the user picks with "vagrant up --provider=...".

Usage:
  python build_boxes.py                              # detected providers, 24.04 + 26.04
  python build_boxes.py --versions 26.04
  python build_boxes.py --providers hyperv virtualbox
  python build_boxes.py --switch "My Hyper-V Switch"  # only relevant for --providers hyperv
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

BENTO_COMMIT = "c884c077e041f54f56e4e07baddd916c49d31a0e"
BENTO_REPO = "https://github.com/chef/bento.git"
PACKER_DIR = Path(__file__).resolve().parent
BENTO_DIR = PACKER_DIR / ".bento"
# Finished .box files are moved here (git-ignored) out of bento's own build tree,
# so they are easy to find, copy or delete, and survive deleting .bento/ to move
# to a newer bento commit.
BOXES_DIR = PACKER_DIR.parent / "boxes"
UBUNTU_PKRVARS_DIR = BENTO_DIR / "os_pkrvars" / "ubuntu"
# bento names its var files and boxes by guest architecture; build to match the host
# (e.g. Apple Silicon Macs can only run arm64 guests under VirtualBox).
ARCH = "aarch64" if platform.machine().lower() in ("arm64", "aarch64") else "x86_64"
PACKER_TEMPLATES = "../../packer_templates"  # relative to UBUNTU_PKRVARS_DIR, matches bento's own Rakefile

# Packer source name -> Vagrant provider tag used in the output filename ("{{.Provider}}")
PROVIDER_SOURCES = {
    "hyperv": "source.hyperv-iso.vm",
    "virtualbox": "source.virtualbox-iso.vm",
    "vmware": "source.vmware-iso.vm",
}


def packer_exe():
    exe = shutil.which("packer")
    if not exe:
        sys.exit('ERROR: "packer" was not found on PATH. Install it from '
                 'https://developer.hashicorp.com/packer/install')
    return exe


def vmware_installed():
    if shutil.which("vmrun"):
        return True
    return os.path.exists(r"C:\Program Files (x86)\VMware\VMware Workstation\vmrun.exe")


def hyperv_installed():
    if os.name != 'nt':
        return False
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "(Get-Service vmms -ErrorAction SilentlyContinue) -ne $null"],
            capture_output=True, text=True, timeout=15)
        return result.stdout.strip().lower() == 'true'
    except (OSError, subprocess.SubprocessError):
        return False


def detect_providers():
    found = []
    if shutil.which("VBoxManage"):
        found.append("virtualbox")
    if vmware_installed():
        found.append("vmware")
    if hyperv_installed():
        found.append("hyperv")
    return found


def ensure_bento():
    if not BENTO_DIR.exists():
        print('Cloning chef/bento (pinned commit {})...'.format(BENTO_COMMIT))
        subprocess.run(["git", "init", "-q", str(BENTO_DIR)], check=True)
        subprocess.run(["git", "-C", str(BENTO_DIR), "remote", "add", "origin", BENTO_REPO], check=True)
        subprocess.run(["git", "-C", str(BENTO_DIR), "fetch", "-q", "--depth", "1", "origin", BENTO_COMMIT], check=True)
        subprocess.run(["git", "-C", str(BENTO_DIR), "checkout", "-q", "FETCH_HEAD"], check=True)
    # Every time, not just after cloning: plugins install per user (~/.config/packer),
    # so an existing checkout on a new machine or account still needs them. Quick no-op
    # once they're present.
    subprocess.run([packer_exe(), "init", PACKER_TEMPLATES], cwd=str(UBUNTU_PKRVARS_DIR), check=True)


def build_one(version, provider, switch_name, keep_on_error=False):
    var_file = UBUNTU_PKRVARS_DIR / "ubuntu-{}-{}.pkrvars.hcl".format(version, ARCH)
    if not var_file.exists():
        print('  (skipping Ubuntu {}: bento has no "{}" -- check the version number)'.format(
            version, var_file.name))
        return False

    args = [
        packer_exe(), "build",
        "-var-file={}".format(var_file.name),
        '-var=sources_enabled=["{}"]'.format(PROVIDER_SOURCES[provider]),
    ]
    if keep_on_error:
        # Leave the failed VM in place (Packer stops without cleaning up), so its
        # console and network adapter can be inspected. Remove it by hand afterwards.
        args.append("-on-error=abort")
    if provider == "virtualbox" and ARCH == "aarch64":
        # See the comment in that file: removes the x86 IDE controller under its real name.
        args.append("-var-file={}".format((PACKER_DIR / "virtualbox-aarch64.pkrvars.hcl").as_posix()))
    if provider == "hyperv":
        args.append("-var=hyperv_switch_name={}".format(switch_name))
        # Our own autoinstall files (packer/http/), which install hv-kvp-daemon into the
        # installed system. Without it Packer never learns the VM's IP on Hyper-V and
        # times out waiting for SSH. See packer/http/ubuntu/user-data.
        args.append("-var=http_directory={}".format((PACKER_DIR / "http").as_posix()))
    args.append(PACKER_TEMPLATES)

    print('\n=== Building Ubuntu {} for {} '
          '(downloads the install ISO and runs an unattended install -- expect 20-40 minutes) ==='.format(
              version, provider))
    # Full Packer debug log per build, kept next to the boxes: it shows whether the
    # installer fetched its autoinstall file, and what Packer waited on.
    BOXES_DIR.mkdir(exist_ok=True)
    log_path = BOXES_DIR / "packer-ubuntu-{}-{}.log".format(version, provider)
    env = dict(os.environ, PACKER_LOG="1", PACKER_LOG_PATH=str(log_path))
    print("(Packer debug log: {})".format(log_path))
    result = subprocess.run(args, cwd=str(UBUNTU_PKRVARS_DIR), env=env)
    if result.returncode != 0:
        print('Build FAILED for Ubuntu {} / {}.'.format(version, provider))
        return False

    box_file = BENTO_DIR / "builds" / "build_complete" / "ubuntu-{}-{}.{}.box".format(version, ARCH, provider)
    if not box_file.exists():
        print('ERROR: build reported success but the expected box file is missing: {}'.format(box_file))
        return False

    BOXES_DIR.mkdir(exist_ok=True)
    kept = BOXES_DIR / box_file.name
    shutil.move(str(box_file), str(kept))
    box_file = kept
    box_name = "salt-bevy/ubuntu-{}".format(version)
    print('Registering "{}" as {} ({})...'.format(box_file, box_name, provider))
    subprocess.run(["vagrant", "box", "add", str(box_file), "--name", box_name,
                     "--provider", provider, "--force"], check=True)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--versions", nargs="+", default=["24.04", "26.04"],
                         help="Ubuntu versions to build (default: 24.04 26.04)")
    parser.add_argument("--providers", nargs="+", choices=sorted(PROVIDER_SOURCES),
                         help="default: auto-detect installed hypervisors")
    parser.add_argument("--switch", default=os.environ.get("HYPERV_SWITCH", "Default Switch"),
                         help='Hyper-V virtual switch to bridge to (default: "Default Switch"); '
                              'ignored unless building for --providers hyperv')
    parser.add_argument("--keep-on-error", action="store_true",
                         help="on a failed build, leave the VM in place for inspection "
                              "(packer -on-error=abort); delete it by hand afterwards")
    args = parser.parse_args()

    providers = args.providers or detect_providers()
    if not providers:
        sys.exit("ERROR: no supported hypervisor providers were detected on this machine "
                  "(checked for VirtualBox, VMware Workstation, Hyper-V). Pass --providers explicitly.")
    print('Building for providers: {}'.format(', '.join(providers)))

    if "hyperv" in providers and os.name == 'nt':
        # noinspection PyUnresolvedReferences
        from windows_sudo import sudo
        if not sudo.isUserAdmin():
            print('Hyper-V VM creation requires elevation -- requesting it now...')
            sys.exit(sudo.runAsAdmin([os.path.abspath(__file__)] + sys.argv[1:], python_shell=True) or 0)

    ensure_bento()

    failures = []
    for version in args.versions:
        for provider in providers:
            if not build_one(version, provider, args.switch, args.keep_on_error):
                failures.append((version, provider))

    if failures:
        print('\nFAILED: {}'.format(failures))
        sys.exit(1)
    print('\nDone. Registered boxes are visible via "vagrant box list".')


if __name__ == "__main__":
    main()
