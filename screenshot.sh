#!/bin/sh
# Screenshots: ./screenshot.sh full | area
# Saves to ~/Pictures/Screenshots, copies to the clipboard, shows a notification.
# Needs grim, slurp (for area) and wl-clipboard.
dir="$HOME/Pictures/Screenshots"
mkdir -p "$dir"
file="$dir/$(date +%Y-%m-%d_%H-%M-%S).png"

case "$1" in
    area)
        geom=$(slurp -b 1a1f1c88 -c 7fa38a -w 2) || exit 0   # Esc cancels
        grim -g "$geom" "$file" ;;
    *)
        grim "$file" ;;
esac || { notify-send -a screenshot "Screenshot failed"; exit 1; }

wl-copy --type image/png < "$file"
notify-send -a screenshot -i "$file" "Screenshot saved" "$(basename "$file") - also copied to clipboard"
