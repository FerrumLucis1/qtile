import os
from collections.abc import Callable

import libqtile.resources
from libqtile import bar, layout, qtile, widget
from libqtile.config import Click, Drag, Group, Key, Match, Output, Screen
from libqtile.lazy import lazy
from libqtile.utils import guess_terminal

mod = "mod4"
terminal = guess_terminal()

keys = [
    # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html
    # Switch between windows
    Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "h", lazy.layout.grow_left(), desc="Grow window to the left"),
    Key([mod, "control"], "l", lazy.layout.grow_right(), desc="Grow window to the right"),
    Key([mod, "control"], "j", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "k", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    Key(
        [mod, "shift"],
        "Return",
        lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack",
    ),
    Key([mod], "x", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
    Key(
        [mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen on the focused window",
    ),
    Key([mod], "t", lazy.window.toggle_floating(), desc="Toggle floating on the focused window"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
]

keys.extend([
    # This should allow you to move the floating windows around
    Key([mod, "control"], "Left",  lazy.window.move_floating(-30, 0)),
    Key([mod, "control"], "Right", lazy.window.move_floating(30, 0)),
    Key([mod, "control"], "Up",    lazy.window.move_floating(0, -30)),
    Key([mod, "control"], "Down",  lazy.window.move_floating(0, 30)),
    Key([mod, "shift"], "Left",  lazy.window.resize_floating(-30, 0)),
    Key([mod, "shift"], "Right", lazy.window.resize_floating(30, 0)),
    Key([mod, "shift"], "Up",    lazy.window.resize_floating(0, -30)),
    Key([mod, "shift"], "Down",  lazy.window.resize_floating(0, 30)),
])

# Add key bindings to switch VTs in Wayland.
# We can't check qtile.core.name in default config as it is loaded before qtile is started
# We therefore defer the check until the key binding is run by using .when(func=...)
for vt in range(1, 8):
    keys.append(
        Key(
            ["control", "mod1"],
            f"f{vt}",
            lazy.core.change_vt(vt).when(func=lambda: qtile.core.name == "wayland"),
            desc=f"Switch to VT{vt}",
        )
    )


groups = [Group(i) for i in "123456789"]

for i in groups:
    keys.extend(
        [
            # mod + group number = switch to group
            Key(
                [mod],
                i.name,
                lazy.group[i.name].toscreen(),
                desc=f"Switch to group {i.name}",
            ),
            # mod + shift + group number = switch to & move focused window to group
            Key(
                [mod, "shift"],
                i.name,
                lazy.window.togroup(i.name, switch_group=True),
                desc=f"Switch to & move focused window to group {i.name}",
            ),
            # Or, use below if you prefer not to switch to that group.
            # # mod + shift + group number = move focused window to group
            # Key([mod, "shift"], i.name, lazy.window.togroup(i.name),
            #     desc="move focused window to group {}".format(i.name)),
        ]
    )

layouts = [
    layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=4),
    layout.Max(),
    # Try more layouts by unleashing below layouts.
    # layout.Stack(num_stacks=2),
    # layout.Bsp(),
    # layout.Matrix(),
    # layout.MonadTall(),
    # layout.MonadWide(),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

widget_defaults = dict(
    font="sans",
    fontsize=12,
    padding=3,
)
extension_defaults = widget_defaults.copy()

logo = os.path.join(os.path.dirname(libqtile.resources.__file__), "logo.png")
screens = [
    Screen(
        bottom=bar.Bar(
            [
                widget.CurrentLayout(),
                widget.GroupBox(),
                widget.Prompt(),
                widget.WindowName(),
                widget.Chord(
                    chords_colors={
                        "launch": ("#ff0000", "#ffffff"),
                    },
                    name_transform=lambda name: name.upper(),
                ),
                widget.TextBox("default config", name="default"),
                widget.TextBox("Press &lt;M-r&gt; to spawn", foreground="#d75f5f"),
                # NB Systray is incompatible with Wayland, consider using StatusNotifier instead
                # widget.StatusNotifier(),
                widget.Systray(),
                widget.Clock(format="%Y-%m-%d %a %I:%M %p"),
                widget.QuickExit(),
            ],
            24,
            # border_width=[2, 0, 2, 0],  # Draw top and bottom borders
            # border_color=["ff00ff", "000000", "ff00ff", "000000"]  # Borders are magenta
        ),
        background="#000000",
        wallpaper=logo,
        wallpaper_mode="center",
        # You can uncomment this variable if you see that on X11 floating resize/moving is laggy
        # By default we handle these events delayed to already improve performance, however your system might still be struggling
        # This variable is set to None (no cap) by default, but you can set it to 60 to indicate that you limit it to 60 events per second
        # x11_drag_polling_rate = 60,
    ),
]

# Instead of screens, you can define a function here to specify which Screen
# should correspond to which Output.
fake_screens: list[Screen] | None = None

# Instead of screens or fake screens, you can define a function here that
# returns a list of Screen objects based on the list of Outputs; that way you
# can decide based on e.g. the number of screens, or which ports are plugged
# in exactly what do render in each bar for each screen.
generate_screens: Callable[[list[Output]], list[Screen]] | None = None

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
floats_kept_above = True
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="powermenu"),  # power menu
        Match(wm_class="wifimenu"),  # wifi menu
        Match(wm_class="btmenu"),  # bluetooth menu
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
focus_previous_on_window_remove = False
reconfigure_screens = True

# How long (in seconds) to wait after a screen change event before firing the
# screen_change hook, coalescing bursts of events into a single one.
screen_change_debounce_timeout = 1

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
wl_input_rules = None

# xcursor theme (string or None) and size (integer) for Wayland backend
wl_xcursor_theme = None
wl_xcursor_size = 24

idle_timers = []  # type: list
idle_inhibitors = []  # type: list

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"

# --- Wayland additions ---
import subprocess
from libqtile.widget import base
from libqtile import hook
from libqtile.backend.wayland import InputConfig
from libqtile.config import Key
from libqtile.lazy import lazy

wl_input_rules = {
    "type:keyboard": InputConfig(kb_layout="us"),
    "type:touchpad": InputConfig(tap=True, natural_scroll=True),
}

keys.append(Key([mod], "d", lazy.spawn("fuzzel"), desc="Launcher"))

BLUE = "#4aa3ff"


def wifi_state():
    """Return (radio_on, connected, level 0-3)."""
    import glob
    radio_on = True
    for t in glob.glob("/sys/class/rfkill/*/type"):
        try:
            if open(t).read().strip() == "wlan":
                d = t[:-4]
                if open(d + "soft").read().strip() == "1" or open(d + "hard").read().strip() == "1":
                    radio_on = False
        except OSError:
            pass
    for d in glob.glob("/sys/class/net/*/wireless"):
        iface = d.split("/")[4]
        try:
            if open(f"/sys/class/net/{iface}/operstate").read().strip() != "up":
                continue
        except OSError:
            continue
        return radio_on, True, wifi_level(iface)
    return radio_on, False, 0


def wifi_level(iface):
    """Signal bars 0-3. Uses `iw` (tiny, fast); falls back to nmcli if iw is missing."""
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


class WifiArcs(base._Widget):
    """Wi-Fi symbol drawn as a dot plus 3 arcs. Arcs light up blue with signal
    strength, the rest stay white; everything goes grey when Wi-Fi is off."""

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
        import math
        if not self.state:
            return
        radio_on, connected, level = self.state
        self.drawer.clear(self.background or self.bar.background)
        ctx = self.drawer.ctx
        cx, cy = self.length / 2, self.bar.height / 2 + 6
        ctx.set_line_width(2)
        for i, r in enumerate((5, 9, 13), start=1):
            colour = dim if not radio_on else BLUE if connected and i <= level else fg
            self.drawer.set_source_rgb(colour)
            ctx.new_path()
            ctx.arc(cx, cy, r, -3 * math.pi / 4, -math.pi / 4)
            ctx.stroke()
        self.drawer.set_source_rgb(dim if not radio_on else BLUE if connected else fg)
        ctx.new_path()
        ctx.arc(cx, cy, 1.8, 0, 2 * math.pi)
        ctx.fill()
        self.drawer.draw(offsetx=self.offsetx, offsety=self.offsety, width=self.length)


def bt_on():
    """Bluetooth counts as on when its radio isn't blocked (reads sysfs, no programs started)."""
    import glob
    found = False
    for t in glob.glob("/sys/class/rfkill/*/type"):
        try:
            if open(t).read().strip() == "bluetooth":
                found = True
                d = t[:-4]
                if open(d + "soft").read().strip() == "1" or open(d + "hard").read().strip() == "1":
                    return False
        except OSError:
            pass
    return found


def bt_icon():
    colour = BLUE if bt_on() else fg
    return f'<span foreground="{colour}">\uf293</span>'


def menu(name):
    return lazy.spawn([os.path.expanduser("~/qtile/menu.sh"), name])


@hook.subscribe.client_managed
def place_powermenu(c):
    # put the bar pop-up menus just under the bar, in the top-right corner
    if {"powermenu", "wifimenu", "btmenu"} & set(c.get_wm_class() or []):
        scr = qtile.current_screen
        w, h = (c.width or 240), (c.height or 120)
        c.place(scr.x + scr.width - w - 6, scr.y + 36, w, h, 0, "#7fa38a", above=True)

@hook.subscribe.startup_once
def autostart():
    subprocess.Popen(["lxpolkit"])
    subprocess.Popen(["swaybg", "-c", "#1f1a1a"])
    subprocess.Popen([os.path.expanduser("~/.config/qtile/autostart.sh")])
# ---- custom keybindings ----
keys.extend([
    # Apps
    Key([mod], "b", lazy.spawn("brave-browser --ozone-platform=wayland"), desc="Launch Brave"),

    # dwm-style habits
    #Key([mod, "shift"], "q", lazy.window.kill(), desc="Close window"),

    # Laptop media keys
    Key([], "XF86AudioRaiseVolume", lazy.spawn("wpctl set-volume -l 1.0 @DEFAULT_AUDIO_SINK@ 5%+")),
    Key([], "XF86AudioLowerVolume", lazy.spawn("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-")),
    Key([], "XF86AudioMute", lazy.spawn("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle")),
    Key([], "XF86MonBrightnessUp", lazy.spawn("brightnessctl set 5%+")),
    Key([], "XF86MonBrightnessDown", lazy.spawn("brightnessctl set 5%-")),
])

# ---- custom look ----
bg, fg, dim, accent = "#1a1f1c", "#d5ddd7", "#6f7d74", "#7fa38a"

widget_defaults = dict(font="JetBrainsMono Nerd Font", fontsize=15, padding=6, foreground=fg)
extension_defaults = widget_defaults.copy()

layouts = [
    layout.Columns(margin=8, border_width=2, border_focus=accent, border_normal=bg),
    layout.Max(),
]

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
                widget.StatusNotifier(icon_size=16, padding=4),  # tray icons (Wayland-compatible)
                widget.DF(visible_on_warn=False, format="disk {r:.0f}%", fontsize=13),
                widget.Sep(linewidth=1, padding=8, size_percent=50, foreground=dim),
                widget.Volume(fmt="vol {}", fontsize=13),
                widget.Sep(linewidth=1, padding=8, size_percent=50, foreground=dim),
                widget.Memory(format="mem {MemPercent:.0f}%", fontsize=13),
                widget.Sep(linewidth=1, padding=8, size_percent=50, foreground=dim),
                widget.CPU(format="cpu {load_percent:.0f}%", fontsize=13),
                widget.Sep(linewidth=2, padding=10, size_percent=60, foreground=accent),
                widget.Battery(update_interval=1, fontsize=13, format="bat {char}{percent:2.0%}", charge_char="\uf0e7 ", discharge_char="", full_char="\uf00c ", empty_char="", unknown_char="", low_percentage=0.2, low_foreground="#c47a74"),
                widget.GenPollText(func=bt_icon, update_interval=1, fontsize=18, padding=8, mouse_callbacks={"Button1": menu("btmenu")}),
                WifiArcs(mouse_callbacks={"Button1": menu("wifimenu")}),
                widget.TextBox("⏻", fontsize=18, mouse_callbacks={"Button1": lazy.spawn(os.path.expanduser("~/qtile/powermenu.sh"))}),
            ],
            24,
            background="#1e3527",  # dark green bar
            margin=[6, 6, 0, 6],
        ),
    ),
]

# ---- second screen (TV) ----
keys.extend([
    Key([mod], "o", lazy.next_screen(), desc="Focus next screen"),
    Key([mod, "shift"], "o", lazy.window.toscreen(1), desc="Send window to screen 2"),
])
keys.extend([
    Key([mod, "shift"], "i", lazy.window.toscreen(0), desc="Window to laptop"),
])
screens.append(Screen())
