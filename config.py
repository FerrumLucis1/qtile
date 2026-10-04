# Qtile config (Wayland) - Gabriel's laptop
# Backup of the pre-cleanup version: branch "backup-pre-cleanup" on GitHub.
import glob
import math
import os
import subprocess

from libqtile import bar, hook, layout, qtile, widget
from libqtile.backend.wayland import InputConfig
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.widget import base

# ---------------------------------------------------------------- colours
bg, fg, dim, accent = "#1a1f1c", "#d5ddd7", "#6f7d74", "#7fa38a"
BAR_BG, BLUE, LOW = "#1e3527", "#4aa3ff", "#c47a74"
HOME_REPO = os.path.expanduser("~/qtile")

mod = "mod4"
terminal = guess_terminal()

# ---------------------------------------------------------------- keys
keys = [
    # focus / move / grow windows (h j k l)
    *[Key([mod], k, getattr(lazy.layout, d)(), desc=f"Focus {d}")
      for k, d in zip("hljk", ("left", "right", "down", "up"))],
    *[Key([mod, "shift"], k, getattr(lazy.layout, f"shuffle_{d}")(), desc=f"Move window {d}")
      for k, d in zip("hljk", ("left", "right", "down", "up"))],
    *[Key([mod, "control"], k, getattr(lazy.layout, f"grow_{d}")(), desc=f"Grow window {d}")
      for k, d in zip("hljk", ("left", "right", "down", "up"))],
    Key([mod], "space", lazy.layout.next(), desc="Focus next window"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset window sizes"),
    Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle split"),
    Key([mod], "Tab", lazy.next_layout(), desc="Next layout"),
    Key([mod], "q", lazy.window.kill(), desc="Close window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Quit Qtile"),
    # apps
    Key([mod], "x", lazy.spawn(terminal), desc="Terminal"),
    Key([mod], "d", lazy.spawn("fuzzel"), desc="Launcher"),
    Key([mod], "b", lazy.spawn("brave-browser --ozone-platform=wayland"), desc="Brave"),
    # floating windows: Ctrl+Super+arrows move, Shift+Super+arrows resize
    *[Key([mod, "control"], k, lazy.window.move_floating(x, y)) for k, x, y in
      (("Left", -30, 0), ("Right", 30, 0), ("Up", 0, -30), ("Down", 0, 30))],
    *[Key([mod, "shift"], k, lazy.window.resize_floating(x, y)) for k, x, y in
      (("Left", -30, 0), ("Right", 30, 0), ("Up", 0, -30), ("Down", 0, 30))],
    # media keys
    Key([], "XF86AudioRaiseVolume", lazy.spawn("wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")),
    Key([], "XF86AudioMute", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")),
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set 5%+")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-")),
    # second screen (TV)
    Key([mod], "o", lazy.next_screen(), desc="Focus next screen"),
    Key([mod, "shift"], "o", lazy.window.toscreen(1), desc="Send window to screen 2"),
    Key([mod, "shift"], "i", lazy.window.toscreen(0), desc="Window to laptop"),
    # Ctrl+Alt+F1..F7 switch virtual terminals
    *[Key(["control", "mod1"], f"f{vt}", lazy.core.change_vt(vt), desc=f"Switch to VT{vt}")
      for vt in range(1, 8)],
]

groups = [Group(i) for i in "123456789"]
for g in groups:
    keys += [
        Key([mod], g.name, lazy.group[g.name].toscreen(), desc=f"Switch to group {g.name}"),
        Key([mod, "shift"], g.name, lazy.window.togroup(g.name, switch_group=True),
            desc=f"Move window to group {g.name}"),
    ]

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

# ---------------------------------------------------------------- layouts
layouts = [
    layout.Columns(margin=8, border_width=2, border_focus=accent, border_normal=bg),
    layout.Max(),
]
POPUPS = {"powermenu", "wifimenu", "btmenu"}  # GTK menus opened from the bar
floating_layout = layout.Floating(float_rules=[
    *layout.Floating.default_float_rules,
    *[Match(wm_class=c) for c in ("confirmreset", "makebranch", "maketag", "ssh-askpass", *POPUPS)],
    Match(title="branchdialog"),
    Match(title="pinentry"),
])

wl_input_rules = {
    "type:keyboard": InputConfig(kb_layout="us"),
    "type:touchpad": InputConfig(tap=True, natural_scroll=True),
}

# focus, floating, cursor and other general settings are left at Qtile defaults


# ---------------------------------------------------------------- bar helpers
def read(path):
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def radio_on(kind):
    """True if the rfkill radio of this type ('wlan'/'bluetooth') exists and isn't blocked."""
    for t in glob.glob("/sys/class/rfkill/*/type"):
        if read(t) == kind:
            d = t[:-4]
            return read(d + "soft") != "1" and read(d + "hard") != "1"
    return False


def wifi_level(iface):
    """Signal bars 0-3 from `iw` (dBm); falls back to nmcli if iw is missing."""
    try:
        out = subprocess.run(["iw", "dev", iface, "link"], capture_output=True, text=True, timeout=1).stdout
        for line in out.splitlines():
            if "signal:" in line:
                dbm = float(line.split()[1])
                return 3 if dbm >= -60 else 2 if dbm >= -70 else 1 if dbm >= -80 else 0
        return 0
    except FileNotFoundError:
        pass
    except Exception:
        return 0
    try:
        out = subprocess.run(["nmcli", "-t", "-f", "IN-USE,SIGNAL", "dev", "wifi", "list", "--rescan", "no"],
                             capture_output=True, text=True, timeout=2).stdout
        for line in out.splitlines():
            if line.startswith("*:"):
                pct = int(line.split(":")[1])
                return 3 if pct >= 70 else 2 if pct >= 50 else 1 if pct >= 30 else 0
    except Exception:
        pass
    return 0


def wifi_state():
    """(radio_on, connected, level 0-3)"""
    on = radio_on("wlan")
    for d in glob.glob("/sys/class/net/*/wireless"):
        iface = d.split("/")[4]
        if read(f"/sys/class/net/{iface}/operstate") == "up":
            return on, True, wifi_level(iface)
    return on, False, 0


class WifiArcs(base._Widget):
    """Wi-Fi symbol drawn as a dot plus 3 arcs: blue arcs = signal strength,
    white = unlit, grey = Wi-Fi off."""

    defaults = [("update_interval", 3, "Seconds between checks")]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(WifiArcs.defaults)
        self.state = None

    def calculate_length(self):
        return 30

    def timer_setup(self):
        self.poll()

    def poll(self):
        new = wifi_state()
        if new != self.state:
            self.state = new
            self.draw()
        self.timeout_add(self.update_interval, self.poll)

    def draw(self):
        if not self.state:
            return
        on, connected, level = self.state
        self.drawer.clear(self.background or self.bar.background)
        ctx = self.drawer.ctx
        cx, cy = self.length / 2, self.bar.height / 2 + 6
        ctx.set_line_width(2)
        for i, r in enumerate((5, 9, 13), start=1):
            self.drawer.set_source_rgb(dim if not on else BLUE if connected and i <= level else fg)
            ctx.new_path()
            ctx.arc(cx, cy, r, -3 * math.pi / 4, -math.pi / 4)
            ctx.stroke()
        self.drawer.set_source_rgb(dim if not on else BLUE if connected else fg)
        ctx.new_path()
        ctx.arc(cx, cy, 1.8, 0, 2 * math.pi)
        ctx.fill()
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.length)


def bt_icon():
    return f'<span foreground="{BLUE if radio_on("bluetooth") else fg}"></span>'


def menu(name):
    return lazy.spawn([f"{HOME_REPO}/menu.sh", name])


def sep():
    return widget.Sep(linewidth=1, padding=8, size_percent=50, foreground=dim)


# ---------------------------------------------------------------- bar
widget_defaults = dict(font="JetBrainsMono Nerd Font", fontsize=15, padding=6, foreground=fg)
extension_defaults = widget_defaults.copy()
SMALL = 13  # stats text size

screens = [
    Screen(
        top=bar.Bar(
            [
                widget.GroupBox(
                    highlight_method="block", rounded=False, disable_drag=True,
                    active=fg, inactive=dim, this_current_screen_border=accent,
                    padding_x=6, padding_y=3, margin_x=0,
                ),
                widget.Spacer(length=180),
                widget.Spacer(),
                widget.Clock(format="%a %b %d  %H:%M"),
                widget.Spacer(),
                widget.StatusNotifier(icon_size=16, padding=4),  # tray icons
                widget.DF(visible_on_warn=False, format="disk {r:.0f}%", fontsize=SMALL),
                sep(),
                widget.Volume(fmt="vol {}", fontsize=SMALL, update_interval=1),
                sep(),
                widget.Memory(format="mem {MemPercent:.0f}%", fontsize=SMALL),
                sep(),
                widget.CPU(format="cpu {load_percent:.0f}%", fontsize=SMALL),
                sep(),
                widget.Battery(
                    update_interval=1, fontsize=SMALL, format="bat {char}{percent:2.0%}",
                    charge_char=" ", discharge_char="", full_char=" ",
                    empty_char="", unknown_char="", low_percentage=0.2, low_foreground=LOW,
                ),
                widget.GenPollText(func=bt_icon, update_interval=1, fontsize=18, padding=8,
                                   mouse_callbacks={"Button1": menu("btmenu")}),
                WifiArcs(mouse_callbacks={"Button1": menu("wifimenu")}),
                widget.TextBox("⏻", fontsize=18,
                               mouse_callbacks={"Button1": lazy.spawn(f"{HOME_REPO}/powermenu.sh")}),
            ],
            24,
            background=BAR_BG,
            margin=[6, 6, 0, 6],
        ),
    ),
    Screen(),  # second monitor / TV
]


# ---------------------------------------------------------------- hooks
@hook.subscribe.client_managed
def place_popup(c):
    """Put the bar's pop-up menus just under the bar, top-right corner."""
    if POPUPS & set(c.get_wm_class() or []):
        scr = qtile.current_screen
        w, h = (c.width or 240), (c.height or 120)
        c.place(scr.x + scr.width - w - 6, scr.y + 36, w, h, 0, accent, above=True)


@hook.subscribe.startup_once
def autostart():
    subprocess.Popen(["lxpolkit"])
    subprocess.Popen(["swaybg", "-c", "#1f1a1a"])
    subprocess.Popen([os.path.expanduser("~/.config/qtile/autostart.sh")])
