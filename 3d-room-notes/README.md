# 3D Room · Notes

A single-file Three.js scene. First-person walk around a bedroom with a bed, cabinet, and whiteboard. Drop floating sticky notes in free space. Walk up to the whiteboard and actually write on it.

## Run it

No build step. Just open the file:

```
open index.html
```

Or serve the folder with any static server if your browser blocks ES modules on `file://`:

```
python3 -m http.server 8000
# then visit http://localhost:8000/3d-room-notes/
```

## Controls

| key | action |
| --- | --- |
| `click` | lock mouse, enter room |
| `W A S D` | walk |
| `Shift` | sprint |
| mouse | look |
| `N` | drop a floating note where you're looking |
| `E` | when close to the whiteboard — open the drawing pad |
| `Esc` | release the mouse |

## What's in the room

- **Bed** against the left wall (frame, mattress, pillow, duvet, headboard)
- **Cabinet** against the back wall with three drawers and a little potted plant
- **Whiteboard** on the right wall — walk up, press `E`, draw with 5 colors + eraser, press *done*, drawing stays on the board when you walk away
- Rug, warm floor lamp, directional + area lighting for atmosphere

## Notes in free space

Press `N`, type a thought, hit `Enter`. A sticky note spawns 1.4m in front of the camera at the point you're looking, billboarded toward you with a small random tilt and one of six pastel colors. Walk around them. They persist for the session.

## Context — how this links into the other threads

This lives inside the [`dump`](https://github.com/lozturner/dump) repo, which is the catch-all for spike experiments spun out of Claude chat threads. Companion artefacts in the same repo:

- [`../tldr-session-map.html`](../tldr-session-map.html) — the **17 Apr 2026** session TLDR. This 3D room is a concrete stab at one of the unresolved threads in that map:
  - 🔴 *Core Problem* — "the gap between Claude reasons about it and a thing actually happens". A 3D room where you can *place* a thought into space is a tiny, single-file demonstration that the output doesn't have to stay in the chat.
  - 🟢 *Lost Tool — Three Lane Overseer* — not this, but related energy. This is spatial externalisation of ideas. Could eventually be the host surface for a lane/oversight view.
  - 🟠 *Voice / HTML Build Problem* — deliberately avoided here. No voice libs, no native Web Speech yet. Hook point: the `placeNote()` function takes a string; swap the modal for Web Speech recognition and you've got voice-pinned notes.

## Where to extend

If a future Claude session picks this up, obvious next moves:

- **Persistence** — serialize `notes[]` + the whiteboard canvas to `localStorage` on change; rehydrate on load. Currently session-only.
- **Voice** — replace the textarea in `#noteModal` with `webkitSpeechRecognition`; keep the existing `placeNote()` signature.
- **Grab / move notes** — raycast from camera on click; drag along the view plane.
- **Export** — button to dump all notes + the whiteboard PNG as a single JSON/zip, so a chat thread can ingest them.
- **MCP hook** — wire note creation to an MCP tool call so notes from this room become structured memory elsewhere.
- **More rooms** — doorways leading to "thread rooms", one per colored thread in `tldr-session-map.html`.

## Stack

- Three.js r160 (via unpkg ESM + importmap, no bundler)
- `PointerLockControls` for FPS movement
- CanvasTexture for the whiteboard and the note faces
- Sphere-vs-Box3 collision against furniture and walls

Single HTML file. No dependencies to install.
