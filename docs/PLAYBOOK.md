# Playbook: ideas, UI, diagrams + deck, beyond-scope

Four topics only. Tailored to our product (staffing planner, FastAPI + Next.js, co-pilot).

---

## 1. Brainstorming ideas

Goal: many options fast, cut by rubric, pick one "wow" + one "proof". Humans choose. AI generates and attacks.

### Steps (60-90 min, whole team)

1. **Constraint sheet (10 min).** Paste into one doc, give to AI every time:
   - Track brief + judging criteria (verbatim)
   - Rule: AI assists, people decide
   - Time left, team skills, what already works
   - Non-goals (no passenger data, no dispatch)
2. **Diverge with lenses (20 min).** Ask AI for 5 ideas per lens, not "give ideas":
   - Who else touches this system? (customers, line crew, dispatchers, airport ops)
   - What changes minute by minute? (real-time, events, delays)
   - What medium sells it? (3D, map, voice, simulation, live replay)
   - What can AI do that a spreadsheet cannot? (what-if by chat, risk, explain)
   - What would a judge remember in one image?
3. **Score (15 min).** Table: idea | rubric items it moves (innovation, accuracy, practical, human-in-command) | effort (h) | demo risk | "visual in 5 sec?". Score 1-5 each. Humans vote, AI does not break ties.
4. **Attack (10 min).** Ask AI to argue each top-5 idea scores LOW with judges. Drop what survives badly.
5. **Pick portfolio.** 1 core (must work), 1 wow (visual, bounded), 1 stretch (only if ahead). Everything else goes in "future work" slide.
6. **Pre-mortem again at 50% time.**

### Prompts

```
[constraint sheet]
Lens: "who else touches this system". Give 5 distinct ideas. For each: user, what they do, what changes in the planner, rubric items moved, build effort in hours, biggest risk. No generic ideas.
```
```
Here are our top 5 ideas and rubric. Act as a skeptical judge. For each, list the 3 most likely reasons you score it low. Then say which survives and why.
```
```
Rank by (rubric gain)/(effort). Show the table. Flag any idea that weakens "AI assists, people decide".
```

### Rules
- Idea must show in the demo in under 20 seconds.
- Reality check each idea against the rubric. Cool but off-rubric = cut.
- Judges never see brainstorm. They see result. Do not over-spend time here.

---

## 2. High-quality professional website

Cause of "looks student-made": no design system, inconsistent spacing, default charts, no empty/loading states, wall of numbers. Fix with system + review loop.

### A. Design system before pages (30 min)
Write one file (`frontend/app/globals.css` tokens + `docs` note if needed):
- **Color:** 1 background, 2 surfaces, 1 text, 1 muted, 1 accent, 3 status (ok/warn/risk). No more. Contrast >= 4.5:1.
- **Type:** one font family + mono for numbers. Scale: 12 / 14 / 16 / 20 / 28 / 40. Numbers big, labels small + muted.
- **Spacing:** 4px grid (4, 8, 12, 16, 24, 32). Cards same radius and padding everywhere.
- **Elevation:** borders over shadows; one level of glow for the primary KPI only.
- **Motion:** 150-250 ms ease-out on hover/state change. Chart enter once. No bouncing.

### B. Layout rules for a dashboard
- Visual hierarchy: 1 hero number, 3-4 KPI cards, then charts. Top-left = most important.
- One screen at 1080p without scrolling for the demo view. Extra detail in tabs/drawers.
- Chart per question: line for time, bar for categories, heatmap for hour-by-day risk. Sort bars. Same scale across comparisons (baseline vs plan).
- Always label units, uncertainty (band + legend), and "SYNTHETIC DATA".
- Every panel has: loading, empty, error state. No blank boxes.
- Primary action (Approve) visually dominant; destructive/secondary muted.

### C. Build loop with AI (per component, not whole page)
1. Give AI: design tokens + a reference screenshot (a dashboard you like: Linear, Vercel, Stripe, Grafana).
2. Ask for ONE component (e.g. KPI card). Accept only after it matches tokens.
3. Screenshot with Playwright (already installed) at 1920x1080 and 1280x720.
4. Feed screenshot back: "Critique against these tokens: hierarchy, contrast, spacing, clutter, alignment. List fixes, then apply."
5. Repeat 2-3 rounds per page. Stop when no critique item is above "nit".
6. Use shadcn/ui primitives + Tailwind 4 tokens instead of hand-rolled controls (accessible, consistent).

### D. Polish checklist (run before freeze)
- [ ] Hero states user + problem + data badge in one glance
- [ ] No default browser buttons/fonts/scrollbars
- [ ] Hover, focus, active, disabled states exist
- [ ] Numbers use tabular figures and thousands separators
- [ ] Legible from 3 m (min 16 px body on projector, KPI 40 px)
- [ ] Dark/light decided once, no half-themed parts
- [ ] Zero console errors; no layout jump on load
- [ ] Favicon + page title set
- [ ] Demo path works with network off (cached/seeded)

### Prompt
```
Design tokens: [paste]. Reference: [screenshot]. Build only <KpiCard> in shadcn/Tailwind 4. Props: label, value, delta, unit, status. Include loading + empty state. No new colors or fonts.
```
```
Here is a screenshot of the page. Critique against the tokens: hierarchy, contrast, spacing, alignment, clutter. Max 8 fixes, ordered by impact. Then apply them.
```

---

## 3. Diagrams + presentation that explain the product

Winning decks have: one theme, one visual language, diagrams that carry the technical story, and a requirement-to-feature trace. Build the story first, slides second.

### A. Pick a theme (30 min)
One sentence, used on every slide and in the speech. Example for us:
> "From surge to roster in minutes - AI proposes, people decide."

Derive from it: one color accent, one recurring visual (e.g. the baseline-vs-plan seat chart), one recurring phrase ("AI proposes, people decide").

### B. Narrative arc (6-8 slides, ~3 min)
Titles are takeaways, not labels ("Event week breaks the ordinary roster", not "Problem").

| # | Slide | Content | Visual |
|---|---|---|---|
| 1 | Hook | One number or scene: Super Bowl week, X arrivals vs ordinary | Big stat + LA image |
| 2 | Problem + user | FBO ops manager, ordinary roster understaffs the surge | Before chart (short seat-hours) |
| 3 | Solution at a glance | Forecast -> plan -> risk -> human approval | **Diagram 1: flow** |
| 4 | How it works (technical) | Data, forecast, solver, simulation, co-pilot | **Diagram 2: architecture** |
| 5 | AI + human boundary | What AI does / never does / human-only | **Diagram 3: decision gate** |
| 6 | Results | Accuracy vs naive, coverage, cost, uncertainty | Real chart screenshot |
| 7 | Requirements met | Judging item -> feature -> evidence | **Table: traceability** |
| 8 | Beyond + next | Extensions, real-data validation, LA 2028 | Roadmap strip |

Demo goes between 4 and 6 (or replaces 6 with live app). Deck = support, demo = proof.

### C. Diagrams to produce (5)
1. **Flow diagram** (user journey): scenario -> forecast -> plan -> risk -> approve/edit/reject -> audit.
2. **Architecture**: frontend, FastAPI, forecaster, workload model, CP-SAT solver, Monte Carlo, co-pilot (OpenRouter tools), config/assumptions, audit log. Arrows labeled with data (e.g. "P10/P50/P90 arrivals").
3. **AI/Human boundary**: three columns: AI proposes (forecast, roster, risk, explain) | Human decides (approve, edit, reject, safety) | Never (dispatch, aircraft movement, passenger data).
4. **Method/pipeline**: how demand becomes staffing: arrivals + parking + fuel -> workload minutes -> required seats -> solver -> roster. Shows "staffing focus with drivers".
5. **Requirement trace**: table, not diagram: each hackathon requirement -> feature -> where in demo.

Rules: one message per diagram, 5-9 elements, labels on arrows, consistent shapes (AI = accent color, human = neutral, external = dashed).

### D. Generating diagrams with AI
- **Mermaid** for the draft: plain text, easy to review/fix, Claude knows it well. Good for flow + pipeline.
- **Excalidraw** for the polished version: Claude writes `.excalidraw` JSON (needs bound labels; check arrows). Mermaid can import into Excalidraw. Skill: `npx -y skills add coleam00/excalidraw-diagram-skill --skill excalidraw-diagram --agent claude-code`.
- **D2** if you want better auto-layout from text.
- **Hand SVG/HTML inside the deck** for the hero visuals (full control, matches theme, no export issues).
- **Verify against code.** AI draws plausible diagrams. Feed it the real structure (`backend/app` module list, endpoints from `main.py`) and ask it to diagram that. Team member checks every arrow.

Prompt:
```
Here are our modules and endpoints: [paste]. Draw a Mermaid flowchart (left to right), max 9 nodes. Group into Frontend / Backend / AI / Human gate. Label every arrow with the data. No node that is not in the code.
```
Then: "Convert to Excalidraw JSON with bound labels, colors: AI=#accent, human=#neutral."

### E. Generating the deck
Options (pick one, do not mix):
- **HTML deck** via the `power-design` skill or Claude Design: matches website style, embeds live screenshots and SVG. Best control, needs a browser to present.
- **PPTX** via the `pptx` skill: safest for venue laptops/projectors.

Workflow:
1. Write script first (section 4 of speech) and the numbers table from the real app.
2. Prompt: one slide per script beat, title = takeaway, <= 20 words, one visual, speaker notes in notes not on slide.
3. Insert real screenshots (Playwright), diagrams from D.
4. Check every number against the app.
5. Export PDF as backup.
6. Rehearse x5 with timer; cut slides, not speech speed.

Prompt:
```
Theme: "[sentence]". Palette/type: [tokens]. Script: [paste]. Build slide N of M: title (takeaway), one visual [describe], <= 20 words, speaker notes. Match the website style.
```

### F. Technical story to tell (the "how it was built" 60 s)
Say in this order: data (synthetic, seeded, assumptions file) -> forecast (Poisson GBM, bands, beats naive) -> workload (arrivals + parking + fuel -> seats) -> solver (CP-SAT, shift rules) -> risk (Monte Carlo) -> co-pilot (tools only, no invented numbers) -> human gate (approve/edit/reject + audit). One diagram supports it.

---

## 4. Going beyond the requirements with AI

Rule: extras must strengthen the core story, not replace it. Core demo first. Each extra is time-boxed and cut if it is not stable by 75% time. Humans stay in command in every extra.

### Ranked options for us

| Extra | Wow | Effort | Risk | Rubric link |
|---|---|---|---|---|
| **A. Customer request portal** (second site) | High | Medium (1 day-ish) | Medium | Practical prep, innovation |
| **B. 3D apron twin driven by the plan** | Very high | Medium-High | Medium-High | Innovation, instant understanding |
| **C. Live replay / "storm hits" scenario run** | High | Low-Medium | Low | Uncertainty, practical |
| **D. Morning briefing export (PDF/MD)** | Medium | Low | Low | Practical prep |
| **E. Voice co-pilot** | Medium | Medium | High (venue noise) | Innovation |
| **F. LA 2028 profile swap** | Medium | Low | Low | Stretch goal in brief |

Recommend: C + D first (cheap, safe), then A, then B only if A is stable.

### A. Customer portal (airport-facing site)
What: second page/app where an operator/pilot/flight planner submits a **planning request** (aircraft category, ETA window, services: fuel / ramp / parking duration). No passenger or crew data.
Flow: portal -> backend event -> demand forecast uplift (arrival added to scenario) -> replan -> manager sees "3 new requests, +2 ramp seats Fri 14:00" -> approves. Customer sees "request received, subject to FBO confirmation".
Human in command: portal never changes the roster. It only creates **demand signals**; manager approves staffing; confirming the customer is a human action.
Build:
- `POST /requests` (schema: aircraft_category, eta_start, eta_end, services). Reuse `create_scenario` disruption type `spike`.
- `GET /stream` Server-Sent Events (simple, one-way) -> manager dashboard updates live. WebSocket only if needed.
- Frontend route `/request` with a clean form; manager dashboard shows an inbox + auto-replan toast.
- Seed 5 pre-made requests to avoid empty demo.
Demo beat (20 s): submit request on phone/second tab -> manager screen updates -> risk heatmap changes -> approve.
Risks: scope creep (accounts/auth: skip, use a code), spam: rate limit + note "prototype".

### B. 3D apron twin
What: a stylized 3D top-down/isometric apron: parking stands, aircraft blocks, staff dots by role per hour, color by understaffing risk, timeline scrubber (Mon-Sun).
Stack: React Three Fiber + drei in the existing Next.js app. Data comes from current API (plan + risk), no new backend.
Keep it low-poly and abstract (boxes, simple aircraft silhouettes). Do not chase realism.
Build:
1. Ask AI for a `<ApronScene>` with a ground plane, N stands, instanced aircraft meshes.
2. Bind to hour index: aircraft count from forecast, staff dots from roster, tint from risk.
3. Timeline slider drives the scene; click hour -> shows seats required vs supplied.
4. Camera: fixed good angle + slow auto-orbit; one hero shot for the deck.
5. Performance: instancing, no shadows beyond one light, cap 60 objects.
Fallback: pre-record a 20 s capture of the 3D view for the video/deck. Check on the demo laptop GPU.
Warning: an unfinished 3D scene looks worse than none. Timebox 4-6 h; if scene does not read clearly by then, cut.

### C. Live replay / storm scenario
Scripted event: scrub time forward, disruptions drop in (delay, spike), plan changes, risk updates, human approves. Uses existing endpoints, mostly frontend. Highest wow per hour.

### D. Briefing export
One click -> markdown/PDF: plan summary, assumptions, risks, decisions + audit entries. Shows "practical preparation" and auditability.

### How to use AI to build extras safely
- Spec first (one paragraph + acceptance check), then code. One extra at a time on a branch.
- Reuse existing APIs; avoid new data models where possible.
- Merge only if demo path still passes and tests are green.
- Add a feature flag / separate route so a broken extra cannot break the main demo.
- Every extra gets one slide line and one sentence in the pitch: "what it adds, what stays human".
- Record each extra as a short clip as soon as it works.

### Guardrails
- Any extra that touches people/aircraft stays recommend-only.
- No real customer data; request forms collect planning-level fields only.
- Label synthetic. Label unverified.
- If it cannot be explained in one sentence, cut it.
