"""Read Elite Dangerous binding presets and the per-device button maps the game ships."""
import glob, os, re
import xml.etree.ElementTree as ET
from collections import Counter

from ed_actions import friendly, PRESET_SLOT

SLOT_NAMES = ["General", "Ship", "SRV", "On foot"]
NOT_CONTROLLERS = {"Keyboard", "Mouse", "{NoDevice}", ""}


def bindings_dir(override=None):
    """Locate the Bindings folder (Windows, or Steam Proton on Linux)."""
    if override:  # an explicit location is never silently swapped for a default one
        if os.path.isdir(override):
            return override
        raise SystemExit(f"BINDINGS_NOT_FOUND: {override} is not a folder.")
    cands = []
    if os.environ.get("LOCALAPPDATA"):
        cands.append(os.path.join(os.environ["LOCALAPPDATA"], "Frontier Developments", "Elite Dangerous",
                                  "Options", "Bindings"))
    home = os.path.expanduser("~")
    for steam in (".steam/steam", ".local/share/Steam", ".var/app/com.valvesoftware.Steam/.local/share/Steam"):
        cands.append(os.path.join(home, steam, "steamapps/compatdata/359320/pfx/drive_c/users/steamuser",
                                  "AppData/Local/Frontier Developments/Elite Dangerous/Options/Bindings"))
    for c in cands:
        if c and os.path.isdir(c):
            return c
    raise SystemExit("BINDINGS_NOT_FOUND: could not find the Elite Dangerous Bindings folder. Pass "
                     "--bindings-dir or set \"bindings_dir\" in ed-sheets.json. Tried: " + "; ".join(c for c in cands if c))


def _version(path):
    m = re.search(r"\.(\d+)\.(\d+)\.binds$", path)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def preset_file(bdir, name, major=4):
    """Newest <name>.<major>.<minor>.binds for a preset name (or a direct path)."""
    if name.endswith(".binds") and os.path.isfile(name):
        return name
    if name.endswith(".binds"):
        p = os.path.join(bdir, name)
        if os.path.isfile(p):
            return p
    files = [f for f in glob.glob(os.path.join(bdir, glob.escape(name) + ".*.binds"))
             if _version(f)[0] == major]
    if not files:
        raise SystemExit(f"No {name}.{major}.x.binds file in {bdir}")
    return max(files, key=_version)


def active_presets(bdir):
    """The four preset names from StartPreset.4.start (General, Ship, SRV, On foot).

    Older or hand-written files may hold a single line; it then applies to every slot."""
    p = os.path.join(bdir, "StartPreset.4.start")
    if not os.path.isfile(p):
        p = os.path.join(bdir, "StartPreset.start")
    lines = [l.strip() for l in open(p, encoding="utf-8-sig").read().splitlines() if l.strip()]
    if not lines:
        raise SystemExit(f"{p} is empty")
    return (lines + [lines[-1]] * 4)[:4]


def _parse(path):
    root = ET.parse(path).getroot()
    out = []
    for el in root:
        inv, tog = el.find("Inverted"), el.find("ToggleOn")
        for slot in el:
            if slot.tag not in ("Primary", "Secondary", "Binding"):
                continue
            dev, key = slot.get("Device"), slot.get("Key")
            if not dev or dev == "{NoDevice}" or not key:
                continue
            out.append(dict(action=el.tag, device=dev, key=key,
                            mods=[(m.get("Device"), m.get("Key")) for m in slot.findall("Modifier")],
                            axis=slot.tag == "Binding",
                            inverted=inv is not None and inv.get("Value") == "1",
                            toggle=None if tog is None else tog.get("Value") == "1"))
    return out


def load_bindings(bdir, preset=None):
    """All bindings in effect. Returns (bindings, description of sources).

    With per-mode presets (StartPreset.4.start lines differ) each action is taken from the
    preset for its mode, mirroring what the game does."""
    if preset:
        f = preset_file(bdir, preset)
        return _parse(f), [os.path.basename(f)]
    names = active_presets(bdir)
    files = {n: preset_file(bdir, n) for n in set(names)}
    parsed = {n: _parse(f) for n, f in files.items()}
    if len(files) == 1:
        n = names[0]
        return parsed[n], [os.path.basename(files[n])]
    out = []
    for n, binds in parsed.items():
        for b in binds:
            slot = PRESET_SLOT.get(friendly(b["action"])[0], 0)
            if names[slot] == n:
                out.append(b)
    src = []
    for n in dict.fromkeys(names):  # group slots that share a preset
        slots = "/".join(SLOT_NAMES[i] for i, m in enumerate(names) if m == n)
        src.append(f"{os.path.basename(files[n])} ({slots})")
    return out, src


def devices_in(binds):
    """Controller device ids with the number of bindings on each, most-used first."""
    c = Counter(b["device"] for b in binds if b["device"] not in NOT_CONTROLLERS)
    return c.most_common()


_DIR_TOKENS = {"U": "Up", "R": "Right", "D": "Down", "L": "Left"}


def clean_label(text):
    """'RGNX A1 [ps4PadU]' -> 'A1 Up'; drops Elite's glyph tokens like [x52prox]."""
    text = re.sub(r"\[[a-z0-9]*Pad([URDL])\]", lambda m: _DIR_TOKENS[m.group(1)], text)
    text = re.sub(r"\s*\[[^\]]*\]", "", text)
    text = re.sub(r"^[LR]GNX\b\s*", "", text)  # VKB maps prefix every label with the device
    return text.strip()


def button_map(bdir, dev):
    """(device name, {key: label}) from DeviceButtonMaps/<dev>.buttonMap, if Elite ships one."""
    if dev == "GamePad":
        return "Gamepad", {}
    p = os.path.join(bdir, "DeviceButtonMaps", f"{dev}.buttonMap")
    if not os.path.isfile(p):
        return dev, {}
    raw = open(p, encoding="utf-8-sig", errors="replace").read()
    m = re.search(r"<!--(.*?)-->", raw, re.S)
    name = dev
    if m:
        first = [l.strip() for l in m.group(1).strip().splitlines() if l.strip()]
        if first:
            name = first[0]
    labels = {}
    for k, v in re.findall(r"<(\w+)>([^<]*)</\1>", raw):
        if k != "Root":
            labels[k] = clean_label(v)
    return name, labels
