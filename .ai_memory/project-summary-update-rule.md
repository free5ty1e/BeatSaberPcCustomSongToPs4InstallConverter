---
name: project-summary-update-rule
description: "Enforcement: always update /workspace/.agent/project_summary.md after every task completion or before reporting to user"
metadata:
  type: feedback
---

## Rule: Update Documentation Before Reporting

**Note:** All project READMEs have been consolidated into a single project-level README at the repo root. No per-module READMEs.

### README update rule: After any experiment that produces a new finding, also update:
- The **"Current Experiment"** section in the project-level README
- Any **ASCII art diagrams** or **usage examples** that are now incorrect
- The **features table** or **status indicators**

**Enforcement:** After every task completion, deployment, experiment result, or significant discovery — and **before** reporting back to the user — update project documentation FIRST.

### Documents to update:

**1. Log retrieval & analysis** (EVERY test cycle — do FIRST, before any other docs)

- **Download the log file** from PS4:
  ```
  lftp -u anonymous, -p 2121 192.168.100.117 -e "get /data/GoldHEN/AFR/CUSA12878/bs_log.txt -o /tmp/bs_log_<version>.txt; quit"
  ```
  If the file doesn't exist (crash before hook initialization), note that.
  
- **Analyze the log** for these key signals:
  - Total line count (estimate duration: ~150 = quick menu, ~750+ = full song play cycle)
  - Redirect markers: `BeatmapLevelsData/startmeup -> /data/GoldHEN/AFR/CUSA12878/<target>` — count occurrences
  - Environment loading: bundles like `therollingstonesenvironment_*` loaded AFTER redirect
  - Other songs: any `BeatmapLevelsData` opens OTHER than startmeup
  - `PlayerData.dat` save at log end (indicates clean return to menu)
  - Error/exception lines: grep for `error`, `exception`, `fail`, `crash`, `assert`
  - Notification count: `grep -c "notification"` — confirms plugin notification fired
  - Save a copy to `/workspace/screenshots/bs_log_<version>.txt` for permanent reference

- **Log findings table** — include a Markdown table in the experiment entry:
  | Signal | Count | Meaning |
  |--------|-------|---------|
  | Redirects | N | Game opened bundle N times |
  | Env loaded | Y/N | Environment rendered correctly |
  | PlayerData saved | Y/N | Clean exit vs crash |
  | Error lines | N | No unexpected issues |

- **Store the log file permanently** — ALWAYS save a copy to `/workspace/screenshots/bs_log_<experiment>.txt`:
  ```bash
  cp /tmp/bs_log_<experiment>.txt /workspace/screenshots/bs_log_<experiment>.txt
  # (if lftp-get /tmp/bs_log_<experiment>.txt was done first)
  ```
  The historical log archive at `/workspace/screenshots/` is a permanent reference. 
  Every experiment that produces a log MUST have a copy stored there.
  Use a descriptive experiment-specific name (e.g., `bs_log_exp112_crash.txt`).

**2. `/workspace/.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`** (EVERY test cycle)

- Add a new entry for each test/experiment with:
  - Test number (sequential)
  - What changed
  - Result (✅ success / ❌ failed / ⏳ pending)
  - What was learned
  - Key log findings (from log analysis above)
- Update the "Working Configuration" section if the build process changes
- Update the "What We Know" section with confirmed findings

**2. `/workspace/.agent/project_summary.md`** (after each significant result)

- **Current Status header** — one-line summary of current state and what's being tested
- **Phase 5 Iterate** — update with latest findings and next steps
- **Workflow sections** — keep deployment commands and test procedure current
- **File Reference** — update if files/changes are made

**3. `/workspace/.agent/roadmap.md`** (after each significant result)

- **Milestone checklists** — mark items as completed (✅), in progress (🚧), or pending (⬜)
- Add new discoveries, tools, and investigations to appropriate sections
- Keep the "Known Issues" section current with what we're actively investigating

**3.5 `/workspace/.ai_memory/beat-saber-ps4-custom-songs/song_testing_log.md`** (after each PS4 test)

- Add entry for each deployed song with sync result, audio format, and issues
- Keep the "Next Test Candidate" section updated

**3.6 `/workspace/.ai_memory/beat-saber-ps4-custom-songs/beat_saber_song_ids.json`** (when new songs are discovered or metadata changes)

- Regenerate when new official bundles are analyzed
- Update when DLC song names become available from addressables

**4. `/workspace/README.md`** (after each significant result)

- **Status header** — update the one-line project status description
- **Current capabilities** — update what's working vs what's still in progress
- **Key findings** — document root causes discovered (e.g., m_Script is just gzip)
- Keep the setup/build/test instructions current

**5. `/workspace/.agent/llm-wiki-knowledge-base/`** (EVERY test cycle — knowledge base maintenance)

- **Mine findings for durable knowledge** — after each experiment result, ask: "What did we learn that will still be true in 6 months?"
  - New root causes or bugs found → add as new page or update existing page
  - Updated fix patterns (code snippets, workflows) → update relevant pages
  - New tooling or commands discovered → add to toolchain page
  - Superseded claims or stale info → revise or remove
  - Cross-reference new findings with existing pages (add `[[links]]`)
- **Pages to potentially update** based on experiment type:
  - Finding a bug? → update [[m-script-gzip-format]] or [[unitypy-serialization]] or create new root-cause page
  - Fixing a feature? → update [[beatmap-conversion-pipeline]] or [[assetbundle-structure]]
  - Build system change? → update [[toolchain-and-build]]
  - Workflow change? → update [[development-workflow]]
- **Check for contradictions** — if new data contradicts an existing claim, flag it with a note on the relevant page
- **Keep index.md current** — if you add a new page, add it to the index catalog
- **Always add a log entry** — append to `log.md` describing what was updated and why

**6. Song selection criteria** (before choosing a new song for deployment)

Song criteria (documented from user preference): songs must have Easy/Normal/Hard difficulties as Standard, 90Degree, or OneSaber beatmaps. 360Degree maps load but are unplayable on PS4 VR (single-camera ~90-degree tracking arc can't handle behind-player notes). See `song_testing_log.md` for the testing table.

**7. Knowledge capture** (every time a root cause or breakthrough is discovered)

- **Check for existing memory**: before creating a new memory file, check if one already covers the topic
- **Save findings as persistent memory**: write a `.md` file in `/workspace/.ai_memory/beat-saber-ps4-custom-songs/` with:
  - The root cause (what was wrong and why)
  - The fix (what change resolved it)
  - Why other approaches didn't work (prevent repeating dead ends)
  - Link related experiments with `[[experiment-id]]`
  - Example: `m_script-gzip-only.md` — "m_Script is just gzip data, no decompressed_size prefix"
- **Update MEMORY.md** with a pointer to the new knowledge file
- **Stage in git** along with experiment log and other docs

**8. `/workspace/.ai_memory/MEMORY.md`** (when new documents are created)

- Add links to new memory files

### Why:

Without this, the documents fall out of sync with reality. The user specifically reviews these to understand current state, and stale info causes confusion and wasted iteration.

### How to apply (in order):

Before reporting to the user:

1. **Download & analyze the PS4 log** (even on crashes — the log shows how far it got)
   - FTP get `bs_log.txt`, save to `/workspace/screenshots/bs_log_<version>.txt`
   - Count lines, check redirects, env loading, errors, PlayerData save
   - Include findings table in the experiment entry
2. **Update `experiment_log.md`** with test result + log findings
3. **Mine findings for knowledge base** — review what was learned and update `.agent/llm-wiki-knowledge-base/` pages:
   - Add new root causes as new pages
   - Update existing pages with new fix patterns or tooling
   - Flag contradictions if new data supersedes old claims
   - Append to `log.md` with what was updated and why
4. **Capture knowledge** — if a root cause or breakthrough was found, create a dedicated memory file in `.ai_memory/beat-saber-ps4-custom-songs/`
5. **Update `project_summary.md`** status header
6. **Update `roadmap.md`** — mark checklist items, add new tasks
7. **Update `README.md`** — reflect current state, capabilities, findings
8. **Update `MEMORY.md`** if new documents or knowledge base pages were created
9. **Stage all changes in git** (`git add <file>` for specific files)
10. Then report

**See also:** [[research-index-update]] for keeping RESEARCH_INDEX.md in sync.


## Tool Persistence Rule
**Any installed tool, SDK, runtime, or prerequisite MUST be persisted in the devcontainer definition** so the toolset survives a container rebuild.

### Required approach:
1. **For tools installable via script**: Add installation commands to `/workspace/.devcontainer/setup_devcontainer.sh`. This runs on every container creation.
2. **For pre-compiled binaries**: Store the download and extraction in the setup script. Cache the zip/tarball at `/workspace/.tools/<tool-name>/` if size permits.
3. **For experimental scripts**: NEVER put utility scripts in `/tmp/`. All utility scripts must be:
   - Created at `/workspace/scripts/development/<script-name>`
   - Documented in `/workspace/scripts/development/index.md`
   - Staged and committed with the related experiment
4. **For large analysis output** (IL2CPP dumps >10MB): Store key findings in the knowledge base instead of committing raw output. Keep the raw output in a non-committed directory (e.g., `/workspace/il2cpp_output/`).

### Currently persisted tools:
| Tool | Location in Workspace | Installed By |
|------|----------------------|--------------|
| .NET SDK 6.0 | `/workspace/dotnet/` | `setup_devcontainer.sh` |
| Il2CppDumper v6.7.46 | `/workspace/Il2CppDumper/` | `setup_devcontainer.sh` |
| Il2CPP dump output | `/workspace/il2cpp_output/` (gitignored) | run `scripts/development/regen_il2cpp_dump.sh` |

### When a new tool is installed:
- Update this table
- Add installation to `setup_devcontainer.sh`
- Add `.gitignore` entries for any large binary outputs

## Git Etiquette
- The agent NEVER runs `git commit`. Stage only, present message for user review.
- The agent NEVER stages compiled artifacts (.prx, .bundle, .oelf, .fsb5, etc.).
- Binary files are added to `.gitignore` when first encountered.
