#!/usr/bin/env python3
"""Display menu (Super+P): choose which side of the laptop each external monitor
sits on, or turn it off. Choices are remembered per monitor in
~/.config/qtile/displays.json and re-applied automatically when it is plugged in.

    displaymenu.py           open the menu
    displaymenu.py --apply   apply saved positions now (used by Qtile on hotplug)

Uses wlr-randr."""
import json
import os
import subprocess
import sys
from functools import partial
from typing import Any

SAVE = os.path.expanduser("~/.config/qtile/displays.json")
SIDES = ("left", "right", "above", "below")
CHECK = ""


def outputs() -> list[dict[str, Any]]:
    try:
        out = subprocess.run(["wlr-randr", "--json"], capture_output=True, text=True, timeout=3).stdout
        data: list[dict[str, Any]] = json.loads(out)
        return data
    except Exception:
        return []


def is_laptop(o: dict[str, Any]) -> bool:
    return str(o.get("name", "")).startswith(("eDP", "LVDS"))


def key(o: dict[str, Any]) -> str:
    """Stable name for a monitor, so the choice follows it between ports."""
    label = f"{o.get('make') or ''} {o.get('model') or ''}".strip()
    return label or str(o.get("name"))


def size(o: dict[str, Any]) -> tuple[int, int]:
    """Logical size (after scale and rotation)."""
    mode = next((m for m in o.get("modes", []) if m.get("current")), None)
    if not mode:
        return 0, 0
    scale = float(o.get("scale") or 1)
    w, h = int(mode["width"] / scale), int(mode["height"] / scale)
    if str(o.get("transform", "normal")).endswith(("90", "270")):
        w, h = h, w
    return w, h


def load() -> dict[str, str]:
    try:
        with open(SAVE) as f:
            data: dict[str, str] = json.load(f)
            return data
    except (OSError, ValueError):
        return {}


def save(choices: dict[str, str]) -> None:
    os.makedirs(os.path.dirname(SAVE), exist_ok=True)
    with open(SAVE, "w") as f:
        json.dump(choices, f, indent=2)


def apply(choices: dict[str, str] | None = None) -> None:
    """Place every enabled external monitor on its saved side (default: right)."""
    choices = load() if choices is None else choices
    outs = outputs()
    laptop = next((o for o in outs if is_laptop(o)), None)
    if laptop is None:
        return
    cmd = ["wlr-randr"]
    lw, lh = size(laptop)
    placed: list[tuple[dict[str, Any], str, int, int]] = []
    for o in outs:
        if o is laptop or not o.get("enabled"):
            continue
        if choices.get(key(o)) == "off":
            cmd += ["--output", str(o["name"]), "--off"]
            continue
        w, h = size(o)
        placed.append((o, choices.get(key(o), "right"), w, h))
    # wlroots wants non-negative coordinates, so the laptop shifts right/down
    # to make room for monitors placed to its left or above it
    lx = max((w for _, side, w, _ in placed if side == "left"), default=0)
    ly = max((h for _, side, _, h in placed if side == "above"), default=0)
    cmd += ["--output", str(laptop["name"]), "--pos", f"{lx},{ly}"]
    for o, side, w, h in placed:
        x, y = {
            "left": (lx - w, ly),
            "above": (lx, ly - h),
            "below": (lx, ly + lh),
        }.get(side, (lx + lw, ly))
        cmd += ["--output", str(o["name"]), "--pos", f"{x},{y}"]
    if len(cmd) > 1:
        subprocess.run(cmd, timeout=5)


def turn_on(name: str) -> None:
    subprocess.run(["wlr-randr", "--output", name, "--on"], timeout=5)


def main_menu() -> None:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from popup import Popup

    class DisplayMenu(Popup):
        def __init__(self) -> None:
            super().__init__("displaymenu", 280)
            self.choices = load()
            externals = [o for o in outputs() if not is_laptop(o)]
            if not externals:
                self.add_label("No external monitor connected")
                return
            for o in externals:
                name = key(o)
                current = "off" if not o.get("enabled") else self.choices.get(name, "right")
                self.add_label(f"{name}  ({o.get('name')})", dim=False)
                for side in SIDES:
                    mark = CHECK if current == side else " "
                    self.add_item(f"{mark} {side.capitalize()} of laptop",
                                  partial(self.pick, o, side))
                self.add_item(f"{CHECK if current == 'off' else ' '} Off", partial(self.pick, o, "off"))
                self.add_sep()

        def pick(self, o: dict[str, Any], side: str) -> None:
            self.choices[key(o)] = side
            save(self.choices)
            if side != "off" and not o.get("enabled"):
                turn_on(str(o["name"]))
            apply(self.choices)
            self.destroy()

    DisplayMenu().run()


if __name__ == "__main__":
    if "--apply" in sys.argv:
        apply()
    else:
        main_menu()
