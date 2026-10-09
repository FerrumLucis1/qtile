#!/bin/sh
# Starts the demo desktop: virtual screen -> Qtile (mini config) -> VNC -> noVNC web page.
# Env: PORT (web port, default 8080) · SESSION_SECONDS (auto-exit, default 900; 0 = never)
#      VNC_PASSWORD (optional) · SCREEN (default 1024x640x24)
set -e
export DISPLAY=:1
PORT="${PORT:-8080}"
SCREEN="${SCREEN:-1024x640x24}"
export MOD=mod1            # Alt is the main key in the browser (Super is grabbed by the OS)
export TERMINAL="xterm -fa Monospace -fs 11 -bg #1a1f1c -fg #d5ddd7"

Xvfb "$DISPLAY" -screen 0 "$SCREEN" -nolisten tcp >/dev/null 2>&1 &
sleep 1
qtile start -c /app/config.py >/tmp/qtile.log 2>&1 &
sleep 2
DISPLAY=$DISPLAY $TERMINAL >/dev/null 2>&1 &   # one terminal so the screen isn't empty

AUTH="-nopw"
if [ -n "$VNC_PASSWORD" ]; then
  x11vnc -storepasswd "$VNC_PASSWORD" /tmp/vncpass >/dev/null 2>&1
  AUTH="-rfbauth /tmp/vncpass"
fi
# localhost-only VNC; one viewer at a time; noVNC is the only public door
x11vnc -display "$DISPLAY" $AUTH -localhost -forever -nevershared -noxdamage -rfbport 5900 -quiet >/dev/null 2>&1 &
sleep 1

if [ "${SESSION_SECONDS:-900}" != "0" ]; then
  ( sleep "${SESSION_SECONDS:-900}"; echo "session time limit reached"; kill 1 ) &
fi
exec websockify --web /usr/share/novnc "$PORT" localhost:5900
