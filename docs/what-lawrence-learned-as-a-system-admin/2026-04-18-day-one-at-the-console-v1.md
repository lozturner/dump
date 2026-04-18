# Day one at the console — v1

**Date:** 2026-04-18
**Branch:** `claude/add-device-monitoring-layer-Z71p6`
**Where Laurence was:** on his phone, iPhone Safari, signed in to Claude.

> "What does it mean to look in on something and see things moving along?"
> — Laurence Turner, 2026

---

## Situation

We were trying to stand up a **UI** that would let Laurence feel like things
were continuing to happen for him — the court filing, the complaints, the
markets, the kids — even while he wasn't actively looking. A layer between
the websites/documents he opens and the data behind them, rather than
something that boots up when you ask it to.

First attempts lived in a single `hub.html` file with 17 "lanes". The UI was
good but the **hosting story kept failing on iOS Safari**:

1. I kept wrapping URLs in markdown `**bold**`. When Laurence tapped the link
   on iOS, the trailing `**` was being glued into the URL → instant 404 on
   jsDelivr.
2. The feature branch name had a `/` in it
   (`claude/add-device-monitoring-layer-Z71p6`). `raw.githack.com` parses the
   first slash-segment as the branch name — so a 404 again.
3. jsDelivr serves `.html` from GitHub with `Content-Disposition: attachment`
   — Safari showed the source + a "Save…" download prompt instead of
   rendering the page.

That last point is what finally clicked: **jsDelivr is fine for binary assets
and JS libs, but it's the wrong tool for "render this HTML inline."**
`rawcdn.githack.com` (or `raw.githack.com` with a non-slashed branch) is the
right tool for the job.

## What Laurence suggested

- "Make the new UI a separate page, keep the old one linked from it." →
  kicked off the split of `hub.html` into `index.html` (warm landing with
  tiles) + a dedicated page per lane (`court.html`, `markets.html`, etc.).
- "Each tile should open its own page, not an inline drawer." → made tiles
  `<a>` elements pointing to `{id}.html`.
- "Give me clickable links, not walls of text I have to copy." → switched all
  further URLs to proper markdown `[label](url)` form with no bold.
- "Pin all the HTML files onto a pinboard that locks them together." → led to
  `gallery.html` + the `_sitemap.py` generator.
- "New page with a full software mini applet — a UI Stealer." → built
  `stealer.html` + `lego.html`.
- "From now on put version numbers in filenames so I can see where you're
  going." → that's what this file, `lego-v1.html`, `stealer-v1.html` reflect.

## The tech

- **Static site**, single branch `gh-pages` on `github.com/lozturner/dump`.
- **Hosting CDN that renders HTML inline**: `rawcdn.githack.com` (SHA-pinned,
  permanent). Also good: `raw.githack.com/<owner>/<repo>/<branch>/<path>` as
  long as the branch has **no slash**.
- **No build step, no backend.** Every page is a self-contained `.html` that
  loads `style.css` and uses `localStorage` for any user state.
- **Interactivity:** plain DOM. SVG for charts and node diagrams. `fetch()`
  for `sitemap.json`. `postMessage` between an iframe and its parent for the
  UI Stealer's click-to-pick.
- **Python** for the sitemap generator (`_sitemap.py` — scans `*.html`,
  extracts `<title>` + outgoing `href=".html"` links, writes `sitemap.json`).
- **Bash** for the per-lane page generator (`_gen.sh` — templated heredocs).

## Snippets that matter

### 1. The CDN rule of thumb

```text
❌  cdn.jsdelivr.net/gh/<user>/<repo>@<branch>/<file>.html
    → serves as download on iOS Safari

✅  rawcdn.githack.com/<user>/<repo>/<commit-sha>/<file>.html
    → renders inline, permanent, cache-free
```

### 2. Render any sibling HTML inside an iframe and receive clicks back

Used in `stealer.html`. Inject a tiny hook just before `</body>`, then
listen for `postMessage` in the parent:

```html
<style>
  ._ls-hi { outline:2px solid #e84c1e !important; outline-offset:2px !important; }
  ._ls-sel{ outline:2px solid #3fb950 !important; outline-offset:2px !important; }
</style>
<script>
(function(){
  document.addEventListener('click', e => {
    e.preventDefault(); e.stopPropagation();
    const el = e.target;
    const ident = {
      tag: el.tagName.toLowerCase(),
      id: el.id,
      classes: (el.className||'').split(/\s+/).filter(Boolean),
      outerHTML: el.outerHTML,
    };
    parent.postMessage({ type:'ls-pick', ident }, '*');
  }, true);
})();
</script>
```

### 3. Extract only the CSS rules that apply to a chosen element

```js
function extractCss(doc, el){
  const out = [];
  for (const sheet of doc.styleSheets){
    let rules;
    try { rules = sheet.cssRules; } catch(e){ continue; }
    for (const r of rules){
      if (r.type === 1 /* STYLE_RULE */){
        const selectors = (r.selectorText||'').split(',').map(s=>s.trim());
        for (const one of selectors){
          try {
            if (el.matches(one) || el.querySelector(one)){
              out.push(one + ' { ' + r.style.cssText + ' }');
              break;
            }
          } catch(e){}
        }
      }
    }
  }
  return out.join('\n');
}
```

### 4. Save anything as a downloadable `.htm`

```js
function download(name, content){
  const blob = new Blob([content], {type:'text/html'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = name + '.htm';
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(()=>URL.revokeObjectURL(a.href), 2000);
}
```

### 5. Sitemap generator — runs across `*.html`, prints relationships

```python
import re, json, glob, datetime
files = sorted(f for f in glob.glob("*.html") if not f.startswith("_"))
pages = []
for f in files:
    html = open(f).read()
    title = (re.search(r"<title>([^<]*)</title>", html, re.I) or [None,f])[1]
    links = sorted(set(re.findall(r'href="([^"#?]+\.html)', html)))
    pages.append({"file": f, "title": title, "links": links, "incoming": []})
by = {p["file"]: p for p in pages}
for p in pages:
    for l in p["links"]:
        if l in by: by[l]["incoming"].append(p["file"])
json.dump({"generated": datetime.datetime.now().isoformat(timespec="seconds"),
          "count": len(pages), "pages": pages},
          open("sitemap.json","w"), indent=2)
```

## Whole examples (live)

- [Home — `index.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/index.html)
- [The picture — `picture.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/picture.html)
- [The path — `path.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/path.html)
- [Gallery — `gallery.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/gallery.html)
- [Epigraph — `epigraph.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/epigraph.html)
- [UI Stealer · v1 — `stealer-v1.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/stealer-v1.html)
- [Lego Bricks Gallery · v1 — `lego-v1.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/lego-v1.html)
- [Monitoring layer — `hub.html`](https://rawcdn.githack.com/lozturner/dump/gh-pages/hub.html)

(**Note:** `stealer.html` and `lego.html` exist as unversioned mirrors of
`-v1` so inbound links keep working. When I iterate, `-v2` will be a new
file; the unversioned mirror will then point at the latest.)

## What I additionally incorporated (on top of the previous version)

- **Inline `+ Add something to oversee` button** *inside* the greeting text,
  in addition to the existing `+` tile — so both the dedicated UI affordance
  and the inline prose trigger the same modal. Keyboard-accessible
  (Enter/Space), `aria-label`'d, Escape closes the modal.
- **Versioned filenames** for new files: `stealer-v1.html`, `lego-v1.html`,
  this diary entry. The previous un-versioned files stay as canonical "latest"
  pointers — so no existing link ever breaks.
- **Diary folder** at `/what-lawrence-learned-as-a-system-admin/` with this
  README-plus-entries scheme, so every future session can add one.

## Files touched this version

| File | Change |
|------|--------|
| `index.html` | Added inline clickable `+ Add…` phrase + Stealer/Lego buttons |
| `stealer-v1.html` | **new** — UI stealer applet |
| `stealer.html` | mirror of `stealer-v1.html` (canonical latest) |
| `lego-v1.html` | **new** — Lego Bricks gallery + bottle clipboard + dev tools |
| `lego.html` | mirror of `lego-v1.html` |
| `what-lawrence-learned-as-a-system-admin/README.md` | **new** — diary index |
| `what-lawrence-learned-as-a-system-admin/2026-04-18-day-one-at-the-console-v1.md` | **new** — this entry |
| `sitemap.json` | regenerated |

## Where to pick up next time

- The Stealer's CSS extractor only walks inline `<style>` sheets — if we ever
  move to an external CSS framework, need to handle CORS-restricted sheets
  (wrap `cssRules` reads in try/catch; already done).
- JS extraction is heuristic (grep scripts for id/class). Good enough for now,
  but a proper AST walk would be more accurate.
- The Lego Gallery's "import .htm" does naïve regex split on `<style>` /
  `<script>` / `<body>` — doesn't handle multiple of each. If Laurence
  imports a page with several style/script blocks, only the first is
  preserved.
- GitHub Pages is still **off**. One click in `github.com/lozturner/dump/settings/pages`
  (Source: Deploy from branch, Branch: `gh-pages`, Folder: `/ (root)`) flips
  it on and we get a permanent `lozturner.github.io/dump/` URL with no CDN
  middleman.

---

*Written with Laurence, for Laurence, as a standing record of the tech he
learned while pushing through on his phone on 18 April 2026.*
