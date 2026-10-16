# Controller profiles

A profile tells the renderer two things:
- how a controller's buttons group into callout boxes;
- optionally, where each box's leader line lands on a photo.

Profiles live in `assets/profiles/` (bundled) or `<output folder>/profiles/` (user's own, which take
priority when the ids match). Use the bundled ones as worked examples: `xbox-360-controller.json` is the
simplest.

## Format

```json
{
  "id": "virpil-constellation-alpha-prime-right",
  "name": "Virpil Constellation Alpha Prime (Right)",
  "short": "Right stick",
  "suggested_device_ids": ["3344025A"],
  "notes": "Anything future editors should know (button numbering source, firmware profile...)",
  "photo": {
    "file": "alpha-prime-right.png",
    "image_size": [1200, 1200],
    "source_url": "https://.../image.png",
    "page_url": "https://.../product-page",
    "credit": "Photo: Virpil product image",
    "licence": "Virpil product photo",
    "crop": [100, 50, 1100, 1150],
    "blank": [[0, 0, 200, 120]]
  },
  "modifier_names": {"Joy_5": "pinky"},
  "implicit_modifiers": {"Joy_2": ["Joy_1"]},
  "show_unbound": true,
  "controls": [
    {"id": "A1", "title": "A1  Ministick", "short": "A1", "dot": [283, 125], "side": "left",
     "rows": [["up", "Pos_Joy_RYAxis"], ["right", "Pos_Joy_RXAxis"], ["down", "Neg_Joy_RYAxis"], ["left", "Neg_Joy_RXAxis"]]},
    {"id": "HAT1", "title": "Hat 1", "short": "Hat 1", "dot": [330, 160],
     "rows": [["up", "Joy_POV1Up"], ["right", "Joy_POV1Right"], ["down", "Joy_POV1Down"], ["left", "Joy_POV1Left"], ["push", "Joy_10"]]},
    {"id": "FACE", "title": "Face buttons", "dot": [[1500, 465], [1690, 400]], "side": "right",
     "rows": [["A", "GamePad_FaceDown"], ["B", "GamePad_FaceRight"]]},
    {"id": "AXES", "title": "Axes", "rows": [["X", "Joy_XAxis"], ["Y", "Joy_YAxis"], ["Twist", "Joy_RZAxis"]]}
  ]
}
```

### Top-level fields

- **`photo` coordinates.** `crop`, `blank` and every `dot` are pixels in the **original** image of size
  `image_size`. If the downloaded file has a different resolution, everything is scaled automatically.
  `blank` paints white rectangles, e.g. over a logo. Leave `photo` out entirely for a boxes-only profile
  that still groups controls nicely.
- **`modifier_names`.** How a modifier is named in "◆ hold …" lines. Without it, the name comes from the
  control's `short` (plus the glyph when the control has several rows).
- **`implicit_modifiers`.** `{key: [modifier keys to ignore]}` for hardware that always reports one
  button with another, such as two-stage triggers.
- **`show_unbound`.** When true (the default for profiles), unbound rows show "–" so free buttons are
  visible. Generic layouts hide them.

### Control fields

- **`rows`.** Each row is `[glyph, Elite key]`. Glyph tokens `up`, `right`, `down`, `left` and `push`
  become arrows and a dot. Anything else is printed as is: a button number, `F1`, `LB`, `half`...
- **`dot`.** One `[x, y]`, or a list of them, which draws one line per point (as with the face buttons).
  Leave it out for boxes with no leader line, such as axes. These are placed in whichever column has room.
- **`side`.** `left` or `right`. The default is the side of the photo the first dot is on. Override it
  when lines would cross the photo.

### Elite key names

| control | key name |
|---|---|
| Buttons | `Joy_1` … `Joy_128` |
| Hats | `Joy_POV1Up` / `Right` / `Down` / `Left` (POV1–POV4) |
| Axes | `Joy_XAxis`, `Joy_YAxis`, `Joy_ZAxis`, `Joy_RXAxis`, `Joy_RYAxis`, `Joy_RZAxis`, `Joy_UAxis`, `Joy_VAxis` |
| Half-axes used as buttons | `Pos_Joy_RYAxis` / `Neg_…` |
| Gamepad | `GamePad_FaceDown` (A), `FaceRight` (B), `FaceLeft` (X), `FaceUp` (Y), `DPadUp`…, `LBumper`, `RBumper`, `LThumb`, `RThumb`, `Back`, `Start`, `Pos_GamePad_LTrigger`, `GamePad_LStickX`, `Neg_GamePad_LStickY`… |

To see exactly which keys a user has bound on a device, run `make_sheets.py build --device <id>` without a
profile. The generic sheet shows every bound key. You can also read the `.binds` XML directly.

## Making one: the procedure that works

1. **Identify the controls.** Prefer the manufacturer's own button-layout sheet or manual. VKB, Virpil
   and Thrustmaster publish them, and they show which number each physical button sends. Also check
   Elite's `DeviceButtonMaps/<id>.buttonMap`, which often has the maker's labels (e.g. `A3 [ps4PadU]`).
   Programmable devices (VKB, Virpil) can be reconfigured, so if the user has customised their firmware,
   ask, or have them press buttons in the game's controls screen.
2. **Get a photo.** It needs a clean, front-ish, white-background product shot where the buttons are
   visible. Check the store's product JSON (Shopify stores expose `/products/<handle>.json` with full-size
   image URLs) or Wikimedia Commons. Record where it came from (`source_url`, `page_url`) and a `credit`
   line in the profile.
3. **Grid it.** Run `make_sheets.py grid img/photo.png --step 50` (use `--step 25` and a crop for small
   grips), then view the grid image and read off the coordinates of each control. Zoom into the head of
   the grip with a cropped grid if the hats are small.
4. **Write the JSON.**
   - Group controls the way a player thinks of them: each hat or ministick is one box, plus trigger(s),
     base buttons, encoders and an axes box.
   - Give every box a short name for modifier text.
   - Order doesn't matter: boxes are sorted by dot height within each column.
5. **Build with `--preview` and look.** Check that every dot sits on its control, that lines don't cross
   the photo (flip `side` if they do), that there's no red "Not on this sheet" line, and that text isn't
   tiny. If a column is too tall, move a box to the other side. As a last resort, boxes spill onto a
   continuation page.
