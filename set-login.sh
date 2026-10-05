#!/usr/bin/env bash
# Put wallpapers/login.* on the login screen (SDDM), using a copy of the ready-made
# "Maldives" theme (installed as "qtile-login") with a black clock and a visible mouse cursor.
#
#   ~/qtile/set-login.sh          preview in a window first, then ask before switching
#   ~/qtile/set-login.sh --yes    switch without the preview (used by install.sh)
#
# Undo: sudo rm /etc/sddm.conf.d/10-theme.conf   (back to the plain black screen)
set -euo pipefail

REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
YES=0
[ "${1:-}" = "--yes" ] && YES=1

pic=$(find "$REPO/wallpapers" -maxdepth 1 -iname 'login.*' \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \) | head -n1)
if [ -z "$pic" ]; then
    echo "No login picture found. Copy one to $REPO/wallpapers/login.jpg first." >&2
    exit 1
fi

echo "==> Installing the login themes and cursor (sddm-themes, adwaita-cursor-theme)"
rpm -q sddm-themes adwaita-cursor-theme >/dev/null 2>&1 \
    || sudo dnf install -y --skip-unavailable sddm-themes adwaita-cursor-theme

base=/usr/share/sddm/themes/maldives
if [ ! -d "$base" ]; then
    echo "The Maldives theme didn't install - nothing changed." >&2
    exit 1
fi
# our own copy, so package updates don't undo the changes
theme=qtile-login
dir="/usr/share/sddm/themes/$theme"
sudo rm -rf "$dir"
sudo cp -r "$base" "$dir"
sudo sed -i 's/^Name=.*/Name=Qtile login/; s/^Theme-Id=.*/Theme-Id=qtile-login/' "$dir/metadata.desktop"
# clock (date and time, top-right) in black instead of white
sudo sed -i 's/color: "white"/color: "black"/' "$dir/Main.qml"
ext="${pic##*.}"
dest="/usr/share/backgrounds/qtile-login.${ext,,}"

echo "==> Using theme '$theme' with $(basename "$pic")"
sudo install -D -m 644 "$pic" "$dest"
printf '[General]\nbackground=%s\n' "$dest" | sudo tee "$dir/theme.conf.user" >/dev/null

if [ "$YES" -eq 0 ]; then
    greeter=$(command -v sddm-greeter-qt6 || command -v sddm-greeter || true)
    if [ -n "$greeter" ]; then
        echo
        echo "==> Opening a PREVIEW window of the new login screen."
        echo "    It is only a preview - typing in it does nothing."
        echo "    Look at it, then close the window (Super+Q) to continue."
        "$greeter" --test-mode --theme "$dir" >/dev/null 2>&1 || true
    fi
    echo
    read -r -p "Use this as your login screen? [y/N] " answer
    case "$answer" in
        y|Y|yes|YES) ;;
        *) echo "Not switched. Your login screen is unchanged."; exit 0 ;;
    esac
fi

sudo mkdir -p /etc/sddm.conf.d
cursor=""
[ -d /usr/share/icons/Adwaita/cursors ] && cursor="CursorTheme=Adwaita\nCursorSize=24\n"
printf "[Theme]\nCurrent=%s\n$cursor" "$theme" | sudo tee /etc/sddm.conf.d/10-theme.conf >/dev/null
echo "==> Done. You'll see it the next time the login screen appears (log out, or restart)."
echo "    To undo: sudo rm /etc/sddm.conf.d/10-theme.conf"
