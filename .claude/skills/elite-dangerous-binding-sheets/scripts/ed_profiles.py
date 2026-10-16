"""Controller profiles: how a device's controls are grouped into callout boxes, and (optionally)
which photo to draw them around. Curated profiles are JSON files; any device without one gets a
generic profile built from the bindings and Elite's own button map."""
import glob, json, os, re

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLED = os.path.join(SKILL_DIR, "assets", "profiles")
GLYPHS = {"up": "↑", "right": "→", "down": "↓", "left": "←", "push": "●"}
POV_DIRS = [("Up", "up"), ("Right", "right"), ("Down", "down"), ("Left", "left")]


def _load(path):
    with open(path, encoding="utf-8") as f:
        p = json.load(f)
    p["_path"] = path
    return p


def all_profiles(workspace):
    """Workspace profiles override bundled ones with the same id."""
    found = {}
    for d in (BUNDLED, os.path.join(workspace, "profiles")):
        for f in sorted(glob.glob(os.path.join(d, "*.json"))):
            p = _load(f)
            found[p["id"]] = p
    return found


def pick_profile(dev, workspace, dev_cfg):
    profiles = all_profiles(workspace)
    pid = dev_cfg.get("profile")
    if pid:
        if pid not in profiles:
            raise SystemExit(f"Profile '{pid}' (configured for {dev}) not found. Known: {', '.join(profiles)}")
        return profiles[pid]
    matches = [p for p in profiles.values() if dev in p.get("suggested_device_ids", [])]
    return matches[0] if matches else None


def normalise(profile):
    """Turn glyph tokens into symbols and controls into a uniform list of dicts."""
    controls = []
    for c in profile["controls"]:
        rows = [(GLYPHS.get(g, g), k) for g, k in c["rows"]]
        dots = c.get("dot")
        if dots and not isinstance(dots[0], list):
            dots = [dots]
        controls.append(dict(id=c["id"], title=c["title"], short=c.get("short", c["title"]), rows=rows,
                             dots=dots or [], side=c.get("side")))
    out = dict(profile)
    out["controls"] = controls
    out.setdefault("show_unbound", True)
    return out


def _num(k):
    m = re.search(r"(\d+)", k)
    return int(m.group(1)) if m else 0


def generic_profile(dev, dev_name, labels, binds):
    """Group every control this device has bindings on: axes, hats, axis-as-button, buttons."""
    keys = {b["key"] for b in binds if b["device"] == dev}
    keys |= {k for b in binds for d, k in b["mods"] if d == dev}
    controls = []

    def lab(k, default):
        return labels.get(k) or default

    axes = sorted(k for k in keys if re.fullmatch(r"Joy_\w*Axis", k))
    if axes:
        controls.append(dict(id="AXES", title="Axes", short="Axis",
                             rows=[(lab(k, k[4:].replace("Axis", " axis")), k) for k in axes], dots=[]))
    povs = sorted({int(m.group(1)) for k in keys for m in [re.fullmatch(r"Joy_POV(\d)\w+", k)] if m})
    for n in povs:
        name = re.sub(r"\s*(Up|Down|Left|Right)$", "", lab(f"Joy_POV{n}Up", "")) or f"Hat {n}"
        controls.append(dict(id=f"POV{n}", title=f"{name}" if name.startswith("Hat") else f"Hat {name}",
                             short=name, rows=[(GLYPHS[g], f"Joy_POV{n}{d}") for d, g in POV_DIRS], dots=[]))
    half = sorted((k for k in keys if re.fullmatch(r"(Pos|Neg)_Joy_\w+Axis", k)), key=lambda k: (k[4:], k))
    if half:
        rows = []
        for k in half:
            base = k[4:]
            rows.append((("+ " if k.startswith("Pos") else "− ") + lab(base, base[4:].replace("Axis", "")), k))
        controls.append(dict(id="HALFAXES", title="Axes used as buttons", short="Axis", rows=rows, dots=[]))
    buttons = sorted((k for k in keys if re.fullmatch(r"Joy_\d+", k)), key=_num)
    for i in range(0, len(buttons), 8):
        chunk = buttons[i:i + 8]
        rows = [(str(_num(k)), k) for k in chunk]
        controls.append(dict(id=f"BTN{i}", title=f"Buttons {_num(chunk[0])}–{_num(chunk[-1])}",
                             short="Button", rows=rows, dots=[], row_notes={k: labels.get(k, "") for k in chunk}))
    other = sorted(keys - set(axes) - set(half) - set(buttons) - {k for k in keys if k.startswith("Joy_POV")})
    if other:
        controls.append(dict(id="OTHER", title="Other", short="", rows=[(k, k) for k in other], dots=[]))
    return dict(id=f"generic-{dev}", name=dev_name, short=dev_name, controls=controls,
                show_unbound=False, generic=True)


def modifier_label(profile, key, labels):
    """Short name for a modifier key, e.g. 'D1' or 'D-pad ↑'."""
    names = profile.get("modifier_names", {})
    if key in names:
        return names[key]
    for c in profile["controls"]:
        for g, k in c["rows"]:
            if k == key:
                if len(c["rows"]) == 1:
                    return c["short"]
                if profile.get("generic") and c["short"] == "Button":
                    return f"button {g}" + (f" ({labels[key]})" if labels.get(key) else "")
                return f"{c['short']} {g}".strip()
    return labels.get(key) or key.replace("Joy_", "button ")
