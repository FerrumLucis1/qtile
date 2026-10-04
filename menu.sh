#!/bin/sh
# Toggle a bar pop-up menu: ./menu.sh wifimenu | btmenu
# First click opens it, clicking again closes it.
pkill -f "$1.py" && exit 0
exec python3 "$(dirname "$(readlink -f "$0")")/$1.py"
