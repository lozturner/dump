# 3D Room · Notes

A single-file Three.js scene. First-person walk around a bedroom with a bed, cabinet, and whiteboard. Drop floating sticky notes in free space. Walk up to the whiteboard and actually write on it.

**Live:** https://lozturner.github.io/dump/3d-room-notes/

## Controls

### Desktop

| key | action |
| --- | --- |
| `click` | lock mouse, enter room |
| `W A S D` | walk |
| `Shift` | sprint |
| mouse | look |
| `N` | drop a floating note where you're looking |
| `E` | when close to the whiteboard — open the drawing pad |
| `Esc` | release the mouse |

### Mobile / touch

- Left thumb stick → walk
- Drag right half of screen → look
- `N` button → drop a floating note
- `E` button (appears near whiteboard) → open the drawing pad
- `RUN` button → toggle sprint

## What's in the room

- **Bed** against the left wall (frame, mattress, pillow, duvet, headboard)
- **Cabinet** against the back wall with three drawers and a little potted plant
- **Whiteboard** on the right wall — walk up, press `E`, draw with 5 colors + eraser, press *done*, drawing stays on the board when you walk away
- Rug, warm floor lamp, directional + area lighting for atmosphere

## Notes in free space

Press `N`, type a thought, hit `Enter` (or tap *pin it*). A sticky note spawns 1.4m in front of the camera at the point you're looking, billboarded toward you with a small random tilt and one of six pastel colors. Walk around them. They persist for the session.

## Context — how this links into the other threads

This lives inside the [`dump`](https://github.com/lozturner/dump) repo, the catch-all for spike experiments spun out of Claude chat threads. Companion artefacts:

- [`../tldr-session-map.html`](../tldr-session-map.html) — the **17 Apr 2026** session TLDR. This 3D room is a concrete stab at one of the unresolved threads in that map:
  - 🔴 *Core Problem* — "the gap between Claude reasons about it and a thing actually happens". A 3D room where you can *place* a thought into space is a tiny, single-file demonstration that the output doesn't have to stay in the chat.
  - 🟢 *Lost Tool — Three Lane Overseer* — not this, but related energy. Spatial externalisation of ideas. Could eventually host a lane/oversight view.
  - 🟠 *Voice / HTML Build Problem* — deliberately avoided here. Hook point: the `placeNote()` function takes a string; swap the modal for Web Speech recognition and you've got voice-pinned notes.

## Where to extend

- **Persistence** — serialize `notes[]` + whiteboard canvas to `localStorage`. Currently session-only.
- **Voice** — replace the textarea in `#noteModal` with `webkitSpeechRecognition`; keep `placeNote()` signature.
- **Grab / move notes** — raycast from camera; drag along view plane.
- **Export** — dump all notes + whiteboard PNG as JSON so a chat thread can ingest them.
- **MCP hook** — wire note creation to an MCP tool call so notes become structured memory elsewhere.
- **More rooms** — doorways to "thread rooms", one per colored thread in the session map.

## Stack

- Three.js r160 (via unpkg ESM + importmap, no bundler)
- `PointerLockControls` for desktop FPS movement; custom pointer-event joystick + look drag for touch
- CanvasTexture for whiteboard + note faces
- Sphere-vs-Box3 collision against furniture and walls

Single HTML file. No dependencies to install.
