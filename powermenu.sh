#!/bin/sh
# Power menu: shows choices in fuzzel, nothing happens until one is picked.
choice=$(printf 'Shutdown\nSleep\nLog out\n' | fuzzel --dmenu --prompt "power > " --lines 3 --width 16)
case "$choice" in
    Shutdown) systemctl poweroff ;;
    Sleep)    systemctl suspend ;;
    "Log out") qtile cmd-obj -o cmd -f shutdown ;;
esac
