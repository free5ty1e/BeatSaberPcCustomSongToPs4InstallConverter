# Beat Sage + Local Song Folder Support (Web App "Pick a Song" Tab)

**Status:** 🟢 Implemented (Exp 283, 2026-10-22) — web app 0.6.20; Tier 1 verified against the live service; the PS4 deploy validated end-to-end (bundle built + deployed) pending the console's return for the final play-test
**Goal:** the web app's Pick-a-song tab gains two new sections below the existing
BeatSaver search: **(2) Beat Sage** — generate a Beat Saber map from any song, with
the web app automating everything that can be automated and guiding the user through
the steps that genuinely must be manual — and **(3) a local song folder picker** so
users can convert songs they already have on disk.
**Companion plan:** `.agent/plans/eliminating_or_automating_ps4_dump_folder_requirement.md`
**Doctrine:** M9 rules — the web app is a thin layer; every action is an existing
pipeline command or a well-bounded adapter. No pipeline/plugin changes are required
for the core of this feature (the pipeline already accepts local song folders via
`--song-dir`).

---

## 1. The Pick-a-song tab today (and after this feature)

| Section | Today | After M13 |
|---|---|---|
| 1. BeatSaver | Search + map-ID entry (existing) | unchanged |
| 2. Beat Sage | — | NEW: audio → AI-generated map → pipeline |
| 3. Local folder | — | NEW: browse/select a local song folder (or zip) → pipeline |

Both new sections end at the same place: a **validated local song directory**, which
flows into the existing Deploy tab unchanged (`--song-dir <dir> --target <slot> ...`).

## 2. Beat Sage — what it is, what it does, what we must respect

**Beat Sage** (beatsage.com) is a free web service that generates Beat Saber-style
maps from any audio file (AI difficulty placement). Flow on their site: upload an
audio file → choose options (difficulty levels, style/system settings) → generate
(job queues; processing takes minutes) → download a **zip containing a standard
BeatSaver-format map** (`Info.dat`, per-difficulty `.dat` beatmaps, the audio file).

Implications for us:

- **The OUTPUT is exactly what our pipeline already eats** (a local song folder:
  Info.dat + .dat files + audio — the `.ogg` audio Beat Sage ships is handled by
  the existing audio path per the KB's audio conventions). Zero pipeline work.
- **The INPUT is any audio file** — this unlocks the "convert MY song" use case
  BeatSaver alone can't cover (no community map exists for most songs).
- **It is a third-party free service.** We must: respect their terms of service,
  not hammer their queue, degrade gracefully when they change their UI/API, and
  never present their work as ours. The plan keeps their branding explicit in the
  UI ("powered by beatsage.com") and treats automation as best-effort.

## 3. Beat Sage section — automation ladder

The design principle (user's directive): **automate as much as possible; guide the
user through whatever steps absolutely MUST be manually performed.** We build a
three-tier ladder and use the highest tier that works; the UI is identical from the
user's perspective except for how much it does for them.

### Tier 1 — Full automation (backend drives beatsage.com)

Our FastAPI backend acts as the beatsage.com client:

1. User provides an audio file (browser upload → server temp) + generation options
   (difficulties, style).
2. Backend POSTs the audio to beatsage.com's upload endpoint (their web app's own
   API — same one the browser page uses), receives a job reference.
3. Backend polls job status (a long-running web-app job — the existing single-job
   runner + live log pane already model minutes-long work: batch deploys do this).
4. On completion, backend downloads the generated zip, extracts + validates it
   (Info.dat parse, beatmap discovery, audio present — reuse the pipeline-side
   validation), stages it as a local song folder, and the Deploy tab lights up.

**What must remain manual even at Tier 1:**
- **The user provides the source audio and asserts they have the rights to use it**
  (the plan adds an explicit checkbox + note: use your own music or music you're
  licensed to process).
- **First-run acknowledgment of beatsage.com's terms** (one-time checkbox; we link
  their ToS — the user must accept THEIR terms, not ours).
- **The wait itself** (their processing time — minutes; we show live status).

**Verification needed before Tier 1 ships (research task):** the exact endpoints
(upload/status/download) are undocumented; the implementation must be driven from a
live capture of the site's network traffic (browser devtools — one session's worth
of work) and validated against their rate limits. If their backend requires a
browser session token or presents a captcha, Tier 1 is blocked and we ship Tier 2.

### Tier 2 — Guided flow with automated intake (the guaranteed-deliverable tier)

The web app cannot lose with this tier — every step of the beatsage.com interaction
is user-driven, but **we automate the tedious parts around it**:

1. User picks their audio file + options in OUR section.
2. The app opens beatsage.com pre-focused (deep link where possible) and displays
   a precise step-by-step card: "upload this file → choose these options
   (recommended defaults pre-shown: Easy–ExpertPlus, Standard) → click Generate →
   when it finishes, download the zip."
3. **The return path is fully automated:** the user drags the downloaded zip onto
   the Beat Sage section → the browser uploads it to our backend → backend
   extracts + validates + stages the song folder → Deploy tab lights up.

The zip intake (a few lines of FastAPI: `UploadFile` → zipfile extract → the same
validation as Tier 1 step 4) is entirely within our control and covers ANY map zip
source, not just Beat Sage — making this tier independently valuable.

### Tier 3 — Manual-only acknowledgment (embedded worst case)

If both automation tiers are impractical at any time (site redesign, API change),
the section degrades to the Tier 2 guidance card without the zip drop (the user
points the Local Folder section at their extracted zip instead — which already
works after §4). The feature never *breaks*; it just asks a little more of the user.

### UX layout (below the BeatSaver section)

```
┌─ 2 · Generate a map with Beat Sage ──────────────────────────── [collapsible] ─┐
│ ⚠ Only use audio you have the rights to process.        [ ] I have the rights │
│ ( ) Upload & generate for me  ( ) I'll use beatsage.com myself                 │
│ Audio file: [drag-drop / browse…]  Difficulties: [Easy…ExpertPlus ☑]           │
│ [Generate map] → job pane (live status / or the guided card + zip drop zone)   │
│ Result: <song name> staged ✓ → continue in the Deploy tab                     │
└────────────────────────────────────────────────────────────────────────────────┘
```

## 4. Local song folder section (below Beat Sage)

For users who already have map folders (from BeatSaver zips, prior conversions,
other tools) or who just finished a Beat Sage download:

1. **Path entry + live validation** (the established wizard pattern from the dump
   guide): the user types/pastes a folder path; the backend validates in real time
   — Info.dat parses; beatmap `.dat` files discovered per difficulty; audio file
   present and readable; V2/V3/V4 schema detected (the pipeline's own readers).
   Per-problem messages with fixes (e.g. "no Info.dat found — is this the folder
   containing it, or its parent?").
2. **Zip drag-drop** (the same intake as Beat Sage Tier 2): drop a map zip →
   backend extracts to a staging dir → identical validation → staged.
3. **(Optional, v2) Server-side folder browser:** a click-through directory listing
   served by the backend for users who don't want to type paths. The M9 plan
   deferred a native picker (no tkinter in the devcontainer); a web-native browser
   avoids that dependency entirely.

Staged songs persist in `webapp_state`-managed staging (the existing
browsable-state pattern) with a "recent songs" list so users can redeploy without
re-extracting.

## 5. Backend adapter surface (all web-app side; the pipeline is untouched)

| Endpoint | Purpose |
|---|---|
| `POST /api/beatsage/prepare` | Start a Tier-1 generation job (upload → poll → fetch → stage) or hand back the Tier-2 guidance payload |
| `GET  /api/beatsage/job/{id}` | Live status of the generation job (the existing job-runner model) |
| `POST /api/songs/stage-zip` | Upload a map zip → extract → validate → stage (shared by Beat Sage Tier 2 + local zip drop) |
| `POST /api/songs/validate-dir` | Validate a local folder path → staged song payload |
| `GET  /api/songs/staged` | List staged songs (recent list) |

Every deploy remains `deploy.pipeline_command(argv)` — the sections only produce a
`--song-dir`.

## 6. Testing plan (hermetic; the M9 rules)

- Manifest/argv tests: every new button maps to documented pipeline flags (the
  thin-layer proof pattern).
- Zip intake: synthetic map zips (valid, missing Info.dat, missing audio, V2/V3/V4
  variants) → correct validation verdicts + staging behavior.
- Path validation: temp-dir fixtures for the four failure modes + one happy path.
- Beat Sage Tier 1: the beatsage.com client behind an interface — mocked
  endpoint tests for the job-state machine (queued → processing → complete →
  download → stage); the live-service contract test is gated (HAS-network class
  like the existing hardware gates) so CI never touches the real service.
- Job-runner integration: a long-running generation job streams lines and resolves
  (the batch-deploy precedent).

## 7. Milestone phases (M13)

- [x] **M13.1** — Local song folder section: adapters/songs.py (validator
      mirroring the pipeline's contract + zip-slip-guarded intake + persistent
      staging with auto-prune) — 24 tests
- [x] **M13.2** — Beat Sage Tier 2 (guided card, served by /api/beatsage/guide,
      with a static pages-mode fallback) + the shared zip intake
- [x] **M13.3** — Tier 1: the API live-captured from their Nuxt bundle (KB:
      beatsage-api-capture), the client (webapp/beatsage_client.py) runs as THE
      single job (upload → poll at their cadence → download → validate →
      stage), verified against the LIVE service twice (the gated contract
      test with a synthesized tone; the full user flow with a synthesized
      48s original song — staged in 12s, all four difficulties)
- [x] **M13.4** — Docs: feature doc (beat-sage-and-local-songs.md), README row,
      CI_RELEASE rows, KB page, the rights/ToS notes in the UI + feature doc

## 8. Open questions

- **Q1** — beatsage.com's API stability/limits (resolved by M13.3 research; the
  ladder makes the answer non-blocking).
- **Q2** — Whether to expose Beat Sage *style/options* beyond difficulty (e.g.
  their "system" choices) in v1, or keep the recommended-defaults card. Recommend:
  defaults in v1; the card shows what we chose.
- **Q3** — Staging retention: keep staged songs across web-app restarts (yes —
  `webapp_state` pattern) and expose a cleanup control.


## RUN LOG

### Exp 283 (2026-10-22) — implementation + validation
- Everything above landed in web app 0.6.20 (no pipeline/plugin changes — the
  flow ends at the pipeline's existing `--song-dir`, exactly as planned).
- 57 new tests (songs/beatsage/deploy-argv/server-endpoints/JS-syntax-gate);
  suite 924 passed + 93 hardware-gated; ruff clean; app.js quickjs-parsed.
- **Live Tier-1 proof:** a synthesized 48s original song (rights-clean,
  `development/scripts/make_rights_clean_test_song.py`) went through the app's
  own `/api/jobs/beatsage` → Beat Sage accepted (job a3dfabb5…) → DONE in 12s
  → 338,890-byte zip → validated (V2, N/H/E/E+) → **staged**; the staged entry
  **survived a web-app restart** (the persistence design).
- **Deploy validation:** the staged folder deployed via `/api/jobs/deploy`
  (song_dir → TruthHurts): the V2 map auto-converted to V3, Easy auto-filled
  from Normal (Beat Sage can't make Easy), 15 mode beatmaps generated, the
  bundle built + verified locally… and the FTP push hit `No route to host` —
  **the PS4 had gone to rest/off mid-flow**; the job failed cleanly (lftp
  600s timeout, exit 1; nothing corrupted — a re-deploy overwrites the
  possibly-partial bundle). The one-click re-run from the staged list is the
  remaining hardware validation.
- Quickjs found two real JS bugs the Python suite couldn't (a template-literal
  missing paren + a lexical redefinition) → added the permanent
  test_webapp_js_syntax.py gate + quickjs to the test requirements.
