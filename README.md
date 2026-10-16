# Elite Dangerous Bindings Cheat Sheets

A [Claude Code](https://claude.com/claude-code) skill that turns your Elite Dangerous control bindings into
printable PDF cheat sheets, one per controller.

- **Visual sheets:** a photo of the controller, with a callout box for each control showing what it does.
  There's one page per group of game modes (flight, SRV & on foot, cameras & colony...).
- **Text-only sheets** (optional): every binding on the controller, as a compact reference.
- **Combinations stand out.** A modifier button is labelled **MODIFIER** in blue, and anything that needs
  a modifier held first is marked `◆ hold D1: …` in orange.
- **Any controller works.** VKB, Virpil, Thrustmaster, Logitech/Saitek, Winwing, gamepads... Controllers
  without a photo profile get a clean boxes-only layout of everything you've bound.

The full instructions Claude follows are in the skill itself:
[`.claude/skills/elite-dangerous-binding-sheets/SKILL.md`](.claude/skills/elite-dangerous-binding-sheets/SKILL.md).

## Getting started

1. **Install the requirements.** You need Python 3, plus:

   ```bash
   pip install reportlab pillow pypdfium2
   ```

   (`pypdfium2` is only needed for layout previews.)
2. **Clone this repo** and open the folder in Claude Code. The skill lives in `.claude/skills/`, so Claude
   picks it up automatically whenever you work in this folder.
3. **Ask Claude:** "build my elite bindings".

The first time, Claude runs a short guided setup:
- finds your bindings (or asks where they are);
- asks which controllers to make sheets for;
- asks which game modes to include and how to group them into pages;
- asks whether you want graphical sheets, text-only sheets or both;
- fetches any controller photos the sheets need.

It saves your answers to `ed-sheets.json`, builds the PDFs into this folder and checks the layout. After
that, the same request offers to rebuild with your saved setup. You can also ask for changes directly,
e.g. "drop multicrew" or "also make text-only versions".

You can also run the script yourself:

```bash
python .claude/skills/elite-dangerous-binding-sheets/scripts/make_sheets.py list --out .
python .claude/skills/elite-dangerous-binding-sheets/scripts/make_sheets.py build --out .
python .claude/skills/elite-dangerous-binding-sheets/scripts/make_sheets.py build --out . --style both
```

## Doing it by hand (without Claude Code)

Everything Claude does is a plain Python script plus two JSON files, so you can do all of it yourself.
In the commands below, `SCRIPT` means `python .claude/skills/elite-dangerous-binding-sheets/scripts/make_sheets.py`,
run from the folder you want the PDFs and `img/` in (the `--out` folder, `.` here).

### 1. See what the script found

```bash
SCRIPT list --out .
SCRIPT list --out . --json      # same, machine-readable
```

This shows the bindings folder and preset files in use, then each controller with:

- its **device id** (a USB VID+PID such as `231D0200`, or a name such as `GamePad` or `SaitekX52Pro`);
- how many bindings it has, and how many are in each **mode**;
- which profile it will use, and whether that profile's photo is in `img/`.

Keyboard and mouse are ignored. If it can't find your bindings folder, pass `--bindings-dir <path>`. To
use one preset for every mode instead of what the game loads, pass `--preset "<name or .binds path>"`.

### 2. Choose modes and pages in `ed-sheets.json`

Create `ed-sheets.json` in the output folder. Every key is optional; the full format is in
[`references/config.md`](.claude/skills/elite-dangerous-binding-sheets/references/config.md). Every binding
belongs to one **mode** (called a context in the config):

| Code | Covers | Code | Covers |
|---|---|---|---|
| `SHIP` | flight, combat, targeting, pips, cockpit | `SRV` | driving the SRV |
| `UI` | menu and panel navigation | `FOOT` | on foot (Odyssey) |
| `FSS` | system scanner | `MAP` | galaxy and system map |
| `DSS` | surface scanner | `CAM` | ship and free cameras |
| `MC` | multicrew | `COL` | colonisation |
| `STORE` | store preview and Holo-Me | | |

`drop` lists modes to leave out entirely. `pages` lists the printed pages, and each page lists the modes it
shows. A page with nothing bound for a controller is skipped for that controller.

```json
{
  "style": "visual",
  "drop": ["MC", "MAP", "STORE"],
  "pages": [
    {"title": "Flight – ship, menus, FSS & DSS", "contexts": ["SHIP", "UI", "FSS", "DSS"]},
    {"title": "SRV & on foot", "contexts": ["SRV", "FOOT"]},
    {"title": "Cameras & colony", "contexts": ["CAM", "COL"]}
  ],
  "devices": {
    "GamePad": {"drop": ["CAM", "COL"], "file": "Xbox pad"}
  }
}
```

Anything under `devices.<device id>` overrides the top-level key of the same name for that controller.
`style` is `visual` (photo with callouts), `table` (text-only, every binding) or `both`. Save the file as
UTF-8, or characters such as the en dash in titles come out garbled.

### 3. Build

```bash
SCRIPT build --out .                        # everything
SCRIPT build --out . --device GamePad       # one controller
SCRIPT build --out . --preview              # also writes PNGs to _preview/ to check the layout
```

A controller with no profile still gets a clean boxes-only sheet labelled from Elite's own button names,
so you only need to write a profile if you want the photo.

### 4. Write a profile for your own controller (to get the photo)

A profile is a JSON file in `profiles/<id>.json` in your output folder (it takes priority over the bundled
ones in `assets/profiles/`). It groups a controller's buttons into named callout boxes and says where each
box's leader line lands on the photo. Start by copying
[`xbox-360-controller.json`](.claude/skills/elite-dangerous-binding-sheets/assets/profiles/xbox-360-controller.json),
the simplest example. The field reference is in
[`references/profiles.md`](.claude/skills/elite-dangerous-binding-sheets/references/profiles.md).

1. **Get a photo.** A clear, front-on product shot with the buttons visible works best. Save it in `img/`
   and note where it came from (`source_url`, `page_url`, `credit`) in the profile.
2. **Find out which key each physical control sends.** Elite names them `Joy_1` to `Joy_128` for buttons,
   `Joy_POV1Up`/`Right`/`Down`/`Left` for hats, `Joy_XAxis`, `Joy_YAxis`, `Joy_ZAxis`, `Joy_RXAxis`,
   `Joy_RYAxis`, `Joy_RZAxis`, `Joy_UAxis`, `Joy_VAxis` for axes, and `Pos_`/`Neg_` in front of an axis
   name when half an axis is used as a button. For gamepads they are `GamePad_FaceDown` (A), `FaceRight` (B),
   `FaceLeft` (X), `FaceUp` (Y), `DPadUp` and so on. Ways to work out the numbers:
   - Run `build` for that controller without a profile. The boxes-only sheet shows every key you've bound.
   - Look in `...\Options\Bindings\DeviceButtonMaps\<device id>.buttonMap` for the maker's own labels.
   - Press each control in the game's controls screen, or in Windows Game Controllers (`joy.cpl`, then
     Properties), and write down the number it shows. Numbering can differ by one between tools.
   - Use the manufacturer's button-layout sheet or manual if it publishes one. Programmable sticks (VKB,
     Virpil) can be reconfigured, so check against your own firmware setup.
3. **Find pixel positions on the photo.**

   ```bash
   SCRIPT grid img/photo.png --step 50           # use --step 25 for a small image
   ```

   This writes `img/photo_grid.png`, the photo with labelled grid lines. The labels are pixels in the
   **original** image, so read coordinates from the labels, not from your screen (a zoomed image will
   mislead you). Note an `[x, y]` for each control.
4. **Write the JSON.** One entry in `controls` per callout box, with a `dot` on its control and a `rows`
   list of `[label, Elite key]` pairs:

   ```json
   {
     "id": "my-stick",
     "name": "My Stick",
     "short": "Stick",
     "suggested_device_ids": ["SaitekX52Pro"],
     "photo": {"file": "my-stick.jpg", "image_size": [1024, 576],
               "source_url": "https://...", "page_url": "https://...", "credit": "Photo: ..."},
     "controls": [
       {"id": "TRIG", "title": "Trigger", "short": "Trigger", "dot": [668, 215], "side": "right",
        "rows": [["half", "Joy_1"], ["full", "Joy_15"]]},
       {"id": "HAT", "title": "Hat", "dot": [665, 90], "side": "right",
        "rows": [["up", "Joy_POV1Up"], ["right", "Joy_POV1Right"], ["down", "Joy_POV1Down"], ["left", "Joy_POV1Left"]]},
       {"id": "AXES", "title": "Axes", "rows": [["X", "Joy_XAxis"], ["Y", "Joy_YAxis"]]}
     ]
   }
   ```

   Tips:
   - Give every control you've bound a box, or the sheet shows a red "Not on this sheet" line.
   - `dot` can be a list of `[x, y]` points, which draws one line per point (for a group of face buttons).
     Leave it out for boxes with no leader line, such as axes.
   - `side` (`left` or `right`) picks the column the box sits in. Flip it if lines cross the photo.
   - `suggested_device_ids` makes the profile apply to that device id automatically. Otherwise map it in
     `ed-sheets.json` with `"devices": {"<id>": {"profile": "my-stick"}}`.
   - `modifier_names` and `implicit_modifiers` are optional; see `references/profiles.md`.
5. **Build with `--preview` and look at the PNGs.** Check that each dot sits on its control, that nothing
   overlaps and that the text isn't tiny. Adjust the coordinates, rebuild, and repeat until it looks right.

### 5. Controller photos and device ids

- Photos go in `img/` under the file name the profile gives. A profile with no photo present is drawn as
  boxes only.
- Programmable sticks such as VKB and Virpil can report different ids depending on how they're configured.
  If a sheet shows the wrong controller, run `list` and map the id explicitly in `ed-sheets.json` with
  `devices.<id>.profile` (and a readable `name`).
- To share a profile, copy it into `assets/profiles/`.

## What you should know

- **Which bindings are used.** The skill reads what the game actually loads: `StartPreset.4.start` in
  `%LOCALAPPDATA%\Frontier Developments\Elite Dangerous\Options\Bindings`. That file can name a different
  preset for General, Ship, SRV and On-foot controls, and the skill reads each mode from its own preset.
  If your on-foot binds look wrong, check that file. Linux/Proton installs are found automatically.
- **Your preferences live in `ed-sheets.json`.** It holds page groupings, game modes to leave out, file
  names and which profile each controller uses. Ask Claude to change things and it updates this file, so
  the next regeneration repeats them. It's personal, so it isn't tracked in git: a fresh clone starts
  with the defaults. [`ed-sheets.example.json`](ed-sheets.example.json) is a working example (two VKB
  sticks and an Xbox pad); the script never reads it. The format is documented in
  [`references/config.md`](.claude/skills/elite-dangerous-binding-sheets/references/config.md).
- **Controller profiles.** A profile (`assets/profiles/*.json`) lists a controller's controls and where
  they sit on its photo. Included are the VKB Gladiator NXT EVO SCG Premium Right, the VKB Gladiator NXT
  EVO Omni Throttle SCG Left and the Xbox 360 controller (fine for any Xbox-style pad). Claude can make a
  profile for your own controller; see
  [`references/profiles.md`](.claude/skills/elite-dangerous-binding-sheets/references/profiles.md).
- **Check your device ids.** Elite identifies controllers by USB id. Programmable sticks such as VKB and
  Virpil can report different ids depending on how they're configured. If a sheet shows the wrong
  controller, run `list` and map the id to the right profile in `ed-sheets.json`.

## Photos and copyright

Controller photos go in the `img/` folder. Each profile records where its photo comes from (`source_url`
and `page_url`). When a photo is missing, Claude downloads it into your local `img/` folder.

- **What this repo includes.** The only photo here is the Xbox 360 controller, a public-domain image by
  Evan-Amos on
  [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Xbox-360-Controller-Black.jpg).
- **What it leaves out.** Manufacturer product photos are proprietary: the VKB images belong to VKB-Sim,
  and the same goes for Virpil, Thrustmaster and other brands. So this repo doesn't include them. Its
  `.gitignore` excludes the VKB photos (`img/GNE_*.png`) and all generated PDFs, which embed whichever
  photos were used.
- **Your clone is yours.** What you do with photos in your own copy is up to you.
- **Pull requests.** If a pull request adds images, I'll decide whether they can stay or need removing.
- **No photo still works.** A sheet without its photo is still built, as boxes only.

## Repository layout

```
.claude/skills/elite-dangerous-binding-sheets/   the skill (SKILL.md, scripts, profiles, reference docs)
img/                                             controller photos (manufacturer photos not committed)
ed-sheets.example.json                           example sheet settings (your own ed-sheets.json is not committed)
*.pdf                                            generated sheets (not committed)
```
