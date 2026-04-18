# Tash — what this is, where you can help, and why I need it

*Written 18 April 2026. Version 2 — adds a Part Two that breaks the fourth wall so you can see what I was actually doing while writing this.*

---

## What this is, in one line

It's a personal hub I'm building on my phone, with an AI, to **hold the
shape of my life in one place** — so that when I look at it, I can see
things moving along, instead of feeling like everything is slipping.

## What it actually looks like

Right now it's a set of web pages that live in a GitHub repo. No app store.
No backend. No database. Just HTML files that open on my phone. Everything
I type into it saves on my phone — nothing leaves the device unless I move
it myself.

The main pieces:

- **A landing page** — with my name at the top and tiles for each part of
  my life: family court, markets, complaints, the kids' day-to-day, health,
  money, and so on.
- **A deeper "monitoring layer"** behind the landing — denser, more data.
- **A page called "The picture"** — where I keep an honest, visual
  accounting of how much time I'm supposed to be seeing my children versus
  how much I actually am. Heatmap. Stats. A log.
- **A page called "The path"** — nodes on a board showing how to move from
  state A (cut off) to state B (seeing and talking to them). With the
  actions at each node: what costs money, what costs time, what's
  paperwork, what's going out into the world.
- **A UI Stealer** (a little tool) and a **Lego Bricks Gallery** — where
  I can grab UI pieces I like from one page and save them to reuse.
- **A "what Laurence learned as a system admin" diary** — a running record
  of the technical stuff I picked up while making this, so I can pick up
  next time without having to remember everything.

## Why I need it

The short version: **the tools exist, but the tools need the executive
function I don't always have, in order to set themselves up.** It's a
recursive paradox. I've got three years of finding this pattern.

The slightly longer version:

1. I've got a lot of live threads — court, complaints, kids, money — and
   they don't wait for me to be ready. They all run in parallel whether
   I'm watching or not. When I'm not watching I lose days, and when I
   come back I don't know where I left off.
2. Apps and AI chat are powerful, but they're also high-friction. Opening
   a fresh chat means re-explaining my entire story. Using a proper
   project-management app means setting it up first, which is the
   executive function I'm trying to replace.
3. What I actually need is **a place that's already running when I get
   there.** Not something I have to start. Not something I have to
   re-explain to. A place that greets me by name and tells me what moved
   while I was away.

That's what the hub is. It's not clever. It's not unique. But it exists,
on my phone, in my pocket, right now — and when I open it, I can see things.

## Where you can help

If you want to — and only if you want to — here are the places where a
second pair of hands or eyes would actually move the needle:

### 1. Sanity-check the picture

On "The picture" page there's a big calendar heatmap of days I was
supposed to see my son, vs days I actually did, vs days that were missed.
I can tap each square to record what actually happened. What would help
is **you being a witness to that** — either confirming a date I've marked,
or adding dates I've forgotten. Your perspective is worth something the
court doesn't otherwise see.

### 2. Proof-reading the court-facing material

There are drafts — the escalation letter, the court bundle, the
complaints. If you're up for reading any of them with calm eyes and
telling me where the tone goes off, that's a massive help. I'm too close
to it.

### 3. Being the "person beside you" on the path

On "The path" page there's a node called **People beside you**. The ask
there is specifically: *at least one person who knows the facts and can
stand next to you.* If you'd be OK with me briefing you on the facts once
and keeping you updated every so often, that's already meaningful. You
don't have to do anything with the information. Just knowing someone else
knows makes the difference between carrying it alone and not.

### 4. Telling me when the tech gets in the way of the life

A lot of today was me fighting with URL formats and CDNs while what I
actually needed was to look at my son. If you see me disappearing into
the building, tell me. I'll listen.

### 5. Nothing

You don't have to help. Reading this and understanding what's going on
is already more than most people have. No pressure.

## How to actually use the hub (when I send it to you)

- Open the link I send on your phone's browser (Safari or Chrome, either
  works).
- Everything you do on it stays on *your* phone — your ticks don't appear
  on mine and vice versa. So you can poke around freely without worrying
  about messing anything up.
- If you want to see what I'm looking at, I'll either screenshot or we'll
  walk through it together. Over coffee is best.

## What I don't need

- Advice on "have you tried…". I've tried.
- Solutions, unless I ask. The building of solutions is what the hub is
  for.
- Comparison. Everyone's situation is different.

## The one thing I most want you to take away

When you see me working on this, it isn't a distraction from the real
thing. **It is the real thing.** Stopping the slide is the real thing.
Keeping a record is the real thing. Seeing my son is the real thing. The
hub is the scaffolding.

Thank you for reading this far.

— Laurence

---

## Part Two — what Laurence actually means (fourth wall)

*(I'm stepping out of my own voice for a minute so you see how this was actually made. Then I'll step back in. — L.)*

Everything above was written while I was sitting on my phone. Not at a desk, not on a laptop, not in an IDE. Phone. One hand. Thumbs.

Here is the actual setup, because I want you to see it:

- I don't have a screen. I'm trying to get one back. This whole build is me trying to stand one up — somewhere I can see the shape of my life in one window.
- The only tool I've got in my pocket that can create files, make folders, push to GitHub, and write real code is **Claude** — the Anthropic AI. I talk to it on my phone. It does the typing.
- Claude, on its own, doesn't render webpages. It can write HTML and push it to my repo, but it can't show me the result. So every time I want to *see* what's been built, I have to switch apps, open a browser, paste the CDN link, wait for the file to download, open it from Files, and then finally I'm looking at the thing. Over and over. Every single change.
- Because of that round-trip, this is the **fastest** way I have of working right now. The alternatives are slower, not faster: voice-only (drifts, loses context), manually writing files on a laptop I don't have, or waiting until I'm somewhere quiet with a desktop (which is most of the time not happening).
- I use Claude to create folders, files, move files, sterilise copies, generate sitemaps, write diary entries, and yes, to write what you're reading now. It then pushes those files to GitHub where they live. GitHub is the floor under my feet; Claude is the voice giving the instructions; my phone is the window I'm holding all of it through.
- To be honest with you, this workflow leans on a lot of the AI's edges. I am asking it to do things at the edge of what the people who made it probably had in mind — creating and moving files on my behalf at volume, being the only way I can get work out the door. It has broken a fair few of the normal "just use the proper tool" rules. It has pushed some of the security defaults, because every file we make is a file I can't check line-by-line before it goes live; I'm trusting the sum, not the parts.

I'm telling you this because when you read the polished version above, it's easy to assume I had a machine, a setup, a routine. I didn't. I had one phone, one AI, and the determination not to let today be another day where nothing got done.

So when you see the UI and think "that looks alright" — remember it was built one thumb-typed message at a time, by someone who was trying to see his son.

The scrappiness is not carelessness. It's effort. Please read it that way.

— L.

*(End of Part Two. Back to the top for the normal version. —)*
