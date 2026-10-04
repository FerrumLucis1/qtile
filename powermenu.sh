#!/bin/sh
# Toggle the GTK power menu: first click opens it, clicking again closes it.
pkill -f powermenu.py && exit 0
exec python3 "$(dirname "$(readlink -f "$0")")/powermenu.py"
