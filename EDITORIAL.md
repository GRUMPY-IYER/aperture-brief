# The Aperture — editorial rules

The daily task reads this file. It is the *what to publish* half of the paper;
`build.py` and `templates/aperture.html.j2` are the *how it looks* half. Changing
a rule here changes the paper without touching a line of code.

Mechanical rules are NOT repeated here — `build.py check()` already enforces the
story cap, source diversity, duplicate and repeat URLs, the India cap, the travel
count, and the paywall blocklist. It fails the build rather than asking anyone to
remember. What follows is the judgement it cannot make.

## Voice

A brief, not a digest. Every story earns its slot. On a thin day a section runs
short; it never pads. Blurbs say what happened AND why it matters — a headline
restated in longer words is wasted space.

## Sourcing

Prefer independent and investigative outlets over wire copy, and bylined
reporting over agency feed. Tag stories from investigative outlets so readers can
see where the reporting came from.

Never link a paywalled article. The blocklist in `build.py` catches the known
offenders, but it cannot detect a metered outlet that happens to have walled the
specific piece you picked. Open the page. If it demands a login or shows
"subscriber only", find the same story reported free — Reuters, AP, NPR, Al
Jazeera and Techmeme usually have it. When unsure, choose a different story.

Every link must point at the actual article — never a section front, tag page,
topic hub or Wikipedia entry standing in for reporting.

By section:
- **US Politics** — Axios, NPR, ProPublica, The Marshall Project, The Intercept,
  Mother Jones, Reveal/CIR. Look for an investigative piece from the last 24h
  before finalising; skip rather than force one.
- **Geopolitics** — Al Jazeera English, Foreign Policy, War on the Rocks, Noema, NPR.
- **India** — Scroll.in, Newslaundry, The News Minute, Article 14, The Caravan,
  Alt News, IndiaSpend, The Reporters' Collective. Same investigative expectation
  as US Politics.
- **Bengal** — The Telegraph India, ABP Live, Millennium Post, The Statesman,
  The Federal. At least one ABP-family item when one exists. Note: anandabazar.com
  blocks fetching, and anandabazar.com.in is an impersonation site — never link it.
  Prefer a bylined ground report over PTI/ANI wire copy; a slightly older
  well-reported piece beats a same-day weather alert, but say so when you do it.
- **Cricket** — ESPNcricinfo, BBC Sport. Cricket only: no football, tennis,
  cycling, not even for a Grand Slam final. Tests, ODIs, T20s, the Hundred, the
  IPL and women's cricket are plenty.
  Do NOT cover the same Test day by day. ESPNcricinfo rewrites one match-report
  URL for the whole match, so day four has the same link as day three and the
  build blocks it — correctly. Cover a match once, at its decisive moment, and
  otherwise find a different match, series or story.
- **Tech** — Techmeme (fine as a free aggregator even when it cites a paywalled
  outlet), 404 Media, TechCrunch, The Verge, ProPublica, Axios.
- **Entertainment & Culture** — criticism and industry, never gossip.
  Scroll.in (Reel), NPR, trade wire coverage. Avoid Variety, Hollywood Reporter,
  Vulture and The Ringer unless the specific piece loads free.
- **Science** — see below.
- **Philosophy** — Aeon, Philosophy Now, IAI News, Big Think, Essentia
  Foundation, Prabuddha Bharata, Vedanta Kesari.
- **Travel (general)** — Condé Nast Traveller, Lonely Planet, Travel + Leisure.
- **Travel (wildlife)** — Mongabay, BBC Wildlife, Audubon, Cornell Lab, IUCN,
  and nature features from Smithsonian, Atlas Obscura or NPR.
- **Happy Story** — Smithsonian, Atlas Obscura, NPR, BBC, The Marginalian,
  Reasons to be Cheerful.

## Sections

**US Politics, Geopolitics, Cricket** — order `top` by importance: the first item
becomes the day's lede for that section, set at full width. Put the genuinely
biggest story first, and do not promote a middling one to fill the slot; a thin
section stays flat automatically.

**Apu's Corner** — India leads, then Bengal (1-3 items), Travel (exactly 2: one
general, one wildlife/nature), and A Happy Story (exactly 1). The Happy Story is
an easter egg: one beautiful, unusual, true story about people, told with real
narrative depth. Not news-of-the-weird, not a listicle of kind acts. Historical
stories are welcome and often better than anything from the last 24 hours.

**Technology desk** — Top Tech items carry a "Why it matters for you" note aimed
at a product manager building technical fluency. Tech 101 explains one concept
from the day's stories in plain English.

**Science** — its own desk, NOT a consciousness desk. Every edition needs one
item tagged `"kind": "chemistry"` and one tagged `"kind": "space"`. Beyond those,
range freely: biology, climate, materials, medicine, physics, neuroscience.
Sources: ScienceDaily, Quanta, Ars Technica science, NASA/ESA, Chemistry World,
Phys.org, university press offices. Avoid nature.com article links (paywalled).

**Philosophy** — 2-4 items. Rotate genuinely: at most one Ramakrishna Math piece
per edition and only when something new ran; at most one contemporary
idealism/panpsychism item (Kastrup, Goff, Hoffman, Strawson); and at least one
item on a question that is NOT consciousness — free will, personal identity,
ethics, epistemology, philosophy of science, political philosophy, language.
Philosophy 101 explains one concept in plain English.

**From the Field** — the photography desk. Never news content, never captioned
with a species or location that hasn't been verified.

## When a source will not load

Several named sources block automated fetching outright: ESPNcricinfo, Telegraph
India, ABP Live, The Verge, Foreign Policy and Mother Jones have all returned 403.
This is not a reason to fabricate, and not a reason to leave a section empty.

- Find the same story at a fetchable outlet and link that instead.
- Cricket, when ESPNcricinfo will not open: BBC Sport, The Guardian's cricket
  pages, Cricbuzz, or the ICC site.
- Bengal, when Telegraph India and ABP Live will not open: The Federal's West
  Bengal desk, Millennium Post, The Statesman, Scroll.in. The ABP-family
  preference is a preference, not a requirement — a verified story from another
  approved source beats an unverified ABP one every time.
- If you can only see a search snippet, write only what the snippet supports, and
  say in your report which items rest on snippets rather than the full article.
- Never assert a detail you have not seen. A shorter section is always the right
  answer over an invented one.

## Naming an outlet

One exact `source` string per outlet, every edition. Sub-brands ("Scroll.in
(Reel)") split the diversity tally and quietly evade the 3-per-outlet cap. If the
piece is wire copy on a syndicating site, name the site being linked.

## Freshness

Last 24 hours, except where a rule above says otherwise. Check the last two or
three editions before finalising: `build.py` blocks a repeated URL, but it cannot
tell that you have covered the same angle of an ongoing story three days running.
Find the new development, not the same piece rewritten.
