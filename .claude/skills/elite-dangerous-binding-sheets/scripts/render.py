"""PDF renderers: 'visual' (photo with callout boxes, one page per group of game modes) and
'table' (text-only reference listing every binding)."""
import datetime, os
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from ed_actions import friendly, CTX, CTX_ORDER
from ed_profiles import modifier_label

INK = colors.HexColor("#1b1f24")
MUTED = colors.HexColor("#5b6470")
HEAD_BG = colors.HexColor("#23282f")
RULE = colors.HexColor("#d5d9df")
LINE = colors.HexColor("#d0312d")
GLYPH_BG = colors.HexColor("#eef0f3")
MOD_INK, ORANGE, RED = "#1a5fb4", "#b35c00", "#b3261e"
ARROWS = ("\u2191", "\u2192", "\u2193", "\u2190", "\u25CF")
SHORT = {"Shutdown field neutraliser": "Field neutraliser", "Select target ahead": "Target ahead",
         "Toggle scanned-area view": "Scanned-area view"}


# ------------------------------------------------------------------ fonts
class Fonts:
    """Arial + Segoe UI Symbol on Windows, DejaVu on Linux, Arial on macOS; else Helvetica + ASCII."""
    R, B, SYM = "Helvetica", "Helvetica-Bold", "Helvetica-Bold"
    ascii = True

    @classmethod
    def setup(cls):
        win = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
        sets = [
            (os.path.join(win, "arial.ttf"), os.path.join(win, "arialbd.ttf"), os.path.join(win, "seguisym.ttf")),
            ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            ("/usr/share/fonts/TTF/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
             "/usr/share/fonts/TTF/DejaVuSans.ttf"),
            ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        ]
        for r, b, s in sets:
            if all(os.path.isfile(p) for p in (r, b, s)):
                pdfmetrics.registerFont(TTFont("SheetR", r))
                pdfmetrics.registerFont(TTFont("SheetB", b))
                pdfmetrics.registerFont(TTFont("SheetSym", s))
                cls.R, cls.B, cls.SYM, cls.ascii = "SheetR", "SheetB", "SheetSym", False
                return

    @classmethod
    def g(cls, ch):
        """A glyph, falling back to ASCII when no Unicode font is available."""
        if not cls.ascii:
            return ch
        return {"\u2191": "^", "\u2192": ">", "\u2193": "v", "\u2190": "<", "\u25CF": "o",
                "\u25C6": "*", "\u2013": "-", "\u2212": "-", "\u00B7": "-"}.get(ch, ch)

    @classmethod
    def sym(cls, ch):
        return f'<font name="{cls.SYM}">{cls.g(ch)}</font>'

    @classmethod
    def text(cls, s):
        """Wrap arrow / diamond characters in the symbol font inside Paragraph markup."""
        out = []
        for ch in s:
            out.append(cls.sym(ch) if ch in ARROWS + ("\u25C6",) else ch)
        return "".join(out)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------------ binding text
def strip_prefix(name):
    for pre in ("Free cam move ", "Free cam ", "Placement cam "):
        if name.startswith(pre):
            rest = name[len(pre):]
            return rest[0].upper() + rest[1:]
    return name


class Sheet:
    """Everything one device's PDF needs: profile, bindings and naming helpers."""

    def __init__(self, dev, profile, labels, binds, all_binds, device_names, cfg):
        self.dev, self.profile, self.labels, self.cfg = dev, profile, labels, cfg
        self.device_names = device_names  # dev id -> short name, for cross-device modifiers
        implicit = profile.get("implicit_modifiers", {})
        drop = set(cfg.get("drop", []))

        def fix(b):
            # e.g. VKB two-stage trigger: stage 2 implies stage 1 is held; Elite records that as a
            # modifier, but physically it is just a full pull, so hide it.
            if b["device"] == dev and b["key"] in implicit:
                b = dict(b, mods=[m for m in b["mods"] if not (m[0] == dev and m[1] in implicit[b["key"]])])
            return b
        self.all = [fix(b) for b in all_binds if friendly(b["action"])[0] not in drop]
        self.mine = [b for b in self.all if b["device"] == dev]

    def mod_name(self, d, k):
        if d == self.dev:
            return modifier_label(self.profile, k, self.labels)
        return f"{self.device_names.get(d, d)} {k.replace('Joy_', 'button ')}"

    def line(self, b, tagged):
        ctx, name = friendly(b["action"])
        name = SHORT.get(name, name)
        if ctx in ("CAM", "COL") and ctx in tagged:
            name = strip_prefix(name)
        if ctx == "UI" and ctx in tagged and name.startswith("UI "):
            name = name[3:4].upper() + name[4:]
        extra = []
        if b["axis"] and b["inverted"]:
            extra.append("inverted")
        if b["toggle"] is False:
            extra.append("hold")
        elif b["toggle"]:
            extra.append("toggle")
        name = esc(name)
        if extra:
            name += f' <font color="#5b6470" size="6.3">({", ".join(extra)})</font>'
        tag = ""
        if ctx in tagged:
            tag = f'<font name="{Fonts.B}" size="5.6" color="{CTX[ctx][1]}">{CTX[ctx][0]}</font> '
        if b["mods"]:
            held = " + ".join(Fonts.text(esc(self.mod_name(d, k))) for d, k in b["mods"])
            return f'<font name="{Fonts.B}" color="{ORANGE}">{Fonts.sym(chr(0x25C6))} hold {held}:</font> {tag}{name}'
        return tag + name

    def cell(self, key, binds, tagged, modifiers, note=""):
        out, seen = [], set()
        if key in modifiers:
            out.append(f'<font name="{Fonts.B}" color="{MOD_INK}">MODIFIER</font> '
                       f'<font color="#5b6470">{Fonts.g(chr(0x2013))} hold for the {Fonts.sym(chr(0x25C6))} combos</font>')
        if note:
            out.append(f'<font color="#5b6470">[{esc(note)}]</font>')
        for b in sorted(binds, key=lambda b: bool(b["mods"])):
            l = self.line(b, tagged)
            if l not in seen:
                seen.add(l)
                out.append(l)
        return "<br/>".join(out)


# ------------------------------------------------------------------ callout box
class Box:
    def __init__(self, control, rows, width, size):
        self.c, self.key, self.title, self.width, self.size = control, control["id"], control["title"], width, size
        st = ParagraphStyle("r", fontName=Fonts.R, fontSize=size, leading=size * 1.18, textColor=INK)
        self.gw = max([25] + [pdfmetrics.stringWidth(Fonts.g(g), Fonts.B, size - 0.6) + 8
                              for g, _ in rows if g not in ARROWS])
        self.rows = []
        for glyph, html in rows:
            p = Paragraph(html or f'<font color="#aab1ba">{Fonts.g(chr(0x2013))}</font>', st)
            _, h = p.wrap(width - self.gw - 5, 1000)
            self.rows.append((glyph, p, max(h + 3.2, size * 1.18 + 3.2)))
        self.head_h = size + 6
        self.height = self.head_h + sum(r[2] for r in self.rows)

    def draw(self, c, x, y_top):
        self.x, self.y_top = x, y_top
        w, gw = self.width, self.gw
        c.setFillColor(HEAD_BG)
        c.roundRect(x, y_top - self.head_h, w, self.head_h, 2, stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont(Fonts.B, self.size + 0.6)
        c.drawString(x + 5, y_top - self.head_h + 3.6, self.title)
        y = y_top - self.head_h
        for glyph, p, h in self.rows:
            c.setFillColor(GLYPH_BG)
            c.rect(x, y - h, gw, h, stroke=0, fill=1)
            c.setFillColor(INK)
            arrow = glyph in ARROWS or glyph == "◆"
            c.setFont(Fonts.SYM if arrow else Fonts.B, self.size + (1.6 if arrow else -0.6))
            c.drawCentredString(x + gw / 2, y - h / 2 - self.size * 0.35, Fonts.g(glyph))
            p.drawOn(c, x + gw + 3, y - h + 1.6)
            c.setStrokeColor(RULE)
            c.setLineWidth(0.4)
            c.line(x, y - h, x + w, y - h)
            y -= h
        c.setStrokeColor(colors.HexColor("#9aa3ad"))
        c.setLineWidth(0.6)
        c.rect(x, y_top - self.height, w, self.height, stroke=1, fill=0)

    def anchor(self, side):
        return (self.x + (self.width if side == "left" else 0), self.y_top - self.head_h / 2)


# ------------------------------------------------------------------ page furniture
def header(c, W, H, sheet, title, src, margin=16):
    top = H - margin
    c.setFillColor(INK)
    c.setFont(Fonts.B, 15)
    c.drawString(margin, top - 14, sheet.profile["name"])
    c.setFont(Fonts.R, 9.5)
    c.setFillColor(MUTED)
    c.drawString(margin, top - 28, f"Elite Dangerous  {Fonts.g(chr(0xB7))}  {title}")
    c.setFillColor(colors.HexColor("#1f5fa8"))
    c.setFont(Fonts.B, 9.5)
    c.drawRightString(W - margin, top - 14, title.upper())
    c.setFont(Fonts.R, 7)
    c.setFillColor(MUTED)
    c.drawRightString(W - margin, top - 26, "Bindings: " + "; ".join(src))
    lx, ly = W - margin, top - 40
    for ink, txt in ((MOD_INK, "MODIFIER \u2013 hold it first"),
                     (ORANGE, "\u25C6 combination (hold modifier, then press)")):
        txt = "".join(Fonts.g(ch) for ch in txt)
        tw = c.stringWidth(txt, Fonts.R, 7) + 14
        lx -= tw
        c.setStrokeColor(colors.HexColor("#c9ced6"))
        c.rect(lx, ly - 3, tw - 4, 11, stroke=1, fill=0)
        c.setFillColor(colors.HexColor(ink))
        x = lx + 4
        for ch in txt:
            f = Fonts.SYM if ch in ("\u25C6",) else Fonts.R
            c.setFont(f, 7)
            c.drawString(x, ly, ch)
            x += c.stringWidth(ch, f, 7)
        lx -= 4
    c.setFont(Fonts.R, 5.5)
    c.setFillColor(MUTED)
    c.drawRightString(W - margin, 6, f"Generated {datetime.date.today():%d %b %Y}")
    return top - 52


# ------------------------------------------------------------------ visual renderer
def _tagged(ctxs, cfg_page):
    if "tagged" in cfg_page:
        return set(cfg_page["tagged"])
    return {c for c in ctxs if c != "SHIP"}


def render_visual(sheet, pages, src, out_path, photo_path):
    """One page per entry in `pages` that has any bindings for this device."""
    W, H = landscape(A4)
    c = canvas.Canvas(out_path, pagesize=(W, H))
    c.setTitle(f"{sheet.profile['name']} - Elite Dangerous bindings")
    prof = sheet.profile
    photo = None
    if photo_path:
        from PIL import Image
        img = Image.open(photo_path).convert("RGB")
        ph = prof["photo"]
        sx = sy = 1.0
        if ph.get("image_size"):
            sx, sy = img.width / ph["image_size"][0], img.height / ph["image_size"][1]
        for x0, y0, x1, y1 in ph.get("blank", []):
            img.paste((255, 255, 255), (int(x0 * sx), int(y0 * sy), int(x1 * sx), int(y1 * sy)))
        crop = ph.get("crop") or [0, 0, ph.get("image_size", img.size)[0], ph.get("image_size", img.size)[1]]
        img = img.crop((int(crop[0] * sx), int(crop[1] * sy), int(crop[2] * sx), int(crop[3] * sy)))
        tmp = out_path + ".photo.jpg"
        img.save(tmp, quality=90)  # JPEG keeps the PDF small; product shots are photos anyway
        photo = (tmp, img.size, crop, sx, sy)
    made = []
    for page in pages:
        ctxs = set(page["contexts"])
        binds = [b for b in sheet.mine if friendly(b["action"])[0] in ctxs]
        if not binds:
            continue
        made.append(page["title"])
        tagged = _tagged(ctxs, page)
        page_all = [b for b in sheet.all if friendly(b["action"])[0] in ctxs]
        modifiers = {k for b in page_all for d, k in b["mods"] if d == sheet.dev}
        per_key = defaultdict(list)
        for b in binds:
            per_key[b["key"]].append(b)

        def rows_for(ctrl):
            rows = []
            notes = ctrl.get("row_notes", {})
            for glyph, k in ctrl["rows"]:
                html = sheet.cell(k, per_key.get(k, []), tagged, modifiers, notes.get(k, ""))
                if html or prof["show_unbound"]:
                    rows.append((glyph, html))
            return rows

        controls = [ct for ct in prof["controls"] if rows_for(ct) or ct["dots"]]
        _page(c, W, H, sheet, page["title"], src, controls, rows_for, photo, prof)
        known = {k for ct in prof["controls"] for _, k in ct["rows"]}
        missing = sorted(set(per_key) - known)
        if missing:
            c.setFont(Fonts.B, 6.5)
            c.setFillColor(colors.HexColor(RED))
            c.drawString(16, 8, "Not on this sheet: " + "; ".join(
                f"{k}: {friendly(per_key[k][0]['action'])[1]}" for k in missing))
        c.showPage()
    c.save()
    if photo:
        os.remove(photo[0])
    return made


def _page(c, W, H, sheet, title, src, controls, rows_for, photo, prof):
    margin, col_w, gap = 16, 236, 14
    body_top = header(c, W, H, sheet, title, src, margin)
    with_dots = [ct for ct in controls if ct["dots"]]
    if not photo or not with_dots:
        _flow(c, W, H, sheet, title, src, controls, rows_for, body_top, margin)
        return
    tmp, (iw, ih), crop, sx, sy = photo
    px0, px1 = margin + col_w + gap + 18, W - margin - col_w - gap - 18
    avail_w, avail_h = px1 - px0, body_top - margin - 24
    scale = min(avail_w / iw, avail_h / ih)
    dw, dh = iw * scale, ih * scale
    ix, iy = px0 + (avail_w - dw) / 2, margin + 16 + (avail_h - dh) / 2
    c.drawImage(tmp, ix, iy, dw, dh)

    def pts(ct):
        return [(ix + (x * sx - crop[0] * sx) * scale, iy + dh - (y * sy - crop[1] * sy) * scale) for x, y in ct["dots"]]

    mid = (px0 + px1) / 2
    side_of = {ct["id"]: ct.get("side") or ("left" if pts(ct)[0][0] < mid else "right") for ct in with_dots}
    free = [ct for ct in controls if not ct["dots"]]
    space = body_top - (margin + 10)
    overflow = []
    for size in (7.4, 7.0, 6.6, 6.2, 5.8, 5.4):
        cols = {}
        for side in ("left", "right"):
            cts = sorted((ct for ct in with_dots if side_of[ct["id"]] == side),
                         key=lambda ct: max(y for _, y in pts(ct)), reverse=True)
            cols[side] = [Box(ct, rows_for(ct), col_w, size) for ct in cts]
        for ct in free:  # boxes without a dot go wherever there is room
            short = min(cols, key=lambda s: sum(b.height + 4 for b in cols[s]))
            cols[short].append(Box(ct, rows_for(ct), col_w, size))
        if all(sum(b.height for b in bs) + 4 * (len(bs) - 1) <= space for bs in cols.values()):
            break
    else:  # still too tall at the smallest size: spill the bottom boxes onto a continuation page
        for side, bs in cols.items():
            while bs and sum(b.height for b in bs) + 4 * (len(bs) - 1) > space:
                overflow.insert(0, bs.pop().c)
    for side, bs in cols.items():
        x = margin if side == "left" else W - margin - col_w
        spacing = min(12, (space - sum(b.height for b in bs)) / max(1, len(bs) - 1))
        y = body_top
        for b in bs:
            b.draw(c, x, y)
            y -= b.height + spacing
    c.setStrokeColor(LINE)
    c.setLineWidth(0.8)
    for side, bs in cols.items():
        for b in bs:
            if not b.c["dots"]:
                continue
            ax, ay = b.anchor(side)
            elbow = ax + (10 if side == "left" else -10)
            for dx, dy in pts(b.c):
                p = c.beginPath()
                p.moveTo(ax, ay)
                p.lineTo(elbow, ay)
                p.lineTo(dx, dy)
                c.drawPath(p, stroke=1, fill=0)
    for side, bs in cols.items():
        for b in bs:
            for dx, dy in pts(b.c):
                c.setFillColor(LINE)
                c.setStrokeColor(colors.white)
                c.setLineWidth(1)
                c.circle(dx, dy, 2.6, stroke=1, fill=1)
    credit = prof.get("photo", {}).get("credit")
    if credit:
        c.setFont(Fonts.R, 5.5)
        c.setFillColor(MUTED)
        c.drawCentredString((px0 + px1) / 2, iy - 9, credit)
    if overflow:
        c.showPage()
        _flow(c, W, H, sheet, title + " (continued)", src, overflow, rows_for,
              header(c, W, H, sheet, title + " (continued)", src, margin), margin)


def _flow(c, W, H, sheet, title, src, controls, rows_for, body_top, margin, ncols=3, gap=12):
    """No photo: masonry of boxes in columns, continuing onto new pages as needed."""
    col_w = (W - 2 * margin - gap * (ncols - 1)) / ncols
    col, y = 0, body_top  # fill columns top-to-bottom, left-to-right, so reading order is kept
    for ct in controls:
        b = Box(ct, rows_for(ct), col_w, 7.2)
        if y - b.height < margin + 10 and y < body_top:
            col, y = col + 1, body_top
            if col == ncols:
                c.showPage()
                body_top = y = header(c, W, H, sheet, title + " (continued)", src, margin)
                col = 0
        b.draw(c, margin + col * (col_w + gap), y)
        y -= b.height + 10


# ------------------------------------------------------------------ table renderer
def render_table(sheet, src, out_path, ncols=3):
    """Text-only reference: every control with all its bindings across every mode."""
    W, H = landscape(A4)
    c = canvas.Canvas(out_path, pagesize=(W, H))
    c.setTitle(f"{sheet.profile['name']} - Elite Dangerous bindings (text)")
    prof = sheet.profile
    tagged = set(CTX_ORDER)
    modifiers = {k for b in sheet.all for d, k in b["mods"] if d == sheet.dev}
    per_key = defaultdict(list)
    for b in sheet.mine:
        per_key[b["key"]].append(b)
    combos = [b for b in sheet.mine if b["mods"]]
    combos += [b for b in sheet.all if b["device"] != sheet.dev and any(d == sheet.dev for d, _ in b["mods"])]

    def rows_for(ct):
        rows, unbound = [], []
        notes = ct.get("row_notes", {})
        for glyph, k in ct["rows"]:
            html = sheet.cell(k, per_key.get(k, []), tagged, modifiers, notes.get(k, ""))
            if html:
                rows.append((glyph, html))
            else:
                unbound.append(Fonts.g(glyph))
        if unbound and prof["show_unbound"]:
            rows.append(("free", f'<font color="#8a939e">{esc(", ".join(unbound))}</font>'))
        return rows

    margin = 16
    body_top = header(c, W, H, sheet, "All bindings (text)", src, margin)
    items = []
    if combos:
        lines = []
        for b in sorted(combos, key=lambda b: (b["mods"], b["key"])):
            seq = [sheet.mod_name(d, k) for d, k in b["mods"]] + [sheet.mod_name(b["device"], b["key"])]
            lines.append(("\u25C6", f'<font name="{Fonts.B}" color="{ORANGE}">'
                                    f'{" + ".join(Fonts.text(esc(s)) for s in seq)}</font> '
                                    f'= {sheet.line(dict(b, mods=[]), tagged)}'))
        items.append(dict(id="COMBOS", title="All combinations", rows=lines, dots=[], _rows=lines))
    for ct in prof["controls"]:
        r = rows_for(ct)
        if r:
            items.append(dict(ct, _rows=r))
    _flow(c, W, H, sheet, "All bindings (text)", src, items, lambda ct: ct["_rows"], body_top, margin,
          ncols=ncols)
    c.showPage()
    c.save()
