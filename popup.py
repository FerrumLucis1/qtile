"""Shared base for the bar's GTK pop-up menus (Wi-Fi, Bluetooth).
Closes on Esc, on click-away (focus loss), or after an action."""
import os
import shlex
import subprocess
import sys

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
"""


def notify(title, body=""):
    return shlex.join(["notify-send", "-a", "network", title, body])


def run_bg(cmd):
    """Run a shell command in the background, detached from the menu."""
    subprocess.Popen(["sh", "-c", cmd], start_new_session=True)


def relaunch_cmd(*args):
    """Shell snippet that reopens the current menu script."""
    return shlex.join([sys.executable, os.path.abspath(sys.argv[0]), *args])


class Popup(Gtk.Window):
    def __init__(self, name, width=240):
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
    def add_switch(self, text, state, on_toggle):
        row = Gtk.Box(spacing=12)
        row.get_style_context().add_class("header")
        lbl = Gtk.Label(label=text, xalign=0)
        row.pack_start(lbl, True, True, 0)
        sw = Gtk.Switch(active=state)
        sw.connect("notify::active", lambda s, _p: on_toggle(s.get_active()))
        row.pack_end(sw, False, False, 0)
        self.box.pack_start(row, False, False, 0)

    def add_sep(self):
        self.box.pack_start(Gtk.Separator(), False, False, 0)

    def add_label(self, text, dim=True):
        lbl = Gtk.Label(label=text, xalign=0)
        lbl.set_margin_start(14)
        lbl.set_margin_top(6)
        lbl.set_margin_bottom(6)
        if dim:
            lbl.get_style_context().add_class("dim")
        self.box.pack_start(lbl, False, False, 0)

    def add_item(self, text, callback, dim=False):
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

    def add_entry(self, placeholder, on_submit, secret=True):
        e = Gtk.Entry(placeholder_text=placeholder, visibility=not secret)
        e.connect("activate", lambda w: on_submit(w.get_text()))
        self.box.pack_start(e, False, False, 0)
        GLib.idle_add(e.grab_focus)

    # --- behaviour ---
    def _arm(self):
        self._armed = True
        return False

    def _on_active(self, *_):
        if self._armed and not self.is_active():
            self.destroy()

    def _on_key(self, _w, ev):
        if ev.keyval == 65307:  # Escape
            self.destroy()

    def run(self):
        self.show_all()
        Gtk.main()
