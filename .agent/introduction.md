# 👋 Introduction — Beat Saber Deluxe (PS4 Custom Songs)

**You are a new agent picking up this project.** This file is the orientation:
what the project is, where everything lives, how work gets done here, and
what to read next. It exists so that a lost conversation never loses the work.

---

## 1. What this project is

**Beat Saber Deluxe** replaces the audio + beatmaps of any song in the PS4
version of Beat Saber (CUSA12878, patch 2.04) with community-made custom
songs from BeatSaver — without touching the game's executable. It runs on a
**jailbroken PS4 with GoldHEN** and uses GoldHEN's file-redirection feature
(the plugin redirects game file opens to files we deploy over FTP).

Three components, versioned independently:

| Component | What it is | Where |
|---|---|---|
| **Plugin** (`v0.80XX`) | GoldHEN PRX in C++; hooks `open()`/`fopen`, swaps UI text via IL2CPP MoveNext hook, reads `features.json` | `beat_saber_deluxe/src/main.cpp`, built by `make` (OpenOrbis toolchain) |
| **Pipeline** (`v0.53XX`) | Python: downloads from BeatSaver, converts audio (FSB5 PCM16) + beatmaps (V2/V3/V4→PS4 V3), builds AssetBundles, surgically patches music-pack bundles + the Addressables catalog, deploys over FTP, self-validates | `beat_saber_deluxe/tools/full_custom_song_pipeline.py` (the ONE entry point) |
| **Web app** (`0.6.X`) | FastAPI local UI + GitHub Pages static build — a thin layer over the pipeline CLI (every button = one pipeline subprocess) | `beat_saber_deluxe/webapp/` |

**Current state (Oct 2026):** Milestones M0–M10 complete. 47 custom songs
across 5 music packs live on the user's PS4 (Britney Spears, Rolling Stones,
Lizzo, Billie Eilish, Camellia), each showing 4 gameplay modes
(Standard/OneSaber/NoArrows/90Degree), with in-game song previews that play
the custom song's own audio (M10). The web app ships in the release and is
hosted on GitHub Pages.

## 2. Hardware & environment (READ THIS — it's unusual)

- The user's real **PS4** (FW 9.00, GoldHEN 2.3/2.4b, FTP port 2121, IP in
  `beat_saber_deluxe/ps4_config.json`) is the test target. It is often
  **powered off** — ask the user to power it on for hardware tests; never
  assume it's reachable.
- Development happens in a **devcontainer** at `/workspace`. The decrypted
  game dump lives at `/workspace/ps4_dump/CUSA12878-patch` (user-supplied,
  never committed — copyrighted).
- **Danger Mode guardrails are active** (see CLAUDE.md): git commits/pushes/
  tags/merges are FORBIDDEN for you. You stage changes + suggest commit
  messages; the USER commits and pushes. `gh` is read-only except PR
  description updates (via `gh api ... --raw-field`, never `--field`).
- **CLAUDE.md is the law.** Read it first. Key rules: transcripts before
  every response (§0.5), experiment-log + project-summary + KB updates every
  cycle (§1), full test suite before presenting (§2), version bumps +
  changelogs for every change (§3.2), feature flags gate every feature.

## 3. The five files you must read first

1. **`/workspace/CLAUDE.md`** — all operating rules (guardrails, docs duties).
2. **`.agent/project_summary.md`** — one-screen current status; the Status
   line is the project's heartbeat.
3. **`.agent/roadmap.md`** — milestones M0–M10 (done) + what's planned next
   (M3 note colors, and any new feature the user picks). **Pick new work
   here.**
4. **`.agent/context.yml`** — compact quick-reference: versions, commands,
   architecture, paths.
5. **`.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`** — the
   ACTIVE experiment log (current feature only). Read the last few entries
   to know where things stand. **Experiment numbers are globally sequential
   (next number: check the last entry +1).** Archived logs live in
   `experiment_log_archive/` (read-only).

Then skim **`.agent/llm-wiki-knowledge-base/index.md`** — the compiled
knowledge base. Every durable lesson is there: FSB5 PCM16 (the only working
audio codec — Vorbis/HEVAG are blocked), the catalog CRC validation trap
(CE-34878-0), pack-bundle patching, lftp's pitfalls, surrogateescape
decoding, preview architecture (`song-previews`), etc. **Consult it before
designing anything** — this project has already made most mistakes once.

## 4. How a work cycle goes

1. **User picks a feature** from the roadmap (or reports a bug). You write a
   plan in `.agent/plans/<feature>.md` FIRST for anything non-trivial.
2. **Research before code**: dump.cs analysis
   (`/workspace/il2cpp_output/dump.cs`), bundle forensics with UnityPy,
   KB consultation. Verify claims against real bytes, not assumptions.
3. **Implement** in the pipeline/plugin/webapp. New/experimental scripts go
   in `beat_saber_deluxe/development/scripts/` first, production only after
   proven. Every behavior change = version bump + changelog entry + tests.
4. **Test hermetically** (`cd beat_saber_deluxe && python3 -m pytest tests/
   -q`; currently 864 tests) + `python3 -m ruff check tools/ tests/`.
   Hardware-dependent tests self-skip via gates (HAS_DUMP / HAS_BUILT).
5. **Deploy + hardware-validate** via pipeline flags only (user directive:
   NO manual FTP file manipulation). The PS4's own post-deploy validation
   and `--verify-ps4` (which now checks every deployed bundle's actual CRC
   against the catalog) must pass.
6. **Document**: experiment-log entry (Exp N+1), transcript cycle append
   (`.agent/transcripts/<date>_<slug>.md` — one file per session), project
   summary status line, KB pages if durable knowledge, roadmap checkbox.
7. **Stage** everything (`git add` fine-grained) + suggest a commit message.
   Never commit.

### Release flow (when a milestone lands)

1. User merges the feature branch to `main`, pushes a tag
   `v<plugin>-pipeline-<pipeline>-webapp-<webapp>`.
2. CI (`.github/workflows/plugin-build.yml`) builds both plugin PRXs
   (FSELF format) + the release zip (tools, webapp, docs, example scripts).
3. **You validate the release**: download the zip, audit contents, boot the
   webapp from the extraction, run a `--deploy-full` from the SHIPPED
   pipeline against the live PS4, run `--verify-ps4`. The full procedure:
   `.agent/docs/release-validation-test-procedure.md` (companion script
   runs it automatically). Then audit README/CI_RELEASE/KB/docs currency.
4. Watch out: always test from a **clean extraction** of the zip (not the
   repo) — layout bugs hide when the dev checkout sits beside you.

## 5. The invariants (violating any of these crashes the game)

- **The catalog/bundle CRC triple**: a patched pack bundle must ALWAYS ship
  with the merged catalog that describes it AND redirects naming the exact
  deployed variant. Any drift = CE-34878-0 at boot (lazy CRC validation at
  the pack scan). `--deploy-full` and `--verify-ps4` enforce this; never
  deploy bundle/catalog/redirects separately.
- **FSB5 PCM16 only** (codec 2) for audio. Stock Vorbis (15) is
  encoder-blocked; HEVAG is blocked. Preview clips mirror the full-song
  AudioClip field template exactly.
- **Never trust size equality as content identity** (two builds of the same
  variant share size); uploads skip only on same-session records.
- **Feature flags gate everything** (`features.json`, defaults false except
  `enable_plugin`). New plugin behavior needs a flag + pipeline
  `DEFAULT_FEATURES` key + webapp surface. The boot toast counts them.
- **Pull-before-push** for every PS4 state file (redirects.json,
  features.json, song_metadata.json): always base writes on the LIVE state,
  abort on read failure — a stale local push has wiped live state twice.
- **`_ftp_quote()` every lftp path** (`&` splits paths); never trust lftp's
  exit code (verify via remote listing read-back).

## 6. Where things live

```
/workspace/
├── CLAUDE.md                     ← THE RULES
├── README.md                     ← user-facing docs (keep current)
├── beat_saber_deluxe/
│   ├── src/main.cpp              ← plugin source (v0.80XX)
│   ├── tools/full_custom_song_pipeline.py  ← THE pipeline (v0.53XX)
│   ├── tools/song_previews.py    ← M10 preview patcher
│   ├── tools/build_pack_mode_bundles.py   ← pack bundle + catalog patching
│   ├── webapp/                   ← web app (0.6.X)
│   ├── tests/                    ← pytest suite (864)
│   ├── VERSION                   ← pipeline version
│   ├── CHANGELOG-*.md, CI_RELEASE.md
│   └── custom_songs/             ← built song bundles (local cache)
├── ps4_dump/CUSA12878-patch/     ← the decrypted game dump (user-supplied)
├── .agent/
│   ├── project_summary.md        ← status heartbeat
│   ├── roadmap.md                ← milestones + next steps
│   ├── plans/                    ← per-feature plans
│   ├── transcripts/               ← session transcripts (MANDATORY)
│   ├── docs/release-validation-test-procedure.{md,sh}
│   └── llm-wiki-knowledge-base/  ← the durable KB (index.md first)
├── .ai_memory/beat-saber-ps4-custom-songs/
│   ├── experiment_log.md         ← ACTIVE log (current feature)
│   └── experiment_log_archive/   ← past features (read-only)
└── docs/example-scripts/         ← 69 ready-to-run per-pack examples
```

## 7. Current versions & next steps (as of 2026-10-12)

- Plugin **v0.8048** · Pipeline **v0.5362** · Web app **0.6.6**
- Latest release: **`v0.8048-pipeline-0.5362-webapp-0.6.6`** (LIVE, fully validated;
  M10 song previews shipped — 46 previews across 5 packs, hardware-confirmed).
- M10 (song previews) is SHIPPED (merged PR #7, release live). The next
  feature is whatever the user picks from the roadmap (M3 note-color
  customization is the standing candidate; the user may also choose fresh
  ideas).
- Open PR during release flow: check `gh pr list` — update its description
  per `/workspace/.claude/prompts/update-pr-description.prompt` (surgical
  edits, `--raw-field` only, user approval before pushing).

**Welcome aboard. Read the five files, check the summary's Status line, and
pick up where the last experiment left off.**
