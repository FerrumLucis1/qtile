"""Shared base for the bar's GTK pop-up menus (Wi-Fi, Bluetooth).
Closes on Esc, on click-away (focus loss), or after an action."""
import os
import shlex
import subprocess
import sys
from collections.abc import Callable
from typing import Any

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk, Pango  # noqa: E402,F401

CSS = b"""
window { background-color: #1a1f1c; border: 2px solid #7fa38a; border-radius: 8px; }
* { font-family: "JetBrainsMono Nerd Font"; font-size: 13px; color: #d5ddd7; }
button { background: #1a1f1c; border: none; border-radius: 0; padding: 6px 14px; }
button:hover { background: #7fa38a; }
button:hover label { color: #1a1f1c; }
.header { padding: 8px 14px; }
.header label { font-weight: bold; }
.dim, .dim label { color: #6f7d74; }
separator { background: #2c3a31; min-height: 1px; }
entry { background: #232a26; border: 1px solid #7fa38a; margin: 6px 14px 10px 14px; padding: 4px; }
switch { background: #2c3a31; border: none; }
switch:checked { background: #7fa38a; }
switch slider { background: #d5ddd7; border: none; }
scale trough { background: #2c3a31; min-height: 6px; border-radius: 3px; border: none; }
scale highlight { background: #7fa38a; border-radius: 3px; }
scale slider { background: #d5ddd7; min-width: 14px; min-height: 14px; border-radius: 7px; border: none; }
scale value { color: #d5ddd7; }
"""


def notify(title: str, body: str = "") -> str:
    return shlex.join(["notify-send", "-a", "network", title, body])


def run_bg(cmd: str) -> None:
    """Run a shell command in the background, detached from the menu."""
    subprocess.Popen(["sh", "-c", cmd], start_new_session=True)


def relaunch_cmd(*args: str) -> str:
    """Shell snippet that reopens the current menu script."""
    return shlex.join([sys.executable, os.path.abspath(sys.argv[0]), *args])


class Popup(Gtk.Window):
    def __init__(self, name: str, width: int = 240) -> None:
        GLib.set_prgname(name)  # becomes the Wayland app_id that Qtile matches on
        super().__init__(title=name)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(width, -1)
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.box)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.connect("key-press-event", self._on_key)
        self.connect("notify::is-active", self._on_active)
        self.connect("destroy", Gtk.main_quit)
        self._armed = False
        GLib.timeout_add(500, self._arm)

    # --- building blocks ---
    def add_switch(self, text: str, state: bool, on_toggle: Callable[[bool], None]) -> None:
        row = Gtk.Box(spacing=12)
        row.get_style_context().add_class("header")
        lbl = Gtk.Label(label=text, xalign=0)
        row.pack_start(lbl, True, True, 0)
        sw = Gtk.Switch(active=state)
        sw.connect("notify::active", lambda s, _p: on_toggle(s.get_active()))
        row.pack_end(sw, False, False, 0)
        self.box.pack_start(row, False, False, 0)

    def add_sep(self) -> None:
        self.box.pack_start(Gtk.Separator(), False, False, 0)

    def add_label(self, text: str, dim: bool = True) -> None:
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.set_margin_start(14)
        lbl.set_margin_top(6)
        lbl.set_margin_bottom(6)
        if dim:
            lbl.get_style_context().add_class("dim")
        self.box.pack_start(lbl, False, False, 0)

    def add_item(self, text: str, callback: Callable[[], None], dim: bool = False) -> None:
        b = Gtk.Button()
        b.set_relief(Gtk.ReliefStyle.NONE)
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
        lbl.set_max_width_chars(28)
        b.add(lbl)
        if dim:
            b.get_style_context().add_class("dim")
        b.connect("clicked", lambda *_: callback())
        self.box.pack_start(b, False, False, 0)

    def add_slider(self, value: int, on_change: Callable[[int], None], lo: int = 0, hi: int = 100,
                   delay: int = 120) -> Any:
        """Horizontal slider; on_change(int) fires once dragging pauses for `delay` ms."""
        scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, lo, hi, 1)
        scale.set_value(value)
        scale.set_draw_value(True)
        scale.set_value_pos(Gtk.PositionType.RIGHT)
        scale.set_margin_start(14)
        scale.set_margin_end(14)
        pending: dict[str, int | None] = {"id": None}

        def fire() -> bool:
            pending["id"] = None
            on_change(int(scale.get_value()))
            return False

        def changed(_s: Any) -> None:
            if pending["id"]:
                GLib.source_remove(pending["id"])
            pending["id"] = GLib.timeout_add(delay, fire)

        scale.connect("value-changed", changed)
        self.box.pack_start(scale, False, False, 0)
        return scale

    def add_entry(self, placeholder: str, on_submit: Callable[[str], None], secret: bool = True) -> None:
        e = Gtk.Entry(placeholder_text=placeholder, visibility=not secret)
        e.connect("activate", lambda w: on_submit(w.get_text()))
        self.box.pack_start(e, False, False, 0)
        GLib.idle_add(e.grab_focus)

    # --- behaviour ---
    def _arm(self) -> bool:
        self._armed = True
        return False

    def _on_active(self, *_: Any) -> None:
        if self._armed and not self.is_active():
            self.destroy()

    def _on_key(self, _w: Any, ev: Any) -> None:
        if ev.keyval == 65307:  # Escape
            self.destroy()

    def run(self) -> None:
        self.show_all()
        Gtk.main()
