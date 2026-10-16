---
name: elite-dangerous-binding-sheets
description: Generate printable PDF cheat sheets of Elite Dangerous controller bindings. Visual sheets draw callout boxes around a photo of each joystick, throttle or gamepad, one page per group of game modes (flight, SRV and on foot, cameras...); text-only sheets list every binding. Combinations (hold a modifier then press) are clearly marked. Works for any HOTAS/HOSAS/gamepad Elite supports (VKB, Virpil, Thrustmaster, Logitech/Saitek, Winwing, Xbox...). Use whenever someone wants to see, print, share, document, refresh or regenerate their Elite Dangerous key bindings or controller layout, compare binds across devices, or find free/unused buttons, even if they don't say "cheat sheet" or "PDF".
---

# Elite Dangerous binding cheat sheets

`scripts/make_sheets.py` reads the bindings Elite actually loads and renders one PDF per controller. Your
job is mostly to run it, check the output and tailor the settings. You only write code if a new kind of
controller needs a photo profile, and even that is just a JSON file.

Requirements: Python 3 with `reportlab` and `pillow`, plus `pypdfium2` for the `--preview` PNGs used to
check layouts. If an import fails, offer to run `pip install reportlab pillow pypdfium2`.

## How it works (read this before running anything)

- **Where the bindings come from.** On Windows the files live in
  `%LOCALAPPDATA%\Frontier Developments\Elite Dangerous\Options\Bindings`. The script also tries Steam
  Proton paths on Linux, and `--bindings-dir` overrides the location.
  `StartPreset.4.start` holds four preset names, one per line: General, Ship, SRV, On foot. When the lines
  differ, each action is read from its own mode's preset, mirroring the game. Tell the user when that
  happens, because their on-foot binds can live in a different file from their flight binds. `--preset`
  forces a single preset instead.
- **Devices.** Elite identifies a device by its USB VID+PID (`231D0200` = VKB, `3344xxxx` = Virpil,
  `044Fxxxx` = Thrustmaster) or by a name (`T16000M`, `SaitekX52Pro`, `GamePad`). `make_sheets.py list`
  shows each device with its binding count, Elite's own name for it (from `DeviceButtonMaps`) and the
  profile it will use. Keyboard and mouse are ignored.
- **Profiles** (`assets/profiles/*.json`, or the user's `profiles/` folder, which takes priority).
  - A profile groups a controller's buttons into named callout boxes ("A3 Centre hat", "Face buttons") and
    can place them around a photo with leader lines.
  - A device with no profile still gets a clean **generic** sheet: boxes for axes, hats and buttons,
    labelled from Elite's button map, showing only the controls that are bound.
  - So the skill works for any controller straight away. A profile only adds the photo and nicer grouping.
  - Bundled profiles: VKB Gladiator NXT EVO SCG Premium Right, VKB Gladiator NXT EVO Omni Throttle SCG
    Left, Xbox 360 controller (also fine for any XInput pad).
- **Contexts.** Each binding is tagged SHIP, UI, FSS, DSS, MC (multicrew), SRV, FOOT, MAP, CAM, COL
  (colonisation) or STORE (Holo-Me). Pages are lists of contexts. `drop` removes contexts entirely.
  The catalogue is in `scripts/ed_actions.py`; unknown actions get a heuristic context and label.
- **Combinations.** A binding with modifiers is written `◆ hold D1: Hyperspace jump` in orange. The
  modifier button's own row starts with a blue **MODIFIER** line. A modifier on a *different* device is
  named with that device's short name. Some hardware reports implied modifiers (a VKB two-stage trigger's
  full pull always includes the half pull); profiles hide these via `implicit_modifiers`.

## Workflow: a short guided setup, then build

People usually just say "build my elite bindings". Treat that as the start of a short wizard. Find out
what you can yourself, then ask only what you can't infer. Use the AskUserQuestion tool when available
(2–4 options per question, multi-select for lists, up to 4 questions per call); otherwise ask in chat
with numbered options. Every question should have a recommended default so the user can just accept.

### 0. Output folder and returning users

- The output folder is the current project folder, unless the user names another (`--out`).
- **If `ed-sheets.json` exists**, the user has done the wizard before. Show a one-line summary of the
  saved setup (devices, page groups, style) and ask: rebuild as saved (recommended), change some
  settings, or start over. "Rebuild as saved" goes straight to step 6.
- `ed-sheets.example.json` is someone else's sample; never use it as the user's settings.

### 1. Find the bindings

Run `python <skill>/scripts/make_sheets.py list --out <folder> --json`. It returns:
- the bindings folder and the preset files in use;
- whether per-mode presets are in play;
- each controller's Elite name, binding count, bound **modes** with counts, profile and photo status.

If it fails with `BINDINGS_NOT_FOUND`, ask the user where their Elite Dangerous `Bindings` folder is
(typical locations: Windows `%LOCALAPPDATA%\Frontier Developments\Elite Dangerous\Options\Bindings`,
Linux/Proton under `steamapps/compatdata/359320/...`). Save the answer as `bindings_dir`.

If per-mode presets are in play, tell the user which file each mode comes from. If that looks wrong to
them, offer to pin one preset (`preset`).

### 2. Which controllers

This is its own question call. Do not combine it with the mode questions: the order is controllers, then
modes (step 3A), then grouping (step 3B), each asked only after the previous answer is in.

List the controllers found, by friendly name and binding count, and ask which to make sheets for.
Default: all of them. Mark unchosen ones `"skip": true`. If more than four devices were found, ask in
chat or group them, since the question tool only takes four options.

If a device's identity is unclear, ask what it is. This happens with a generic Elite name, two devices
of the same brand, or a VKB/Virpil id that matches a bundled profile which may be the wrong hand. Map
the answer to a profile with `devices.<id>.profile` and a readable `name`.

### 3. Modes and pages (visual sheets)

Two questions, in this order: **which modes do you use**, then **how should they be grouped**. Step A is a
checkbox form (AskUserQuestion, multi-select); step B is typed in chat because it needs free-form
brackets. Never ask for grouping before the modes are settled, and never ask about modes cold.

**Step A: which modes?** Show a table from the `list` output (mode, code, plain-English meaning, and
each chosen controller's binding count; only modes with at least one binding):

| Mode | Code | Covers | Xbox | Stick | Throttle |
|---|---|---|---|---|---|
| Ship | SHIP | flight, combat, targeting, pips, cockpit | 29 | 30 | 25 |
| Menus | UI | panel and menu navigation | 11 | 11 | 0 |
| FSS | FSS | system scanner | 12 | 7 | 0 |
| DSS | DSS | surface scanner | 0 | 8 | 0 |
| Multicrew | MC | multicrew roles | 0 | 5 | 0 |
| SRV | SRV | driving the SRV | 26 | 0 | 0 |
| On foot | FOOT | Odyssey on-foot | 30 | 0 | 0 |
| Maps | MAP | galaxy and system map | 10 | 0 | 0 |
| Cameras | CAM | ship and free cameras | 8 | 6 | 11 |
| Colonisation | COL | settlement placement | 6 | 5 | 7 |
| Holo-Me | STORE | store preview | 8 | 0 | 0 |

Then, as its own step after the controllers answer, show this table as an **interactive checkbox
form** (mcp__visualize__show_widget after mcp__visualize__read_me with module `interactive`; do NOT
split it across AskUserQuestion questions, the user rejected that). One row per bound mode: a checkbox
(ticked by default), mode name, code, then one binding-count column per chosen controller, exactly like
the table above. Add "Select all" / "Select none" links and a "Continue" button whose handler calls
`sendPrompt("Modes I use: SHIP, UI, FSS")` with the ticked codes (error inline if none ticked). Fall back
to the markdown table plus a typed list of codes only if the widget tool is unavailable. Unticked modes
become `drop`. Repeat back what was dropped.

**Step B: how to group them.** Only after the modes answer is in, and only using the modes the user
ticked (never mention or place an unticked mode). Explain the syntax, then ask for it. Each **square-bracket group is one
printed page**; modes inside a group share that page; any mode left out of every bracket is dropped.

```
[SHIP UI FSS DSS MC] [SRV FOOT] [MAP CAM COL STORE]
```

means three pages: flight, SRV & on foot, and maps/cameras/colony/Holo-Me. Show two or three more
examples built from the user's own chosen modes (fewest pages `[SHIP UI FSS DSS] [everything else]`
written out in full, one page per mode `[SHIP] [UI] [FSS]...`, everything on one page `[all]`). Offer
the first example as the default: "just say `recommended` to accept it". Accept loose input: codes or
plain words ("ship", "on foot"), commas or spaces, any case. A group naming a mode the controller has no
bindings for is fine; empty pages are skipped.

**Step C: per controller (optional).** Unless only one controller was chosen, ask whether the same
grouping applies to every controller. Explain why it may not: the Xbox pad carries the SRV and on-foot
bindings, while the stick and throttle have none, so the same brackets just give them fewer pages. To
vary it, accept one line per controller, using the controller's short name before the brackets:

```
Xbox:      [SRV FOOT] [UI FSS MAP]
Stick:     [SHIP UI FSS DSS MC]
Throttle:  [SHIP] [CAM COL]
```

Per-controller lines override the global grouping and the global mode list for that controller (modes a
controller's line leaves out are dropped for it only). Store as `devices.<id>.pages` / `devices.<id>.drop`.

**Step D: echo and confirm.** Parse the answer yourself, then show the resulting plan as a per-controller
list of pages with the bound modes and counts on each, plus what was dropped, and ask for a yes or
corrections. If a bound mode on a chosen controller ended up in no group, say so and ask (nearest
sensible page as default). Never place a mode the user didn't name and never silently drop one. Write
page titles that list exactly the modes on that page.

### 4. Style

Ask: graphical (photo with callouts, recommended), text-only, or both. Mention that text-only sheets
list every binding across all modes in one document, so the page grouping doesn't apply to them.

### 5. Photos and profiles

For each chosen device:
- **Profile with a missing photo:** download it from the profile's `source_url` (`page_url` is the
  product page it came from) and save it to `<folder>/img/` with the profile's file name, converting the
  format if needed. If the photo isn't available, that sheet is drawn as boxes only.
- **No profile (generic layout):** say that it will still get a tidy boxes-only sheet. Offer to create a
  photo profile (see "Adding a controller photo profile" below), noting that it takes a while and you'll
  ask about button mapping. Default: boxes-only now, photo profile later.

Optionally offer file names. The defaults are the controller names; skip this question unless the user
seems particular.

### 6. Save, build, check, report

1. **Save** every answer to `<folder>/ed-sheets.json` (format in `references/config.md`) before building.
   Then "build my elite bindings" next time is one confirmation.
2. **Build:** `python <skill>/scripts/make_sheets.py build --out <folder> --preview`. It honours the saved
   style; `--device ID ...` limits the run.
3. **Look at the previews** in `<folder>/_preview/` before reporting:
   - nothing overlaps;
   - leader lines land on the right controls;
   - text isn't tiny;
   - no red "Not on this sheet" line. That line means bindings exist on controls the profile doesn't
     cover; fix the profile.

   Pages must contain exactly the modes the user agreed to in step 3D. If you added or moved a mode
   they didn't confirm, fix the config and rebuild.

   If a page is cramped, suggest a different grouping rather than shipping it. Delete `_preview/` when
   you're done.
4. **Report:** list the files, the pages on each, and anything worth knowing: modifier buttons and
   combinations, controls left unbound, and modes coming from a different preset file. Only describe
   modes the user chose or confirmed in step 3. Do not mention a mode (multicrew, Holo-Me, maps...) they
   never asked for; if one slipped onto a page, that is a bug in step 3D, so fix it and rebuild.

If the user asked for something specific up front ("just redo the Xbox one", "text versions too"), skip
the questions that request already answers.

## Tailoring (ed-sheets.json in the output folder)

Save every preference the user expresses here so the next regeneration repeats it. Don't hand-edit the
PDFs. The full format is in `references/config.md`. `ed-sheets.example.json`, if present, is only a
sample; never treat it as the user's settings. Common requests:

| User says | Change |
|---|---|
| "I never use multicrew / Holo-Me" | add `"MC"` / `"STORE"` to `drop` (global or per device) |
| "put FSS on the flight page" / "SRV and on-foot together" | edit that device's `pages` |
| "call the file X" | `devices.<id>.file` |
| "skip the keyboard / that pedals device" | `devices.<id>.skip: true` |
| "also make text-only versions" | `"style": "both"` |
| "this is my left Virpil, not the right one" | `devices.<id>.profile` |

Layout styling (colours, highlight style) lives in `scripts/render.py`. Change it there only if the user
asks for a style change, and tell them it affects every sheet.

## Adding a controller photo profile

When the user wants a photo version of a controller that only has the generic layout, read
`references/profiles.md`. In short:

1. Find an official product photo (manufacturer site or store) showing the buttons clearly.
2. Use VKB/Virpil/Thrustmaster layout sheets or manuals, when the maker publishes them, to identify which
   physical control each button number is.
3. Run `make_sheets.py grid <photo>` and view the gridded image to read pixel positions.
4. Write `<folder>/profiles/<id>.json` with the controls, dots and sides, then build with `--preview` and
   iterate until the dots sit on the controls.

Button numbering is the risky part: Elite's button numbers depend on the device's firmware or
configuration, so confirm uncertain mappings with the user rather than guessing. VKB, for example,
assigns PIDs 0200, 0201... in the order devices are configured, so a profile's `suggested_device_ids`
may not match someone else's setup. Map the device explicitly in `ed-sheets.json` when in doubt.

## Sharing

The skill folder holds the code and profiles; photos live beside it in `<folder>/img/`. Someone else
installs it, runs `list`, downloads any photos their profiles reference that aren't already in `img/`
(each profile records `source_url` and `page_url`), and builds. Profiles they create for new controllers can be copied into `assets/profiles/` to share
further.
