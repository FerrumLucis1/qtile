#!/bin/sh
# Power menu: click-only list (no search box). Nothing happens until one is picked.
pkill -x rofi && exit 0   # clicking the power button again closes the menu
dir=$(dirname "$(readlink -f "$0")")
choice=$(printf 'Shutdown\nSleep\nLog out\n' | rofi -dmenu -no-custom -theme "$dir/rofi/power.rasi")
case "$choice" in
    Shutdown) systemctl poweroff ;;
    Sleep)    systemctl suspend ;;
    "Log out") qtile cmd-obj -o cmd -f shutdown ;;
esac
