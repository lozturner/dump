# CLAUDE.md — lozturner/dump

## Environment reality

Claude Code runs in a Linux sandbox (gVisor container). Laurence is on Windows.
**Localhost ports are never reachable from his browser. Do not start a server and give a localhost URL. It will never work.**

## Previewing pages — the only correct approach

This repo is deployed via GitHub Pages:

**https://lozturner.github.io/dump/**

When a page is created or updated and Laurence needs to view it:
1. Push the file(s) to the `gh-pages` branch using `mcp__github__push_files`
2. Give the direct GitHub Pages URL: `https://lozturner.github.io/dump/<filename>`
3. GitHub Pages deploys within ~60 seconds

Never do:
- `python3 -m http.server` + tell him to visit localhost
- Any variation of localhost:PORT
- "Start a server" of any kind

## Branch rules

- Development branch for new work: check session instructions for the current branch name
- Deployment branch: `gh-pages` — push production-ready HTML/CSS/JS here
- When a feature is complete, push to both the dev branch and `gh-pages`

## Site structure

- Static HTML + single `style.css` + `shit-switch.js`
- Pages use `data-hue` on `<body>` for colour theming (green, amber, blue, violet, pink, accent)
- Cards: `.card` > `.rows` > `.row` with `.k` / `.v` spans
- Navigation: `.back` links at top, `.nav-bar` at bottom
- All pages link back to `index.html`
