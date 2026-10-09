# qtile-mini: the smallest useful Qtile (X11).
# Goal: when nothing is open it uses almost no RAM or CPU.
#  - no polling widgets: the bar is workspaces + a clock that updates once a minute
#  - no compositor, wallpaper daemon, notification daemon or autostart programs
#  - only the two layouts and the keys you actually need
# Super is the main key (set MOD=mod1 in the environment to use Alt instead, e.g. in a VM or browser).
import os

from libqtile import bar, layout, widget
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.lazy import lazy

bg, fg, dim, accent, BAR_BG = "#1a1f1c", "#d5ddd7", "#6f7d74", "#7fa38a", "#1e3527"
mod = os.environ.get("MOD", "mod4")
terminal = os.environ.get("TERMINAL", "xterm")

DIRS = (("h", "left"), ("l", "right"), ("j", "down"), ("k", "up"))
keys = [
    *[Key([mod], k, getattr(lazy.layout, d)()) for k, d in DIRS],
    *[Key([mod, "shift"], k, getattr(lazy.layout, f"shuffle_{d}")()) for k, d in DIRS],
    *[Key([mod, "control"], k, getattr(lazy.layout, f"grow_{d}")()) for k, d in DIRS],
    Key([mod], "space", lazy.layout.next()),
    Key([mod], "Tab", lazy.next_layout()),
    Key([mod], "q", lazy.window.kill()),
    Key([mod], "f", lazy.window.toggle_fullscreen()),
    Key([mod], "t", lazy.window.toggle_floating()),
    Key([mod], "x", lazy.spawn(terminal)),
    Key([mod, "control"], "r", lazy.reload_config()),
    Key([mod, "control"], "q", lazy.shutdown()),
]
groups = [Group(i) for i in "123456789"]
for g in groups:
    keys += [
        Key([mod], g.name, lazy.group[g.name].toscreen()),
        Key([mod, "shift"], g.name, lazy.window.togroup(g.name, switch_group=True)),
    ]

mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

layouts = [
    layout.Columns(margin=8, border_width=2, border_focus=accent, border_normal=bg),
    layout.Max(),
]
floating_layout = layout.Floating(float_rules=[*layout.Floating.default_float_rules, Match(title="pinentry")])

widget_defaults = dict(font="sans", fontsize=13, foreground=fg)
screens = [Screen(top=bar.Bar([
    widget.GroupBox(highlight_method="line", this_current_screen_border=accent, active=fg,
                    inactive=dim, disable_drag=True, padding=4),
    widget.Spacer(),
    widget.Clock(format="%a %b %d  %H:%M", update_interval=60),
    widget.Spacer(),
], 26, background=BAR_BG))]

reconfigure_screens = False
auto_minimize = False
wmname = "qtile"
