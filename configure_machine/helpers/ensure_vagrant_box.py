#!/usr/bin/env python3
"""
Pre-flight check invoked by vgr.bat/vgr before every Vagrant command: if the
target machine needs one of this repo's self-built "salt-bevy/ubuntu-*"
boxes (see packer/README.md) and it isn't registered yet for the provider
that's about to be used, build it now via packer/build_boxes.py instead of
letting "vagrant up" fail with "box could not be found". This is what lets
only DEFAULT_BOX's version need to exist ahead of time -- everything else
gets built the first time it's actually used.

Does nothing (fast no-op) for commands that don't need a box materialized,
for machines that don't use one of our self-built boxes, for a "generic"
machine given an explicit NODE_BOX, or when the needed box is already
registered for the provider in play.

Usage: ensure_vagrant_box.py <the same arguments vgr/vgr.bat was called with>
"""
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent  # helpers/ -> configure_machine/ -> repo root
BUILD_BOXES = REPO_ROOT / "packer" / "build_boxes.py"

# Keep this in sync with the Vagrantfile: which machine uses which self-built
# Ubuntu version. "" is the bare "vgr up" / "vgr up generic ..." case (the
# primary machine, and generic's fallback when NODE_BOX isn't set) -- both
# use DEFAULT_BOX.
SELF_BUILT_MACHINE_VERSIONS = {
    "": "26.04",
    "quail1": "26.04",
    "quail2": "26.04",
    "bevymaster": "26.04",
    "quail24": "24.04",
}

COMMANDS_THAT_NEED_THE_BOX = {"up", "reload", "provision"}

BOX_LIST_LINE_RE = re.compile(r'^(\S+)\s+\((\w+),')


def registered_boxes_for(provider):
    """:return: set of box names registered for `provider`, or None if the lookup itself failed."""
    try:
        result = subprocess.run(["vagrant", "box", "list"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    found = set()
    for line in result.stdout.splitlines():
        m = BOX_LIST_LINE_RE.match(line.strip())
        if m and m.group(2) == provider:
            found.add(m.group(1))
    return found


def main(argv):
    if not argv:
        return
    command = argv[0]
    if command not in COMMANDS_THAT_NEED_THE_BOX:
        return

    if len(argv) > 1 and argv[1] == "generic":
        if os.environ.get("NODE_BOX"):
            return  # an explicit box was given -- not one of ours, let Vagrant handle it
        version = SELF_BUILT_MACHINE_VERSIONS[""]
    else:
        machine = argv[1] if len(argv) > 1 else ""
        if machine not in SELF_BUILT_MACHINE_VERSIONS:
            return
        version = SELF_BUILT_MACHINE_VERSIONS[machine]

    # Mirrors vgr.bat's own rule ("up" defaults to hyperv unless overridden) so this
    # check targets the same provider Vagrant is about to use.
    provider = os.environ.get("VAGRANT_DEFAULT_PROVIDER") or ("hyperv" if command == "up" else None)
    if not provider:
        return  # can't tell which provider will actually be used -- skip the check

    box_name = "salt-bevy/ubuntu-{}".format(version)
    registered = registered_boxes_for(provider)
    if registered is None or box_name in registered:
        return  # already have it, or couldn't check -- don't block the real command over it

    print('\n(box "{}" isn\'t built yet for {} -- building it now via packer/build_boxes.py...)\n'.format(
        box_name, provider))
    subprocess.run([sys.executable, str(BUILD_BOXES), "--versions", version, "--providers", provider])


if __name__ == "__main__":
    main(sys.argv[1:])
