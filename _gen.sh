#!/usr/bin/env bash
set -euo pipefail

gen() {
  local id="$1" hue="$2" name="$3" badge="$4" body="$5" rows="$6" prev_id="$7" prev_name="$8" next_id="$9" next_name="${10}"
  cat > "${id}.html" <<HTML
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#0e0f12">
<title>${name} · Hub</title>
<link rel="stylesheet" href="style.css">
</head>
<body data-hue="${hue}">

<a class="back" href="index.html"><span class="arr">←</span> Home</a>
<a class="back" href="gallery.html" style="margin-left:6px"><span class="arr">⌘</span> Map</a>
<a class="back" href="path.html" style="margin-left:6px"><span class="arr">→</span> Path</a>
<a class="back" href="picture.html" style="margin-left:6px"><span class="arr">○</span> Picture</a>

<div class="page-head">
  <div class="hey">
    <span class="chev">‹</span>
    <span>Hey</span>
    <span class="name">${name}</span>
    <span class="chev">›</span>
    <span>how are you getting on?</span>
  </div>
  <span class="badge">${badge}</span>
</div>

<div class="card">
  <h2>Where this lane's at</h2>
  <p class="body">${body}</p>
</div>

<div class="card">
  <h2>Since you were last here</h2>
  <div class="rows">
${rows}
  </div>
</div>

<div class="card">
  <h2>What you can do</h2>
  <div class="controls">
    <button class="btn primary">Mark read</button>
    <button class="btn">Pin to top</button>
    <a class="btn" href="hub.html#${id}">Open in monitor →</a>
  </div>
</div>

<div class="nav-bar">
  <a href="${prev_id}.html">← ${prev_name}</a>
  <a href="${next_id}.html">${next_name} →</a>
</div>

<div class="footer">
  <b>I've been watching this lane.</b> Nothing here auto-starts. When you check in, I show you what changed.
</div>

</body>
</html>
HTML
}

row() { printf '    <div class="row"><span class="k">%s</span><span class="v">%s</span></div>\n' "$1" "$2"; }

# ── pages ──────────────────────────────────────────────
gen court accent "Family Court" "T−9d hearing" \
"The children's file. Two documents landed this week, one of them contradicts the Feb 18 statement — I've flagged it. Next hearing window opens in nine days and the bundle is about three-quarters assembled." \
"$(row "Since last" "2 docs auto-sorted into the timeline."
row "Flag"       "Contradiction on exhibit-C page 47."
row "You left"   "Reading exhibit-C, paragraph 3."
row "Filing"     "Bundle 73% assembled.")" \
ideas "Ideas" markets "Markets"

gen markets green "Markets" "Live" \
"Today's tape against your sheet. Three of your legs moved into the money since open. The position you flagged Tuesday had its premium collapse — IV crush, down 22%." \
"$(row "Sheet"   "options-watchlist · 3 legs ITM."
row "Alert"   "IV crush on Tue's flagged position."
row "Pending" "Limit order still unfilled at strike."
row "Today"   "Hedge +1.4% · directional −0.3%.")" \
court "Family Court" complaints "Complaints"

gen complaints blue "Complaints" "CC-2026-0842" \
"Case CC-2026-0842 hasn't moved since the 11th — next expected response the 25th. The ombudsman sent an acknowledgement this morning. Your escalation draft is still half-written." \
"$(row "CC"    "Status unchanged · next 25 Apr."
row "Reply" "Ombudsman acknowledged 09:17."
row "Draft" "Escalation letter still open."
row "Pattern" "2 earlier complaints · same officer.")" \
markets "Markets" links "Links & Tools"

gen links violet "Links & Tools" "Bridged" \
"The bridge between the websites you browse and the tools you've built. Four links carried across today. Your screenshots are indexed and OCR'd. Two of your own tools have gone quiet." \
"$(row "Bridged" "4 URLs → research-vault."
row "Capture" "Clipboard indexed, OCR'd."
row "Duplicate" "AAT page opened 3× this week."
row "Dormant" "2 tools unused 11 days.")" \
complaints "Complaints" inbox "Inbox"

gen inbox blue "Inbox" "Triaged" \
"Noise is held back — 42 low-priority emails parked. What reaches you reaches you on purpose. Your solicitor sent one with 'affidavit' in the subject." \
"$(row "Held"      "42 low-priority parked."
row "Forward"   "Solicitor · re: affidavit."
row "Reply-due" "3 you owe. Oldest 6 days."
row "Thread"    "CC complaint thread branched.")" \
links "Links & Tools" calendar "Calendar"

gen calendar pink "Calendar" "Tracking" \
"Every deadline I can see across your portals and inboxes, pulled onto one line. The court window is the heavy one; everything else fits around it." \
"$(row "T−9d"  "Family court filing opens."
row "T−3d"  "Centrelink review form due."
row "T−1d"  "Options expiry · 2 short legs."
row "Today" "16:30 ombudsman call-back.")" \
inbox "Inbox" gov "Gov Portals"

gen gov green "Gov Portals" "Live" \
"MyGov, ATO, Medicare, AAT — I keep the sessions warm so you don't re-login into the abyss. ATO pushed a refund assessment: \$1,284. Your AAT matter moved to Directions." \
"$(row "ATO"     "Refund assessment · \$1,284."
row "AAT"     "Pre-hearing → Directions issued."
row "MyGov"   "1 new message (read here)."
row "Medicare" "2 unreimbursed from March.")" \
calendar "Calendar" research "Research"

gen research violet "Research" "Indexed" \
"Where you stopped reading, and what I pulled from everything else while you were elsewhere. Eleven quotes are tagged for your submission. Two passages contradict each other — flagged." \
"$(row "Stopped"      "Hansard 2024-11-14 · p47."
row "Extracted"    "11 quotes tagged for submission."
row "Contradictions" "2 passages flagged side-by-side."
row "Queue"        "5 PDFs sorted by relevance.")" \
gov "Gov Portals" money "Money"

gen money amber "Money" "Watching" \
"Balances and what's leaving soon. Four charges in the next week totalling \$387. Two subscriptions you haven't used in 90 days. A disputed charge reversed overnight." \
"$(row "Upcoming" "4 charges · \$387.20 total."
row "Zombie"   "2 subs unused 90 days."
row "Refund"   "Disputed charge reversed."
row "Cashflow" "Net this week · +\$612.")" \
research "Research" people "People"

gen people accent "People" "Graph" \
"The humans in the loop. Who's owed a reply, who's gone quiet, who to leave alone today. Your sister checked in — no urgency. Your solicitor is waiting on a draft." \
"$(row "Solicitor" "3 days · draft sits in outbox."
row "Support"   "Sister texted · no urgency."
row "Quiet"     "2 usual fast responders at 4 days."
row "Avoid"     "Do-not-contact list respected.")" \
money "Money" devices "Devices"

gen devices blue "Devices" "Synced" \
"Which device you're on and what each one was last doing. Same hub from any of them — pick up wherever." \
"$(row "This"   "Phone · Safari · active."
row "Phone"  "Idle 2h · 1 unsaved draft."
row "Tablet" "Reading exhibit-C · mirrored."
row "Laptop" "Sleeping · 6 tabs held.")" \
people "People" captures "Captures"

gen captures green "Captures" "24h" \
"Everything you copied, screenshotted, or spoke at a device — kept and searchable. Nothing lost to the void." \
"$(row "Clipboard"   "14 items · 3 pinned."
row "Screenshots" "6 today · all OCR'd."
row "Voice"       "Walking note · 340 words."
row "Lost?"       "Nothing. Recovery 11 Apr 09:00.")" \
devices "Devices" ai "AI Threads"

gen ai violet "AI Threads" "Stitched" \
"Every AI chat you've opened, knitted together. No more retelling your story to a fresh window. Three concepts still unresolved across models." \
"$(row "Claude"     "This thread + 2 linked priors."
row "ChatGPT"    "Options strategy · last 2d."
row "Gemini"     "Court filing format · archived."
row "Carry-over" "Three-lane overseer · missing.")" \
captures "Captures" kids "Kids · Day"

gen kids pink "Kids · Day" "Quiet" \
"Separate from the court file. The small things. One permission form to sign by Friday. Seven new photos on the shared album. No school-side concerns this week." \
"$(row "School" "1 form due Fri · 1 newsletter."
row "Photos" "7 new on shared album."
row "Dates"  "Parent-teacher 29 Apr."
row "Quiet"  "No concerns logged this week.")" \
ai "AI Threads" health "Health"

gen health amber "Health" "Gentle" \
"How much you've had to carry today. Your sleep was short; I'm filtering harder. I'm holding three non-urgent items back unless you ask for them." \
"$(row "Sleep"   "5h 40m · below 7h target."
row "Load"    "38 decisions today · filtering."
row "Meds"    "Morning dose confirmed 08:04."
row "Suggest" "Holding 3 non-urgent items.")" \
kids "Kids · Day" ideas "Ideas"

gen ideas accent "Ideas" "Archive" \
"Things you said once, half-said once, or drew on a napkin once. I don't let them fall off. The three-lane overseer concept is still missing from the archive — I'm still looking." \
"$(row "Missing" "Three-lane overseer · hunting."
row "Tracked" "Always-on hub · this thing."
row "Seeded"  "Voice via Web Speech · not yet."
row "Fresh"   "Dopamine-hook UI framework.")" \
health "Health" court "Family Court"

echo "Generated 16 sub-pages."
