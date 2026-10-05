#!/usr/bin/env python3
"""Power menu: small GTK window with Shutdown / Sleep / Log out.
Add an item by adding one line to ITEMS. Closes on Esc, on click-away, or after picking."""
import os
import subprocess
import sys
from typing import Any

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

ITEMS = [
    ("Lock", [os.path.join(os.path.dirname(os.path.realpath(__file__)), "lock.sh")]),
    ("Shutdown", ["systemctl", "poweroff"]),
    ("Sleep", ["systemctl", "suspend"]),
    ("Log out", ["qtile", "cmd-obj", "-o", "cmd", "-f", "shutdown"]),
]

CSS = b"""
window { background-color: #1a1f1c; border: 2px solid #7fa38a; border-radius: 8px; }
button { background: #1a1f1c; color: #d5ddd7; border: none; border-radius: 0;
         padding: 8px 16px; font-family: "JetBrainsMono Nerd Font"; font-size: 14px; }
button:hover { background: #7fa38a; color: #1a1f1c; }
"""

GLib.set_prgname("powermenu")  # becomes the window's app_id, which Qtile matches on


class Menu(Gtk.Window):
    def __init__(self) -> None:
        super().__init__(title="powermenu")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(170, -1)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(box)
        for label, cmd in ITEMS:
            b = Gtk.Button(label=label)
            b.set_relief(Gtk.ReliefStyle.NONE)
            b.connect("clicked", self.run, cmd)
            box.pack_start(b, True, True, 0)
        prov = Gtk.CssProvider()
        prov.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            self.get_screen(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        self.connect("key-press-event", self.on_key)
        self.connect("notify::is-active", self.on_active)
        self.connect("destroy", Gtk.main_quit)
        self.armed = False
        GLib.timeout_add(500, self.arm)  # ignore focus changes while the window is opening

    def arm(self) -> bool:
        self.armed = True
        return False

    def on_active(self, *_: Any) -> None:
        if self.armed and not self.is_active():
            self.destroy()

    def on_key(self, _w: Any, ev: Any) -> None:
        if ev.keyval == 65307:  # Escape
            self.destroy()

    def run(self, _b: Any, cmd: list[str]) -> None:
        subprocess.Popen(cmd)
        self.destroy()


Menu().show_all()
Gtk.main()
