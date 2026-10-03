#!/bin/sh
# Power menu: click-only list (no search box). Nothing happens until one is picked.
pkill -x wofi && exit 0   # clicking the power button again closes the menu
dir=$(dirname "$(readlink -f "$0")")
choice=$(printf 'Shutdown\nSleep\nLog out\n' | wofi --dmenu --hide-search --prompt "" \
    --location top_right --xoffset -6 --yoffset 36 --width 170 --lines 3 \
    --style "$dir/wofi/power.css" --cache-file /dev/null)
case "$choice" in
    Shutdown) systemctl poweroff ;;
    Sleep)    systemctl suspend ;;
    "Log out") qtile cmd-obj -o cmd -f shutdown ;;
esac
