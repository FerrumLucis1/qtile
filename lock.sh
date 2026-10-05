#!/bin/sh
# Lock the screen. The background explains what to do: type your password and press Enter.
dir="$(dirname "$(readlink -f "$0")")"
exec swaylock -f -i "$dir/swaylock/lock.png" -s center
