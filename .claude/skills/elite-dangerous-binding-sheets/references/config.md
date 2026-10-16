# ed-sheets.json

Optional settings file in the output folder. Every key is optional.

```json
{
  "preset": null,
  "style": "visual",
  "drop": ["MC"],
  "pages": [
    {"title": "Flight – ship, combat, panels & scanners", "contexts": ["SHIP", "UI", "FSS", "DSS", "MC"]},
    {"title": "SRV & on foot", "contexts": ["SRV", "FOOT"]},
    {"title": "Maps, cameras, colony & Holo-Me", "contexts": ["MAP", "CAM", "COL", "STORE"]}
  ],
  "devices": {
    "231D0200": {
      "profile": "vkb-gladiator-nxt-evo-scg-premium-right",
      "file": "VKB Right stick",
      "name": "My right stick",
      "style": "both",
      "drop": ["MC", "STORE"],
      "pages": [ ... ],
      "skip": false
    }
  }
}
```

## Top-level keys

| key | meaning |
|---|---|
| `bindings_dir` | Path to Elite's `Bindings` folder, when it isn't in a standard location. |
| `preset` | Preset name (e.g. `"Custom"`) or a `.binds` path. Leave it null to use what the game loads via `StartPreset.4.start`, including per-mode presets. |
| `style` | `visual` (photo or boxes, one page per page-group), `table` (text-only, every binding, `<name> (text).pdf`) or `both`. |
| `drop` | Contexts to leave out of every sheet. |
| `pages` | Page groups for visual sheets. The defaults are shown above. Pages with no bindings for a device are skipped. |

## Per-device keys (`devices.<device id>`)

Each per-device key overrides the top-level key of the same name for that device.

| key | meaning |
|---|---|
| `profile` | Id of the profile to use. Without it, a profile listing this id in `suggested_device_ids` is used; otherwise the generic layout. |
| `file` | PDF base name (no extension). |
| `name` | Title printed on the sheet. Also useful for generic devices with cryptic ids. |
| `skip` | Don't build this device unless it's named with `--device`. |

## Page keys

| key | meaning |
|---|---|
| `title` | Page heading. |
| `contexts` | Contexts shown on this page. |
| `tagged` | Contexts whose lines get a coloured tag. Default: every context except SHIP, so on a flight page plain lines mean "ship". |

## Contexts

| code | covers |
|---|---|
| SHIP | Flight, combat, targeting, pips, cockpit panels, ship toggles |
| UI | Menu/panel navigation (up/down/select/back, tabs, pages) |
| FSS | Full Spectrum System scanner |
| DSS | Detailed Surface Scanner |
| MC | Multicrew |
| SRV | SRV driving and turret |
| FOOT | On-foot (Odyssey) |
| MAP | Galaxy/system map camera |
| CAM | Ship cameras, free camera |
| COL | Colonisation and settlement placement |
| STORE | Store preview and Holo-Me |

To move an action to a different context, edit its entry in `scripts/ed_actions.py`.
