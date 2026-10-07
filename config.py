# Qtile config (Wayland) - shared by Gabriel's laptop (Fedora) and desktop (CachyOS).
# Laptop-only parts (battery icon, brightness keys, idle dimming) switch themselves
# off on a machine without a battery / backlight - see HAS_BATTERY and HAS_BACKLIGHT.
# Backup of the pre-cleanup version: branch "backup-pre-cleanup" on GitHub.
import glob
import json
import math
import os
import shutil
import subprocess
from typing import Any, cast

from libqtile import bar, hook, layout, qtile, widget
from libqtile.backend.wayland import InputConfig
from libqtile.command.base import expose_command
from libqtile.config import Click, Drag, Group, IdleInhibitor, IdleTimer, Key, Match, Output, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal
from libqtile.widget import base

# ---------------------------------------------------------------- colours
bg, fg, dim, accent = "#1a1f1c", "#d5ddd7", "#6f7d74", "#7fa38a"
BAR_BG, BLUE, LOW = "#1e3527", "#4aa3ff", "#c47a74"
# the repo this config lives in (config.py is symlinked from there), wherever it was cloned
HOME_REPO = os.path.dirname(os.path.realpath(__file__))

# ---------------------------------------------------------------- which machine
# laptop: has a battery and a screen backlight; desktop: has neither
BATTERIES = sorted(glob.glob("/sys/class/power_supply/BAT*"))
HAS_BATTERY = bool(BATTERIES)
HAS_BACKLIGHT = bool(glob.glob("/sys/class/backlight/*"))

mod = "mod4"
terminal = guess_terminal()


# ---------------------------------------------------------------- monitors
def screen_towards(q: Any, side: str) -> Any:
    """The nearest screen to the left/right/up/down of the focused one, by real position."""
    cur = q.current_screen
    cx, cy = cur.x + cur.width / 2, cur.y + cur.height / 2

    def centre(s: Any) -> tuple[float, float]:
        return s.x + s.width / 2, s.y + s.height / 2

    tests = {
        "left": lambda x, y: x < cx, "right": lambda x, y: x > cx,
        "up": lambda x, y: y < cy, "down": lambda x, y: y > cy,
    }
    cands = [s for s in q.screens if s is not cur and tests[side](*centre(s))]
    return min(cands, key=lambda s: abs(centre(s)[0] - cx) + abs(centre(s)[1] - cy), default=None)


@lazy.function
def focus_side(q: Any, side: str) -> None:
    target = screen_towards(q, side)
    if target is not None:
        q.focus_screen(target.index)


@lazy.function
def move_side(q: Any, side: str) -> None:
    """Send the focused window to the monitor on that side and follow it."""
    win, target = q.current_window, screen_towards(q, side)
    if win is not None and target is not None:
        win.togroup(target.group.name)
        q.focus_screen(target.index)
        target.group.focus(win)


@lazy.function
def move_other(q: Any) -> None:
    """Send the focused window to the next monitor and follow it."""
    win = q.current_window
    if win is not None and len(q.screens) > 1:
        target = q.screens[(q.current_screen.index + 1) % len(q.screens)]
        win.togroup(target.group.name)
        q.focus_screen(target.index)
        target.group.focus(win)

# ---------------------------------------------------------------- keys
def section(name: str, ks: list[Key]) -> list[Key]:
    """Tag keys with a heading for the Super+/ cheat sheet."""
    for k in ks:
        setattr(k, "section", name)
    return ks


@lazy.function
def cheat_sheet(q: Any) -> None:
    """Super+/ : dump the current key bindings and open the cheat sheet."""
    names = {"mod4": "Super", "shift": "Shift", "control": "Ctrl", "mod1": "Alt"}
    summary = [  # one line each instead of 4-9 near-identical keys
        ("Windows", "Super + h/j/k/l", "Focus window left/down/up/right"),
        ("Windows", "Super + Shift + h/j/k/l", "Move window"),
        ("Windows", "Super + Ctrl + h/j/k/l", "Grow window"),
        ("Windows", "Super + Ctrl + arrows", "Move floating window"),
        ("Windows", "Super + Shift + arrows", "Resize floating window"),
        ("Workspaces", "Super + 1-9", "Switch to workspace"),
        ("Workspaces", "Super + Shift + 1-9", "Move window to workspace"),
    ]
    rows = [{"section": a, "keys": b, "desc": c} for a, b, c in summary if a == "Windows"] + [
        {
            "section": getattr(k, "section", "Other"),
            "keys": " + ".join([names.get(m, m) for m in k.modifiers] + [KEY_LABELS.get(k.key, k.key)]),
            "desc": k.desc,
        }
        for k in q.config.keys if k.desc and not getattr(k, "hidden", False)
    ]
    rows += [{"section": a, "keys": b, "desc": c} for a, b, c in summary if a != "Windows"]
    path = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "qtile-keys.json")
    with open(path, "w") as f:
        json.dump(rows, f)
    subprocess.Popen([f"{HOME_REPO}/menu.sh", "cheatsheet"])


KEY_LABELS = {
    "comma": ",", "period": ".", "slash": "/", "Return": "Enter", "space": "Space",
    "Escape": "Esc", "Print": "PrtSc", "Left": "←", "Right": "→", "Up": "↑", "Down": "↓",
    "XF86AudioRaiseVolume": "Vol Up", "XF86AudioLowerVolume": "Vol Down", "XF86AudioMute": "Mute",
    "XF86MonBrightnessUp": "Bright Up", "XF86MonBrightnessDown": "Bright Down",
}
DIRS = (("h", "left"), ("l", "right"), ("j", "down"), ("k", "up"))
ARROWS = (("Left", -30, 0), ("Right", 30, 0), ("Up", 0, -30), ("Down", 0, 30))


def hidden(ks: list[Key]) -> list[Key]:
    """Keep these out of the cheat sheet (a summary line is shown instead)."""
    for k in ks:
        setattr(k, "hidden", True)
    return ks


keys = [
    *section("Windows", [
        *hidden([Key([mod], k, getattr(lazy.layout, d)(), desc=f"Focus window {d}") for k, d in DIRS]),
        *hidden([Key([mod, "shift"], k, getattr(lazy.layout, f"shuffle_{d}")(), desc=f"Move window {d}")
                 for k, d in DIRS]),
        *hidden([Key([mod, "control"], k, getattr(lazy.layout, f"grow_{d}")(), desc=f"Grow window {d}")
                 for k, d in DIRS]),
        Key([mod], "space", lazy.layout.next(), desc="Focus next window"),
        Key([mod], "n", lazy.layout.normalize(), desc="Reset window sizes"),
        Key([mod, "shift"], "Return", lazy.layout.toggle_split(), desc="Toggle split"),
        Key([mod], "Tab", lazy.next_layout(), desc="Next layout"),
        Key([mod], "q", lazy.window.kill(), desc="Close window"),
        Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
        Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating"),
        *hidden([Key([mod, "control"], k, lazy.window.move_floating(x, y), desc=f"Move floating window {k}")
                 for k, x, y in ARROWS]),
        *hidden([Key([mod, "shift"], k, lazy.window.resize_floating(x, y), desc=f"Resize floating window {k}")
                 for k, x, y in ARROWS]),
    ]),
    *section("Apps", [
        Key([mod], "x", lazy.spawn(terminal), desc="Terminal"),
        Key([mod], "d", lazy.spawn("fuzzel"), desc="App launcher"),
        Key([mod], "b", lazy.spawn("brave-browser --ozone-platform=wayland"), desc="Brave"),
        Key([mod], "e", lazy.spawn("thunar"), desc="File manager"),
    ]),
    *section("Monitors", [
        Key([mod], "comma", focus_side("left"), desc="Focus monitor on the left"),
        Key([mod], "period", focus_side("right"), desc="Focus monitor on the right"),
        Key([mod, "shift"], "comma", move_side("left"), desc="Move window to monitor on the left"),
        Key([mod, "shift"], "period", move_side("right"), desc="Move window to monitor on the right"),
        Key([mod], "o", lazy.next_screen(), desc="Focus next monitor"),
        Key([mod, "shift"], "o", move_other(), desc="Move window to next monitor"),
        Key([mod], "p", lazy.spawn([f"{HOME_REPO}/menu.sh", "displaymenu"]), desc="Display settings"),
    ]),
    *section("Screenshots", [
        Key([], "Print", lazy.spawn([f"{HOME_REPO}/screenshot.sh", "full"]), desc="Screenshot of everything"),
        Key(["shift"], "Print", lazy.spawn([f"{HOME_REPO}/screenshot.sh", "area"]), desc="Screenshot of an area"),
        Key([mod, "shift"], "s", lazy.spawn([f"{HOME_REPO}/screenshot.sh", "area"]), desc="Screenshot of an area"),
    ]),
    *section("System", [
        Key([mod], "Escape", lazy.spawn(f"{HOME_REPO}/lock.sh"), desc="Lock screen"),
        Key([mod], "slash", cheat_sheet(), desc="This cheat sheet"),
        Key([mod, "control"], "r", lazy.reload_config(), desc="Reload config"),
        Key([mod, "control"], "q", lazy.shutdown(), desc="Quit Qtile (log out)"),
        Key([], "XF86AudioRaiseVolume", lazy.widget["volicon"].change("5%+"), desc="Volume up"),
        Key([], "XF86AudioLowerVolume", lazy.widget["volicon"].change("5%-"), desc="Volume down"),
        Key([], "XF86AudioMute", lazy.widget["volicon"].toggle_mute(), desc="Mute"),
        *([
            Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set 5%+"), desc="Brightness up"),
            Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-"), desc="Brightness down"),
        ] if HAS_BACKLIGHT else []),
        # Ctrl+Alt+F1..F7 switch virtual terminals
        *hidden([Key(["control", "mod1"], f"f{vt}", lazy.core.change_vt(vt), desc=f"Switch to VT{vt}")
                 for vt in range(1, 8)]),
    ]),
]

groups = [Group(i) for i in "123456789"]
for g in groups:
    keys += hidden([
        Key([mod], g.name, lazy.group[g.name].toscreen(), desc=f"Switch to workspace {g.name}"),
        Key([mod, "shift"], g.name, lazy.window.togroup(g.name, switch_group=True),
            desc=f"Move window to workspace {g.name}"),
    ])

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
POPUPS: set[str] = {"powermenu", "wifimenu", "btmenu", "volmenu", "batmenu", "displaymenu", "cheatsheet"}  # GTK menus opened from the bar
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

# idle: dim after 5 min (laptop only), lock after 10 min; never while a window is fullscreen (videos, games)
idle_timers = [
    *([IdleTimer(300, lazy.spawn("brightnessctl -s set 20%"), lazy.spawn("brightnessctl -r"))]
      if HAS_BACKLIGHT else []),
    IdleTimer(600, lazy.spawn(f"{HOME_REPO}/lock.sh")),
]
idle_inhibitors = [IdleInhibitor(when="fullscreen")]


# ---------------------------------------------------------------- bar helpers
def read(path: str) -> str:
    try:
        with open(path) as f:
            return f.read().strip()
    except OSError:
        return ""


def radio_on(kind: str) -> bool:
    """True if the rfkill radio of this type ('wlan'/'bluetooth') exists and isn't blocked."""
    for t in glob.glob("/sys/class/rfkill/*/type"):
        if read(t) == kind:
            d = t[:-4]
            return read(d + "soft") != "1" and read(d + "hard") != "1"
    return False


def wifi_level(iface: str) -> int:
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


def wired_up() -> bool:
    """True when a real (physical, non-Wi-Fi) network port has a cable with a live link.
    Virtual interfaces like lo, tailscale0 or docker have no 'device' entry, so they're skipped."""
    for d in glob.glob("/sys/class/net/*"):
        if os.path.exists(f"{d}/device") and not os.path.exists(f"{d}/wireless"):
            if read(f"{d}/carrier") == "1" and read(f"{d}/operstate") == "up":
                return True
    return False


def wifi_state() -> tuple[bool, bool, int, bool]:
    """(radio_on, connected, level 0-3, ethernet_plugged_in)"""
    if wired_up():
        return True, True, 3, True
    on = radio_on("wlan")
    for d in glob.glob("/sys/class/net/*/wireless"):
        iface = d.split("/")[4]
        if read(f"/sys/class/net/{iface}/operstate") == "up":
            return on, True, wifi_level(iface), False
    return on, False, 0, False


# 16x16 pixel art: monitor with a network plug (the Ethernet symbol)
ETHERNET_ICON = [
    "#####.##########",
    "#...#..........#",
    "#.#.#..........#",
    "#.#.#..........#",
    "#...#..........#",
    "#####..........#",
    "..#............#",
    "#.#............#",
    "#.#............#",
    "#.#............#",
    "#.#............#",
    "#.#.############",
    "#.#.############",
    "..#...####......",
    "..##..####......",
    "...#########....",
]


class WifiArcs(base._Widget):
    """Network symbol. Ethernet cable connected: a monitor with a network plug.
    Otherwise Wi-Fi as a dot plus 3 arcs: blue arcs = signal strength,
    white = unlit, grey = Wi-Fi off."""

    defaults = [("update_interval", 3, "Seconds between checks")]

    def __init__(self, **config: Any) -> None:
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(WifiArcs.defaults)
        self.state: tuple[bool, bool, int, bool] | None = None

    def calculate_length(self) -> int:
        return 36  # a little wider than the icon so it is easy to click

    def timer_setup(self) -> None:
        self.poll()

    def poll(self) -> None:
        new = wifi_state()
        if new != self.state:
            self.state = new
            self.draw()
        self.timeout_add(self.update_interval, self.poll)

    def draw(self) -> None:
        if not self.state:
            return
        on, connected, level, wired = self.state
        self.drawer.clear(self.background or self.bar.background)
        ctx = self.drawer.ctx
        if wired:
            self.draw_ethernet(ctx)
            self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.length)
            return
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

    def draw_ethernet(self, ctx: Any) -> None:
        """Wired connection: a monitor with a network plug beside it, drawn pixel by
        pixel on whole-pixel positions so it stays sharp."""
        x0 = int((self.length - len(ETHERNET_ICON[0])) / 2)
        y0 = int((self.bar.height - len(ETHERNET_ICON)) / 2)
        self.drawer.set_source_rgb(fg)
        for y, row in enumerate(ETHERNET_ICON):
            for x, px in enumerate(row):
                if px == "#":
                    ctx.rectangle(x0 + x, y0 + y, 1, 1)
        ctx.fill()

def text_layout(w: Any, text: str = "") -> Any:
    return w.drawer.textlayout(text, fg, w.font, w.fontsize, None, wrap=False)


class VolumeIcon(base._Widget):
    """Speaker drawn with 0-3 sound waves for the volume level (an X when muted).
    While the volume is being changed it shows the percentage for a moment."""

    defaults = [
        ("update_interval", 2, "Seconds between checks for outside changes"),
        ("show_for", 1.5, "Seconds to show the percentage after a change"),
        ("font", "JetBrainsMono Nerd Font", ""),
        ("fontsize", 13, ""),
    ]

    def __init__(self, **config: Any) -> None:
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(VolumeIcon.defaults)
        self.vol: int = 0
        self.muted: bool = False
        self.showing: Any = None

    def _configure(self, qtile: Any, bar_: Any) -> None:
        base._Widget._configure(self, qtile, bar_)
        self.tl: Any = text_layout(self)

    def calculate_length(self) -> int:
        return 40

    def read(self) -> None:
        try:
            out = subprocess.run(["wpctl", "get-volume", "@DEFAULT_AUDIO_SINK@"],
                                 capture_output=True, text=True, timeout=1).stdout
            self.vol = round(float(out.split()[1]) * 100)
            self.muted = "MUTED" in out
        except Exception:
            pass

    def timer_setup(self) -> None:
        self.poll()

    def poll(self) -> None:
        before = (self.vol, self.muted)
        self.read()
        if (self.vol, self.muted) != before:
            self.draw()
        self.timeout_add(self.update_interval, self.poll)

    def flash(self) -> None:
        """Show the percentage for a moment, then go back to the icon."""
        if self.showing:
            self.showing.cancel()
        self.showing = self.timeout_add(self.show_for, self.end_flash)
        self.draw()

    def end_flash(self) -> None:
        self.showing = None
        self.draw()

    @expose_command()
    def change(self, step: str = "5%+") -> None:
        subprocess.run(["wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", step], timeout=1)
        self.read()
        self.flash()

    @expose_command()
    def toggle_mute(self) -> None:
        subprocess.run(["wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"], timeout=1)
        self.read()
        self.flash()

    @expose_command()
    def refresh(self) -> None:
        self.read()
        self.draw()

    def draw(self) -> None:
        self.drawer.clear(self.background or self.bar.background)
        if self.showing:
            self.tl.text = "mute" if self.muted else f"{self.vol}%"
            self.tl.colour = dim if self.muted else fg
            self.tl.draw((self.length - self.tl.width) / 2,
                             (self.bar.height - self.tl.height) / 2)
        else:
            ctx = self.drawer.ctx
            x, cy = self.length / 2 - 9, self.bar.height / 2
            self.drawer.set_source_rgb(dim if self.muted else fg)
            ctx.new_path()  # speaker: small box + cone
            ctx.move_to(x, cy - 3)
            ctx.line_to(x + 3, cy - 3)
            ctx.line_to(x + 8, cy - 7)
            ctx.line_to(x + 8, cy + 7)
            ctx.line_to(x + 3, cy + 3)
            ctx.line_to(x, cy + 3)
            ctx.close_path()
            ctx.fill()
            ctx.set_line_width(1.8)
            if self.muted or self.vol == 0:
                for a, b in ((-1, 1), (1, -1)):
                    ctx.new_path()
                    ctx.move_to(x + 11, cy - 3 * a)
                    ctx.line_to(x + 17, cy - 3 * b)
                    ctx.stroke()
            else:
                level = 1 if self.vol < 34 else 2 if self.vol < 67 else 3
                for i, r in enumerate((4, 7.5, 11), start=1):
                    self.drawer.set_source_rgb(fg if i <= level else dim)
                    ctx.new_path()
                    ctx.arc(x + 6, cy, r, -math.pi / 4, math.pi / 4)
                    ctx.stroke()
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.length)


def battery_info() -> tuple[int, str]:
    """(percent, status) from sysfs."""
    if not BATTERIES:
        return 0, "Unknown"
    b = BATTERIES[0] + "/"
    try:
        return int(read(b + "capacity")), read(b + "status")
    except ValueError:
        return 0, "Unknown"


class BatteryIcon(base._Widget):
    """Battery outline filled to the charge level, with the percentage to the right.
    Red when low, lightning bolt when charging."""

    defaults = [
        ("update_interval", 1, "Seconds between checks"),
        ("low", 20, "Percent at which it turns red"),
        ("font", "JetBrainsMono Nerd Font", ""),
        ("fontsize", 13, ""),
    ]

    def __init__(self, **config: Any) -> None:
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(BatteryIcon.defaults)
        self.state: tuple[int, str] | None = None

    def _configure(self, qtile: Any, bar_: Any) -> None:
        base._Widget._configure(self, qtile, bar_)
        self.tl: Any = text_layout(self, "\uf0e7100%")
        self.text_w: int = self.tl.width  # widest possible text, so the bar doesn't jump

    def calculate_length(self) -> int:
        return 26 + self.text_w

    def timer_setup(self) -> None:
        self.poll()

    def poll(self) -> None:
        new = battery_info()
        if new != self.state:
            self.state = new
            self.draw()
        self.timeout_add(self.update_interval, self.poll)

    def draw(self) -> None:
        if not self.state:
            return
        pct, status = self.state
        charging = status == "Charging"
        colour = LOW if pct <= self.low and not charging else fg
        self.drawer.clear(self.background or self.bar.background)
        ctx = self.drawer.ctx
        x, y, w, h = 3, self.bar.height / 2 - 5, 18, 10
        self.drawer.set_source_rgb(colour)
        ctx.set_line_width(1.5)
        ctx.new_path()
        ctx.rectangle(x, y, w, h)  # body
        ctx.stroke()
        ctx.rectangle(x + w, y + 3, 2, 4)  # terminal nub
        ctx.fill()
        ctx.rectangle(x + 2, y + 2, (w - 4) * max(pct, 3) / 100, h - 4)  # charge level
        ctx.fill()
        self.tl.text = ("\uf0e7" if charging else "") + f"{pct}%"
        self.tl.colour = colour
        self.tl.draw(26, (self.bar.height - self.tl.height) / 2)
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.length)


def bt_icon() -> str:
    return f'<span foreground="{BLUE if radio_on("bluetooth") else fg}"></span>'


def menu(name: str) -> Any:
    return lazy.spawn([f"{HOME_REPO}/menu.sh", name])


def sep() -> widget.Sep:
    return widget.Sep(linewidth=1, padding=8, size_percent=50, foreground=dim)


# ---------------------------------------------------------------- bar
widget_defaults = dict(font="JetBrainsMono Nerd Font", fontsize=15, padding=6, foreground=fg)
extension_defaults = widget_defaults.copy()
SMALL = 13  # stats text size

def main_bar() -> bar.Bar:
    return bar.Bar(
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
            widget.Memory(format="mem {MemPercent:.0f}%", fontsize=SMALL),
            sep(),
            widget.CPU(format="cpu {load_percent:.0f}%", fontsize=SMALL),
            sep(),
            VolumeIcon(name="volicon", mouse_callbacks={
                "Button1": menu("volmenu"),
                "Button4": lazy.widget["volicon"].change("5%+"),  # scroll up
                "Button5": lazy.widget["volicon"].change("5%-"),  # scroll down
            }),
            sep(),
            *([BatteryIcon(mouse_callbacks={"Button1": menu("batmenu")}), sep()] if HAS_BATTERY else []),
            widget.GenPollText(func=bt_icon, update_interval=1, fontsize=18, padding=8,
                               mouse_callbacks={"Button1": menu("btmenu")}),
            sep(),
            WifiArcs(mouse_callbacks={"Button1": menu("wifimenu")}),
            sep(),
            widget.TextBox("⏻", fontsize=18,
                           mouse_callbacks={"Button1": lazy.spawn(f"{HOME_REPO}/powermenu.sh")}),
        ],
        24,
        background=BAR_BG,
        margin=[6, 6, 0, 6],
    )


def wallpaper() -> dict[str, Any]:
    """Desktop picture: the first wallpapers/background.* in the repo, else a plain colour."""
    found = sorted(glob.glob(f"{HOME_REPO}/wallpapers/background.*"))
    return {"wallpaper": found[0], "wallpaper_mode": "fill"} if found else {"background": "#1f1a1a"}


_main_screen = Screen(top=main_bar(), **wallpaper())  # created once and reused, like a static
_extra_screens: list[Screen] = []       # `screens` list, so plugging/unplugging a
                                        # monitor never rebuilds the bar


def generate_screens(outputs: list[Output]) -> list[Screen]:
    """One Screen per connected output; the full bar always goes on the laptop panel
    (eDP), whatever side the external monitor is placed on."""
    laptop = next((i for i, o in enumerate(outputs) if (o.port or "").startswith(("eDP", "LVDS"))), 0)
    while len(_extra_screens) < len(outputs) - 1:
        _extra_screens.append(Screen(**wallpaper()))
    extras = iter(_extra_screens)
    return [_main_screen if i == laptop else next(extras) for i in range(len(outputs))]


# ---------------------------------------------------------------- hooks
@hook.subscribe.client_managed
def place_popup(c: Any) -> None:
    """Bar menus open under the bar in the top-right corner; the display menu
    (Super+P) and cheat sheet (Super+/) open in the middle of the focused screen."""
    classes = set(c.get_wm_class() or [])
    if not POPUPS & classes:
        return
    q = cast(Any, qtile)
    w, h = (c.width or 240), (c.height or 120)
    if classes & {"displaymenu", "cheatsheet"}:
        scr = q.current_screen
        x, y = scr.x + (scr.width - w) // 2, scr.y + (scr.height - h) // 2
    else:
        scr = next((s for s in q.screens if s.top), q.current_screen)  # the screen with the bar
        x, y = scr.x + scr.width - w - 6, scr.y + 36
    c.place(x, y, w, h, 0, accent, above=True)


_known_outputs: set[str] = set()


@hook.subscribe.screens_reconfigured
def monitors_changed() -> None:
    """When a monitor is plugged in, put it on the side saved for it (Super+P);
    when one is unplugged, move the laptop back to the origin."""
    ports = {s.output.port for s in cast(Any, qtile).screens if s.output and s.output.port}
    if ports != _known_outputs:  # plugged in or unplugged
        subprocess.Popen([f"{HOME_REPO}/displaymenu.py", "--apply"])
    _known_outputs.clear()
    _known_outputs.update(ports)


@hook.subscribe.startup_once
def autostart() -> None:
    subprocess.Popen(["swayidle", "-w", "before-sleep", f"{HOME_REPO}/lock.sh"])  # lock on sleep / lid close
    subprocess.Popen([f"{HOME_REPO}/displaymenu.py", "--apply"])
    # password pop-ups for admin actions: whichever agent this machine has
    # (lxpolkit on the Fedora laptop, KDE's or GNOME's agent on the CachyOS desktop)
    for agent in ("lxpolkit", "/usr/lib/polkit-kde-authentication-agent-1",
                  "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1"):
        if shutil.which(agent):  # finds commands on PATH and full paths alike
            subprocess.Popen([agent])
            break
    subprocess.Popen([os.path.expanduser("~/.config/qtile/autostart.sh")])
