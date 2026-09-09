#!/usr/bin/env bash
# Installs a global "vgr" command, so that Vagrant commands can control this salt-bevy
# checkout's VMs from any directory -- not just from a sibling "projects" folder.
#
# Unlike a plain copy of "vgr", the installed copy has this checkout's real, absolute
# path baked in, so it keeps working correctly even when installed somewhere else on
# PATH (e.g. ~/.local/bin) via a symlink -- which a plain copy does not: "vgr"
# resolves its target repo relative to "$0", and a symlink's "$0" is the symlink's own
# location, not the real file's, so a naive copy/symlink of the unmodified script
# would look for the repo in the wrong place entirely.
set -euo pipefail

# Resolve the real directory this script lives in, following symlinks -- the standard
# portable pattern (works on both GNU and BSD/macOS, unlike "readlink -f").
resolve_script_dir() {
    local source="$1" dir
    while [ -h "$source" ]; do
        dir="$(cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd)"
        source="$(readlink "$source")"
        case "$source" in
            /*) ;;
            *) source="$dir/$source" ;;
        esac
    done
    cd -P "$(dirname "$source")" >/dev/null 2>&1 && pwd
}

REPO_ROOT="$(resolve_script_dir "$0")"
VGR_TEMPLATE="$REPO_ROOT/vgr"
OLD_LINE='SCRIPTPATH="$( cd "$(dirname "$0")/../salt-bevy" ; pwd -P )"'
INSTALL_DIR="${1:-$HOME/.local/bin}"

if ! grep -qF "$OLD_LINE" "$VGR_TEMPLATE"; then
    echo "ERROR: \"$VGR_TEMPLATE\" has changed -- expected to find:" >&2
    echo "  $OLD_LINE" >&2
    exit 1
fi

mkdir -p "$INSTALL_DIR"
NEW_LINE="SCRIPTPATH=\"$REPO_ROOT\""
awk -v old="$OLD_LINE" -v new="$NEW_LINE" '$0 == old { print new; next } { print }' \
    "$VGR_TEMPLATE" > "$INSTALL_DIR/vgr"
chmod +x "$INSTALL_DIR/vgr"

echo "Installed \"vgr\" into \"$INSTALL_DIR\""
echo "It points at this checkout: \"$REPO_ROOT\""
echo
case ":$PATH:" in
    *":$INSTALL_DIR:"*)
        echo 'Type "vgr status" to try it from any directory.'
        ;;
    *)
        echo "NOTE: \"$INSTALL_DIR\" isn't on your PATH yet -- add it in your shell's"
        echo "startup file (e.g. ~/.bashrc or ~/.zshrc), then open a new shell and"
        echo 'type "vgr status" to try it from any directory.'
        ;;
esac
echo '(Re-run this installer if you move or re-clone this checkout.)'
