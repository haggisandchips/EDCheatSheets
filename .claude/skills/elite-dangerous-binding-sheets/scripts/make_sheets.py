"""Elite Dangerous binding cheat sheets.

  python make_sheets.py list   [--out DIR] [--preset NAME] [--json]   devices, modes bound on each, profile/photo status
  python make_sheets.py build  [--out DIR] [--device ID ...] [--style visual|table|both] [--preview]
  python make_sheets.py grid   IMAGE [--step 50] [--scale 0.6]  photo with a pixel grid, for placing callout dots

Settings live in DIR/ed-sheets.json (see references/config.md); everything has a sensible default.
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter  # noqa: E402
from ed_binds import bindings_dir, load_bindings, devices_in, button_map, active_presets  # noqa: E402
from ed_actions import friendly, CTX_ORDER  # noqa: E402
from ed_profiles import pick_profile, normalise, generic_profile  # noqa: E402
import render  # noqa: E402

DEFAULT_PAGES = [
    {"title": "Flight – ship, combat, panels & scanners", "contexts": ["SHIP", "UI", "FSS", "DSS", "MC"]},
    {"title": "SRV & on foot", "contexts": ["SRV", "FOOT"]},
    {"title": "Maps, cameras, colony & Holo-Me", "contexts": ["MAP", "CAM", "COL", "STORE"]},
]


def load_config(out):
    p = os.path.join(out, "ed-sheets.json")
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


def resolve(dev, binds, bdir, out, cfg):
    dcfg = cfg.get("devices", {}).get(dev, {})
    name, labels = button_map(bdir, dev)
    prof = pick_profile(dev, out, dcfg)
    prof = normalise(prof) if prof else generic_profile(dev, dcfg.get("name", name), labels, binds)
    if dcfg.get("name"):
        prof["name"] = dcfg["name"]
    return dcfg, prof, labels


def photo_file(prof, out):
    ph = prof.get("photo")
    if not ph:
        return None, None
    p = os.path.join(out, "img", ph["file"])
    if os.path.isfile(p):
        return p, None
    return None, f"photo {ph['file']} not found in {os.path.join(out, 'img')} (source: {ph.get('source_url')})"


def safe(name):
    return "".join(ch for ch in name if ch not in '<>:"/\\|?*').strip()


def survey(a):
    """Everything a setup conversation needs, in one structure."""
    cfg = load_config(a.out)
    bdir = bindings_dir(a.bindings_dir or cfg.get("bindings_dir"))
    binds, src = load_bindings(bdir, a.preset or cfg.get("preset"))
    try:
        presets = active_presets(bdir)
    except SystemExit:
        presets = []
    devices = []
    for dev, n in devices_in(binds):
        dcfg, prof, _ = resolve(dev, binds, bdir, a.out, cfg)
        ph, warn = photo_file(prof, a.out)
        ctx = Counter(friendly(b["action"])[0] for b in binds if b["device"] == dev)
        devices.append(dict(
            id=dev, bindings=n, elite_name=button_map(bdir, dev)[0], sheet_name=prof["name"],
            profile=None if prof.get("generic") else prof["id"],
            photo=None if prof.get("generic") or not prof.get("photo") else
            dict(file=prof["photo"]["file"], present=bool(ph), source_url=prof["photo"].get("source_url"),
                 page_url=prof["photo"].get("page_url"), licence=prof["photo"].get("licence")),
            modes={c: ctx[c] for c in CTX_ORDER if ctx[c]},
            configured=dev in cfg.get("devices", {}), skip=bool(dcfg.get("skip"))))
    return dict(bindings_dir=bdir, preset_files=src, start_presets=presets,
                per_mode_presets=len(set(presets)) > 1, config_exists=bool(cfg), devices=devices)


def cmd_list(a):
    s = survey(a)
    if a.json:
        print(json.dumps(s, indent=1, ensure_ascii=False))
        return
    print("Bindings folder:", s["bindings_dir"])
    print("Preset files:   ", "; ".join(s["preset_files"]))
    print("Settings file:  ", "ed-sheets.json found" if s["config_exists"] else "none (defaults)")
    for d in s["devices"]:
        kind = f"profile {d['profile']}" if d["profile"] else "generic layout (no profile)"
        if d["photo"]:
            kind += " + photo" if d["photo"]["present"] else f" (photo {d['photo']['file']} missing)"
        skip = "  [skipped in config]" if d["skip"] else ""
        modes = ", ".join(f"{c} {n}" for c, n in d["modes"].items())
        print(f"  {d['id']:<14} {d['bindings']:>4} bindings  {d['elite_name']}  ->  {kind}{skip}")
        print(f"  {'':<14}      modes: {modes}")


def cmd_build(a):
    cfg = load_config(a.out)
    bdir = bindings_dir(a.bindings_dir or cfg.get("bindings_dir"))
    binds, src = load_bindings(bdir, a.preset or cfg.get("preset"))
    os.makedirs(a.out, exist_ok=True)
    devs = [d for d, _ in devices_in(binds)]
    if a.device:
        missing = set(a.device) - set(devs)
        if missing:
            sys.exit(f"No bindings for {', '.join(missing)}. Devices in use: {', '.join(devs)}")
        devs = a.device
    render.Fonts.setup()
    names = {}
    resolved = {}
    for dev in [d for d, _ in devices_in(binds)]:
        resolved[dev] = resolve(dev, binds, bdir, a.out, cfg)
        names[dev] = resolved[dev][1].get("short", resolved[dev][1]["name"])
    made = []
    for dev in devs:
        dcfg, prof, labels = resolved[dev]
        if dcfg.get("skip") and not a.device:
            continue
        merged = {"drop": dcfg.get("drop", cfg.get("drop", []))}
        sheet = render.Sheet(dev, prof, labels, binds, binds, names, merged)
        styles = (a.style or dcfg.get("style") or cfg.get("style") or "visual")
        styles = ["visual", "table"] if styles == "both" else [styles]
        base = safe(dcfg.get("file") or prof["name"])
        for st in styles:
            if st == "visual":
                path = os.path.join(a.out, base + ".pdf")
                ph, warn = photo_file(prof, a.out)
                if warn:
                    print("  note:", warn, "- drawing boxes without a photo")
                pages = dcfg.get("pages") or cfg.get("pages") or DEFAULT_PAGES
                titles = render.render_visual(sheet, pages, src, path, ph)
                print(f"{path}  ({len(titles)} page(s): {', '.join(titles)})")
            else:
                path = os.path.join(a.out, base + " (text).pdf")
                render.render_table(sheet, src, path)
                print(path)
            made.append(path)
    if a.preview:
        preview(made, a.out)


def preview(paths, out):
    """PNG snapshots of every page, so the layout can be checked without opening a PDF viewer."""
    try:
        import pypdfium2 as pdfium
    except ImportError:
        print("pip install pypdfium2 for --preview")
        return
    d = os.path.join(out, "_preview")
    os.makedirs(d, exist_ok=True)
    for p in paths:
        doc = pdfium.PdfDocument(p)
        for i in range(len(doc)):
            png = os.path.join(d, f"{os.path.splitext(os.path.basename(p))[0]} p{i + 1}.png")
            doc[i].render(scale=2).to_pil().save(png)
            print("preview:", png)
        doc.close()


def cmd_grid(a):
    from PIL import Image, ImageDraw
    im = Image.open(a.image).convert("RGB")
    s = a.scale
    g = im.resize((int(im.width * s), int(im.height * s)))
    d = ImageDraw.Draw(g)
    for v in range(0, im.width, a.step):
        d.line([v * s, 0, v * s, g.height], fill=(0, 160, 255))
        d.text((v * s + 2, 2), str(v), fill=(255, 0, 0))
    for v in range(0, im.height, a.step):
        d.line([0, v * s, g.width, v * s], fill=(0, 160, 255))
        d.text((2, v * s + 2), str(v), fill=(255, 0, 0))
    out = a.output or os.path.splitext(a.image)[0] + "_grid.png"
    g.save(out)
    print(out, "- grid labels are original-image pixels; image size", im.size)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("list", "build"):
        p = sub.add_parser(name)
        p.add_argument("--out", default=os.getcwd(), help="output folder (holds ed-sheets.json, img/, profiles/)")
        p.add_argument("--preset", help="preset name or .binds path (default: what the game loads)")
        p.add_argument("--bindings-dir")
        if name == "list":
            p.add_argument("--json", action="store_true", help="machine-readable survey")
        if name == "build":
            p.add_argument("--device", nargs="*", help="only these device ids")
            p.add_argument("--style", choices=["visual", "table", "both"])
            p.add_argument("--preview", action="store_true")
    g = sub.add_parser("grid")
    g.add_argument("image")
    g.add_argument("--step", type=int, default=50)
    g.add_argument("--scale", type=float, default=0.6)
    g.add_argument("--output")
    a = ap.parse_args()
    if getattr(a, "out", None):
        a.out = os.path.abspath(a.out)
    {"list": cmd_list, "build": cmd_build, "grid": cmd_grid}[a.cmd](a)


if __name__ == "__main__":
    main()
