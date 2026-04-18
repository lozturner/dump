# UI Stealer moved to `ui-stealer/` — v1

**Date:** 2026-04-18
**Trigger:** Laurence's instruction — *"The UI Stealer should have its own
folder on the repo. Move it, re-path every page to reflect the change. Start
a changelog folder. Add that as an entry as well."*

## What moved

| From | To |
|------|----|
| `/stealer.html` | `/ui-stealer/stealer.html` |
| `/stealer-v1.html` | `/ui-stealer/stealer-v1.html` |

Used `git mv` so history follows the files. The unversioned `stealer.html`
stays as the canonical mirror of the latest version, sitting next to its
versioned sibling inside `ui-stealer/`.

## Paths repointed

Inside the stealer files (now one folder deeper):

| Was | Now |
|-----|-----|
| `href="style.css"` | `href="../style.css"` |
| `href="index.html"` | `href="../index.html"` |
| `href="gallery.html"` | `href="../gallery.html"` |
| `href="lego.html"` | `href="../lego.html"` |
| `fetch('sitemap.json?t=…')` | `fetch('../sitemap.json?t=…')` |
| `fetch(file + '?t=…')` (when user picks a page in the dropdown) | `fetch('../' + file + '?t=…')` |

From root pages that link to the stealer:

| File | Was | Now |
|------|-----|-----|
| `index.html` | `href="stealer.html"` | `href="ui-stealer/stealer.html"` |
| `lego.html` | 3× `href="stealer.html"` | `href="ui-stealer/stealer.html"` |
| `lego-v1.html` | 3× `href="stealer.html"` | `href="ui-stealer/stealer.html"` |

Also updated the mirrored copies under `docs/` to match (they're just static
exports of the same tree).

## Why

Two reasons:

1. The Stealer is a **tool**, not a lane. Lanes are the dashboard surface
   (`court.html`, `markets.html`, etc.). Tools are its own category. Giving
   it its own folder makes that distinction visible at the repo level — you
   can tell the shape of the thing from the file tree, without opening
   anything.
2. It gives room to grow. The Stealer will eventually need its own CSS, its
   own small JS helpers, maybe sub-views (per-element-type extractors,
   visual diff between original and stolen output, etc.). Having a folder
   means those can land next to it without polluting the root.

## Verification

- `grep -rn 'href="stealer' .` → only hits are inside `docs/` mirrors of
  pre-move snapshots (expected) and in the diary entry from earlier today
  (historical record, intentionally left).
- `grep -rn 'href="ui-stealer/stealer' .` → hit in `index.html`, `lego.html`,
  `lego-v1.html` (plus their `docs/` mirrors).
- `ui-stealer/stealer.html`'s fetch calls correctly target `../sitemap.json`
  and `../<file>` for source-page loads.
- Sitemap regenerated. `ui-stealer/stealer.html` is **not** scanned by
  `_sitemap.py` because it only globs top-level `*.html` — that's deliberate:
  the sitemap is for lane pages, not tools. If we decide later that the
  sitemap should include subfolders, one-line change in the generator.

## Files touched

- `ui-stealer/stealer.html` (moved + repathed)
- `ui-stealer/stealer-v1.html` (moved + repathed)
- `index.html` (link repointed)
- `lego.html` (3 links repointed)
- `lego-v1.html` (3 links repointed)
- `docs/…` equivalents of the above
- `changelog/README.md` (**new**)
- `changelog/2026-04-18-ui-stealer-moved-to-subfolder-v1.md` (**new** — this file)
- `sitemap.json` (regenerated)

## Not yet done

- GitHub Pages is still off. When it's flipped on, the repo becomes
  `lozturner.github.io/dump/` and the URL to the tool becomes
  `lozturner.github.io/dump/ui-stealer/stealer.html`. No further path
  changes needed — subfolder already matches.
- If the Stealer grows (CSS / JS / other views), they go in this same folder.
  The unversioned `stealer.html` will continue to mirror `stealer-vN.html`.
