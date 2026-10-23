# Qtile (Wayland) desktop

My Qtile config for Wayland. One repo, two machines: a Fedora laptop and a CachyOS/Arch desktop. Laptop-only features (battery icon, brightness keys, idle dimming) switch themselves off on a machine without a battery or backlight.

## What's in it

- **`config.py`**: keys, layouts, multi-monitor handling, and a custom top bar (clock, volume, Wi-Fi, battery)
- **Pop-up menus** (small GTK scripts): Wi-Fi, Bluetooth, volume, battery, display settings, power
- **`install.sh`**: one-command setup for Fedora (`dnf`) or Arch (`pacman`)
- **Matching dark theme** for Alacritty, fuzzel, mako, swaylock, and GTK
- **`Super + /`** opens a built-in cheat sheet of every shortcut

## Install

```bash
git clone https://github.com/FerrumLucis1/qtile ~/qtile
~/qtile/install.sh --dry-run   # preview only
~/qtile/install.sh             # install packages and link configs
```

Safe to re-run. Existing config files are moved to `<name>.bak-<date>` before being replaced by links.

## Key shortcuts

| Keys | Action |
|---|---|
| `Super + X` | Terminal |
| `Super + D` | App launcher |
| `Super + B` | Browser |
| `Super + Q` | Close window |
| `Super + T` | Toggle floating |
| `Super + , / .` | Focus left / right monitor |
| `Super + /` | Cheat sheet |
| `Super + Ctrl + R` | Reload config |

## Wallpapers

Pictures are not committed (see `.gitignore`). Put `background.jpg` and `login.jpg` in `wallpapers/`.
