# Getting a live link out of an AI-generated HTML page

**Date:** 2026-04-18
**Project:** `lozturner/dump`
**Trigger:** Claude built `lawrence-site-map.html`, handed back `http://localhost:8000/...`, Safari on iPhone said "can't connect to the server".

Copy this file into future projects. The same problem will happen again — it always does.

---

## What went wrong

The AI runs inside a sandboxed container. When it starts `python3 -m http.server`, that server is listening on the container's own loopback interface. "localhost" on your phone means *your phone*, not the container. The two machines aren't on the same network and there is no route between them.

**This is not a bug in the tool. It is the default behaviour of every AI coding environment** — Claude Code sandboxes, OpenAI Codex, Cursor's remote workers, replit agents, etc. Any time an AI offers you a `localhost` or `127.0.0.1` URL, assume it's unreachable from any other device until proven otherwise.

---

## The fix that actually worked (this session)

Published the file via **GitHub Pages** from a dedicated `gh-pages` branch. GitHub hosts static HTML on a public URL that any browser on any network can hit.

URL shape: `https://<user>.github.io/<repo>/<file>`

For this repo: `https://lozturner.github.io/dump/lawrence-site-map.html`

One-time setup after the first push: **repo → Settings → Pages → Source: `gh-pages` branch, root folder → Save.** After ~30 seconds it's live.

---

## Parameter design — pick the one that matches your constraints

Ranked by how reliable they are in practice.

### 1. GitHub Pages (best durable option)
- **When to use:** you control the repo, the content is public-safe.
- **Setup:** push an `index.html` (or any `.html`) to a `gh-pages` branch (or `main` + `/docs`).
- **URL:** `https://<user>.github.io/<repo>/<path>.html`
- **Pros:** permanent, shareable, free, indexable, HTTPS, works on any device.
- **Cons:** public only on free tier; ~30 s propagation after first enable; needs one manual settings click.
- **AI prompt snippet:** *"Publish it to a gh-pages branch and tell me the github.io URL. Create the branch if it doesn't exist."*

### 2. raw.githack.com (the one that actually works when others blank out)
- **When to use:** file pushed to any branch; Pages not enabled; htmlpreview returned blank.
- **URL shape:** `https://raw.githack.com/<user>/<repo>/<branch>/<file>.html`
- **Pros:** serves with correct MIME types so browsers render HTML inline; tolerates branch names with slashes (e.g. `claude/feature-foo`); no setup; no rate limits in practice.
- **Cons:** `raw.githack.com` is CDN-cached — if you just pushed, hit Ctrl-F5 or append `?v=2`. For production use they recommend `rawcdn.githack.com` (immutable commit-pinned).
- **AI prompt snippet:** *"Give me a raw.githack.com URL for the file on the branch you just pushed."*

### 2b. cdn.statically.io (identical purpose, different CDN)
- **URL shape:** `https://cdn.statically.io/gh/<user>/<repo>/<branch>/<file>.html`
- **Use as a fallback** if raw.githack is down or cached wrong.

### 2c. htmlpreview.github.io (older, flakier)
- **URL shape:** `https://htmlpreview.github.io/?https://github.com/<user>/<repo>/blob/<branch>/<file>.html`
- **Known failure modes:** branch names containing `/` sometimes parse wrong; the preview iframes the content and some layouts render blank; occasionally the service itself is down.
- **Reality:** tried 18 Apr 2026 — returned a blank white page on iPhone Safari. Use only as a last resort. Prefer raw.githack.com (#2) above.

### 3. Raw GitHub link (the honest fallback)
- **When to use:** you just want to read the source or copy it.
- **URL shape:** `https://github.com/<user>/<repo>/blob/<branch>/<file>.html`
- **Pros:** never breaks, shows code.
- **Cons:** does **not** render HTML — shows source.

### 4. Public tunnel (ngrok, cloudflared, tailscale funnel)
- **When to use:** the AI sandbox has outbound internet and you want the AI's running server exposed.
- **Setup (from the sandbox):** `cloudflared tunnel --url http://localhost:8000` → get a `trycloudflare.com` URL.
- **Pros:** doesn't need a git push; works for dynamic servers (Node, Flask, Next.js dev).
- **Cons:** most AI sandboxes block outbound tunnel protocols; URL dies when the sandbox session ends; not every AI has the CLI preinstalled.
- **AI prompt snippet:** *"Start the dev server and expose it with cloudflared. Give me the public https URL."*

### 5. Netlify Drop / Vercel / Surge (drag-and-drop static hosts)
- **When to use:** you want a link without touching git.
- **Flow:** AI zips the built site → you download → drag onto netlify.com/drop → URL.
- **Pros:** no repo needed, instant custom URL.
- **Cons:** human-in-the-loop (you have to upload); not automatable from inside most sandboxes.

### 6. Bind the dev server to `0.0.0.0` on the same LAN
- **When to use:** your phone and the machine running the AI are on the same Wi-Fi (rare — only if the AI is running locally on *your* machine, not a cloud sandbox).
- **Command:** `python3 -m http.server 8000 --bind 0.0.0.0`
- **URL:** `http://<machine-lan-ip>:8000/file.html` (get IP via `ipconfig getifaddr en0` on Mac, `hostname -I` on Linux).
- **Pros:** no cloud round-trip.
- **Cons:** doesn't work from a cellular/4G connection; doesn't work at all if the AI runs in a cloud sandbox.

### 7. Render to PDF / PNG and send the file
- **When to use:** the HTML is a static visual (like this site map) and you just need to *see it*, not interact.
- **Flow:** AI runs `chromium --headless --screenshot` or `wkhtmltopdf`, commits the image/PDF alongside the HTML.
- **Pros:** works on any viewer, including messaging apps.
- **Cons:** loses interactivity; stale the moment the HTML changes.

### 8. Gist + raw link + htmlpreview
- Same idea as #2 but for one-off snippets not worth a repo.
- URL: `https://htmlpreview.github.io/?https://gist.githubusercontent.com/<user>/<id>/raw/<file>.html`

---

## A prompt block to paste into future AI sessions

> Whenever you build an HTML file I need to view, do **not** hand me `localhost` or `127.0.0.1` links — those don't reach my phone. Instead, default to this order:
> 1. If the repo has GitHub Pages already enabled, push to the Pages branch and give me the `github.io` URL.
> 2. Otherwise push to any branch and give me a `raw.githack.com/<user>/<repo>/<branch>/<file>.html` URL (this is the reliable default — works with slashes in branch names, renders inline HTML correctly).
> 3. If raw.githack is down, fall back to `cdn.statically.io/gh/<user>/<repo>/<branch>/<file>.html`.
> 4. Do **not** default to htmlpreview.github.io — it silently returns blank pages too often. Only offer it as a last-resort third fallback.
> 5. If the HTML pulls in sibling CSS/JS/image files, Pages or raw.githack both work (they preserve folder structure). htmlpreview does not — skip it.
> 6. If I want to interact with a running dev server, expose it with cloudflared and give me the `trycloudflare.com` URL. Never offer a localhost URL.
> 7. Before giving me the link, verify it yourself with a fetch — if your sandbox blocks outbound, say so explicitly rather than handing me an unverified URL.

## Gotchas found on 18 Apr 2026

- **`localhost:8000` from AI sandbox → phone on 4G = 0% chance.** Never suggest it without a tunnel.
- **Pages existing on a branch ≠ Pages enabled.** The `gh-pages` branch was already in the repo with commits, but visiting `https://<user>.github.io/<repo>/` returned 404 because Pages had never been switched on in Settings. Having the branch is step 1 of 2.
- **htmlpreview.github.io returned blank** on the exact URL the AI suggested. Branch names with slashes (`claude/create-site-map-t4Un7`) are suspected. raw.githack.com handled the same path fine.
- **AI sandboxes often block outbound HTTPS to random hosts** (got 403 on raw.githack, statically.io, and github.io from inside the sandbox). That means the AI can't always self-verify a preview URL — it has to push and trust, or tell you that up front.

---

## Why this keeps happening

AI coding tools default to "it works on my machine" because their training data is full of developer tutorials that assume `localhost`. The tool doesn't know where *you* are. Unless your prompt states the constraint ("I'm on my phone, on 4G, the server machine is a cloud sandbox"), the model picks the tutorial-default answer.

**Durable fix:** keep a note like this one in `docs/diary/` at the root of every project, and point new AI sessions at it on first contact. One sentence — *"Read `docs/diary/2026-04-18-live-preview-links.md` before suggesting how I preview anything"* — collapses this whole conversation into zero back-and-forth next time.
