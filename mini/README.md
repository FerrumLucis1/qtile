# qtile-mini

A stripped-down Qtile (X11) config built to use as little RAM and CPU as possible.
When nothing is open it sits at about **0% CPU** and **~47 MB** for the Qtile process.

Derived from [FerrumLucis1/qtile](https://github.com/FerrumLucis1/qtile) (same colours and key layout).

## What's in it
- Bar: workspaces + a clock (updates once a minute). No polling widgets.
- Layouts: Columns and Max. Floating windows, fullscreen, 9 workspaces.
- No compositor, wallpaper daemon, notification daemon, launcher or autostart programs.

## Keys (Super; set `MOD=mod1` to use Alt in a VM or browser)
| Keys | Action |
|---|---|
| Super + h/j/k/l | Focus window |
| Super + Shift + h/j/k/l | Move window |
| Super + Ctrl + h/j/k/l | Resize window |
| Super + 1-9 / Shift + 1-9 | Switch workspace / send window |
| Super + Tab | Next layout |
| Super + f / t / q | Fullscreen / float / close |
| Super + x | Terminal (`TERMINAL=xterm` by default) |
| Super + Ctrl + r / q | Reload / quit |

## Install
Needs Qtile 0.30+ and an X server. Copy `mini/config.py` to `~/.config/qtile/config.py`, then start `qtile start` from `.xinitrc` or a display manager.

## Measured (Qtile 0.37.1, Xvfb, idle, Python 3.13)
| Config | Qtile RSS | CPU (10 s idle) |
|---|---|---|
| Qtile stock default | 48.8 MB | ~0% |
| qtile-mini | 47.5 MB | 0% |
| qtile-mini, no bar | 43.2 MB | 0% |

Qtile is a Python program, so about 43 MB is the floor for the interpreter plus libqtile.
The config trims little RAM; what it saves is CPU wakeups and background programs.
For single-digit MB, use a C window manager (dwm, i3). The X server adds its own memory on top.

## Browser demo (Docker)
`Dockerfile` + `start.sh` run the desktop in a container and stream it to a web page (Xvfb + x11vnc + noVNC).
```
docker build -f mini/Dockerfile -t qtile-mini .
docker run --rm -p 8080:8080 qtile-mini
# open http://localhost:8080/vnc.html?autoconnect=true&resize=scale
```
- Alt is the main key in the browser (Alt+x terminal, Alt+1-9 workspaces, Alt+Tab layouts).
- Env: `PORT` (default 8080), `SESSION_SECONDS` (auto-exit, default 900), `VNC_PASSWORD` (optional), `SCREEN`.
- One viewer at a time. VNC listens on localhost only; noVNC is the only public port.
- **Visitors get a terminal inside the container.** Run it as the unprivileged user (the Dockerfile does), with no secrets mounted, and let the host restart it after each session.
- Tested: all five processes together use ~175 MB RAM idle (summed RSS, so slightly overcounted). The Dockerfile itself has not been build-tested (no Docker daemon where it was written), but the same stack was run and driven in a browser.
