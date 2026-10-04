#!/usr/bin/env python3
"""Volume menu: level slider, mute switch, and the list of outputs (click to switch).
Uses wpctl (PipeWire/WirePlumber)."""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from popup import Popup  # noqa: E402

CHECK = ""
SINK = "@DEFAULT_AUDIO_SINK@"


def wpctl(*args):
    try:
        return subprocess.run(["wpctl", *args], capture_output=True, text=True, timeout=2).stdout
    except Exception:
        return ""


def volume():
    out = wpctl("get-volume", SINK)
    try:
        return round(float(out.split()[1]) * 100), "MUTED" in out
    except (IndexError, ValueError):
        return 0, False


def outputs(status=None):
    """[(id, name, is_default)] for the Audio > Sinks section of `wpctl status`."""
    status = status if status is not None else wpctl("status")
    sinks, section, in_audio = [], None, False
    for raw in status.splitlines():
        line = re.sub(r"[│├└─]", " ", raw).rstrip()
        if not line.strip():
            continue
        if not raw.startswith((" ", "│", "├", "└")):  # top-level heading: Audio / Video / Settings
            in_audio = line.strip() == "Audio"
            section = None
            continue
        m = re.match(r"^\s*(\w[\w ]*):$", line)
        if m:
            section = m.group(1).strip()
            continue
        if in_audio and section == "Sinks":
            m = re.match(r"^\s*(\*)?\s*(\d+)\.\s+(.+?)(\s+\[.*\])?$", line)
            if m:
                sinks.append((m.group(2), m.group(3).strip(), bool(m.group(1))))
    return sinks


def refresh_bar():
    subprocess.Popen(["qtile", "cmd-obj", "-o", "widget", "volicon", "-f", "refresh"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class VolMenu(Popup):
    def __init__(self):
        super().__init__("volmenu", 280)
        vol, muted = volume()
        self.add_label("Volume", dim=False)
        self.add_slider(vol, self.set_volume)
        self.add_switch("Mute", muted, self.set_mute)
        self.add_sep()
        self.add_label("Output")
        sinks = outputs()
        if not sinks:
            self.add_label("No outputs found")
        for sid, name, default in sinks:
            self.add_item(f"{CHECK if default else ' '} {name}", lambda i=sid: self.pick(i))

    def set_volume(self, pct):
        wpctl("set-volume", SINK, f"{pct}%")
        refresh_bar()

    def set_mute(self, on):
        wpctl("set-mute", SINK, "1" if on else "0")
        refresh_bar()

    def pick(self, sid):
        wpctl("set-default", sid)
        refresh_bar()
        self.destroy()


if __name__ == "__main__":
    VolMenu().run()
