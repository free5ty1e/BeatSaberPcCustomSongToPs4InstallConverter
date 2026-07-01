---
name: project-summary-update-rule
description: "Enforcement: always update /workspace/.agent/project_summary.md after every task completion or before reporting to user"
metadata:
  type: feedback
---

## Rule: Update Documentation Before Reporting

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

**4. `/workspace/README.md`** (after each significant result)

- **Status header** — update the one-line project status description
- **Current capabilities** — update what's working vs what's still in progress
- **Key findings** — document root causes discovered (e.g., m_Script is just gzip)
- Keep the setup/build/test instructions current

**5. Knowledge capture** (every time a root cause or breakthrough is discovered)

- **Check for existing memory**: before creating a new memory file, check if one already covers the topic
- **Save findings as persistent memory**: write a `.md` file in `/workspace/.ai_memory/beat-saber-ps4-custom-songs/` with:
  - The root cause (what was wrong and why)
  - The fix (what change resolved it)
  - Why other approaches didn't work (prevent repeating dead ends)
  - Link related experiments with `[[experiment-id]]`
  - Example: `m_script-gzip-only.md` — "m_Script is just gzip data, no decompressed_size prefix"
- **Update MEMORY.md** with a pointer to the new knowledge file
- **Stage in git** along with experiment log and other docs

**6. `/workspace/.ai_memory/MEMORY.md`** (when new documents are created)

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
3. **Capture knowledge** — if a root cause or breakthrough was found, create a dedicated knowledge file
4. **Update `project_summary.md`** status header
5. **Update `roadmap.md`** — mark checklist items, add new tasks
6. **Update `README.md`** — reflect current state, capabilities, findings
7. **Update `MEMORY.md`** if new documents were created
8. **Stage all changes in git** (`git add <file>` for specific files)
9. Then report

**See also:** [[research-index-update]] for keeping RESEARCH_INDEX.md in sync.
