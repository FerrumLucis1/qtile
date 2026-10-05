#!/usr/bin/env python3
"""Super+/ cheat sheet: every key binding with its description, grouped by section.
Qtile writes the list (from the live config) to $XDG_RUNTIME_DIR/qtile-keys.json
just before opening this, so it is always up to date."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Gtk, Popup  # noqa: E402

DATA = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "qtile-keys.json")


def load() -> dict[str, list[tuple[str, str]]]:
    try:
        with open(DATA) as f:
            rows = json.load(f)
    except (OSError, ValueError):
        return {}
    sections: dict[str, list[tuple[str, str]]] = {}
    for r in rows:
        sections.setdefault(r["section"], []).append((r["keys"], r["desc"]))
    return sections


class CheatSheet(Popup):
    def __init__(self) -> None:
        super().__init__("cheatsheet", 560)
        self.add_label("Keyboard shortcuts  ·  Esc to close", dim=False)
        self.add_sep()
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(560)
        grid = Gtk.Grid(column_spacing=24, row_spacing=4)
        grid.set_margin_start(14)
        grid.set_margin_end(14)
        grid.set_margin_bottom(10)
        row = 0
        for name, items in load().items():
            head = Gtk.Label(label=name, xalign=0)
            head.get_style_context().add_class("dim")
            head.set_margin_top(10)
            grid.attach(head, 0, row, 2, 1)
            row += 1
            for keys, desc in items:
                k = Gtk.Label(label=keys, xalign=0)
                k.set_markup(f"<b>{keys.replace('&', '&amp;').replace('<', '&lt;')}</b>")
                grid.attach(k, 0, row, 1, 1)
                grid.attach(Gtk.Label(label=desc, xalign=0), 1, row, 1, 1)
                row += 1
        if row == 0:
            grid.attach(Gtk.Label(label="No shortcuts found - press Super+/ from Qtile"), 0, 0, 2, 1)
        scroll.add(grid)
        self.box.pack_start(scroll, True, True, 0)


if __name__ == "__main__":
    CheatSheet().run()
