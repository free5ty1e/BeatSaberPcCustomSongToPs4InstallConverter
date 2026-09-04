# 📋 PROJECT-SPECIFIC RULES — Beat Saber PS4 Custom Songs

You MUST follow these rules for every task in this project. These rules are
enforced by the files they reference — read them if you haven't already.

## 0. Rule Synchronization
- **Any changes to this file MUST be mirrored in `.opencode/rules.md`.**
- If an agent or user asks for a rule change, ensure both files are updated to maintain consistency.

## 1. MANDATORY Documentation Before Performing Work

**Rule file:** `/workspace/.ai_memory/project-summary-update-rule.md`

Before proceeding with work, upon receiving experiment results, you MUST update ALL of these with experiment results and findings:

1. Download the PS4 log directly to `.ai_memory/experiment_logs/` with a version-specific descriptive filename (e.g., `v0.8001_candidate_debug.txt`). Analyze the log, then ensure it's archived there — the download IS the archival copy. Never use `/tmp/` or other temporary locations.
2. Update `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` with experiment results — **the experiment log is PER-FEATURE; it holds only the current feature's experiments. See the "Per-Feature Experiment Log" rule below before appending.**
3. Update `.ai_memory/beat-saber-ps4-custom-songs/song_testing_log.md` if received new song testing results
4. Update `.agent/project_summary.md` with current status
5. Update llm-wiki style knowledge base files in `.agent/llm-wiki-knowledge-base/` if new findings affect durable knowledge
6. Update `.agent/roadmap.md` if appropriate
7. Update `.agent/context.yml` with any changes to versions, commands, architecture, or file paths so the quick-reference context file stays current

## 2. Rules For Performing Work

- If making changes to the Beat Saber Deluxe Plugin, you must bump the version in `main.cpp` and create an appropriate entry in `beat_saber_deluxe/CHANGELOG-PLUGIN.md`
- **Version scheme:** Both plugin and pipeline increment by **0.0001** per experiment (e.g. plugin v0.80 → v0.8001 → v0.8002; pipeline v0.53 → v0.5301 → v0.5302). This gives ample room to iterate before reaching v1.00 for either component.
- If making changes to the Beat Saber Deluxe Song Conversion Pipeline, you must bump the version in `beat_saber_deluxe/VERSION` and create an appropriate entry in `beat_saber_deluxe/CHANGELOG-PIPELINE.md`
- **Development scripts go in `beat_saber_deluxe/development/scripts/`.** Only after a script is proven to work correctly should it be integrated into the production pipeline (e.g., moved to `tools/`, `full_custom_song_pipeline.py`, or the plugin source). This keeps the codebase clean and prevents experimental code from being accidentally deployed or committed as production.
- If any new tools or prerequisites are needed, you have permission to install them; we are in a devcontainer so it is safe. If the tool is useful at all, please persist it along with its prerequisites in the devcontainer definition files so that our full toolset survives a devcontainer rebuild.
- If it makes sense to do so, attempt to deploy latest changes to the PS4 for experimentation
- **PS4 log handling:** Always download PS4 logs directly to `./workspace/.ai_memory/experiment_logs/` with a version-specific descriptive filename — never to `/tmp/` or other temporary locations. The log IS the archival copy; downloading to the workspace ensures it's preserved and organized alongside experiment documentation. **After downloading, ALWAYS clear the log on the PS4** (`lftp rm /data/GoldHEN/AFR/CUSA12878/bs_log.txt`) so the next pull only contains the new session's entries — otherwise the append-only log grows to thousands of stale lines across versions.
- **Feature flag enforcement:** All new experimental or optional functionality in the plugin MUST be gated behind a feature flag in `features.json`. When introducing a new feature, automatically propose a feature flag name (e.g., `enable_<feature_name>`) and gate the code behind `g_feature_<feature_name>` in `main.cpp`. Feature flags must default to `false` when absent. The pipeline's `DEFAULT_FEATURES` dict should include the new flag. This ensures every feature can be toggled on/off without recompiling.
- **Testing enforcement:** Before presenting any changes to the user, you MUST run the full test suite (`cd beat_saber_deluxe && python3 -m pytest tests/ -v`) and ensure all tests pass. Any new features, bug fixes, or behavior changes MUST include corresponding unit or integration tests. If existing tests break due to your changes, fix them before presenting. If the test suite cannot be run (e.g. missing dependencies), state this explicitly rather than skipping.

## 3. MANDATORY Documentation Updates Before Presenting

Before presenting a message to the user after performing work or research:

### 3.1 Documentation Checklist (MUST Complete All Items)

You MUST complete ALL of the following documentation updates BEFORE presenting results to the user. This is non-negotiable and must be done in order:

**A. Experiment Log Update**
- [ ] Append a new sequential experiment entry to `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`
- [ ] Include: Date, What was attempted, Key findings/results, Next steps/status
- [ ] Use the format from previous entries for consistency
- [ ] Experiment numbers are **globally sequential** across the whole project (unique IDs, even after archiving). Read the last experiment number from either the active log OR the newest archive file to find the next number.

### 3.0 Per-Feature Experiment Log (MANDATORY rotation rule)

`experiment_log.md` must stay small and focused. It is the **active log for the CURRENT feature ONLY**.

- **Structure:** `.ai_memory/beat-saber-ps4-custom-songs/`
  - `experiment_log.md` — active log (current feature, e.g. Beatmap Mode Mapping, Exp 160+)
  - `experiment_log_archive/` — archived per-feature logs
    - Naming: `experiment_log_<feature-slug>_exp<start>-<end>_<start-date>_to_<end-date>.md`
    - Example: `experiment_log_exp001-159_prior-features_2026-06-08_to_2026-07-31.md`
- **When to rotate:** when starting work on a NEW feature (roadmap milestone / feature change), BEFORE the first experiment of the new feature:
  1. Move the entire current `experiment_log.md` content into a new file in `experiment_log_archive/` using the naming above (feature-slug = the feature that just concluded).
  2. Rewrite `experiment_log.md` with a fresh header naming the new feature and pointing at the archive.
  3. Keep experiment numbers **globally sequential** (the next feature starts where the last one ended) so cross-references stay valid.
- **Archived logs are read-only references** — never edit them; append new experiments only to the active log.

**B. Project Summary Update**
- [ ] Update `.agent/project_summary.md` with current status
- [ ] Reflect any new blockers, breakthroughs, or changes in approach
- [ ] Keep the "Experiment Timeline" table current

**C. README.md Update (if applicable)**
- [ ] Update if new user-facing features were added
- [ ] Update if new limitations, requirements, or parameters were introduced
- [ ] Update status section to reflect current milestone

**D. Knowledge Base Update (if applicable)**
- [ ] Update `.agent/llm-wiki-knowledge-base/*.md` files if new durable knowledge was discovered
- [ ] Create new pages in the knowledge base for significant findings that should persist across sessions
- [ ] Cross-reference related knowledge base pages with `[[page-name]]` syntax

**E. Changelog Updates (if applicable)**
- [ ] Update `beat_saber_deluxe/CHANGELOG-PIPELINE.md` if pipeline/tools changed
- [ ] Update `beat_saber_deluxe/CHANGELOG-PLUGIN.md` if plugin changed
- [ ] Include version bump and date in new entry

**F. Song Replacements Mapping (if applicable)**
- [ ] Update `current-song-replacements-on-chris-ps4.md` when deployed custom songs change
- [ ] This is the mapping file that lets the user find custom songs in-game manually

**F2. Agent Context File (if applicable)**
- [ ] Update `.agent/context.yml` with any changes to versions, pipeline flags, commands, architecture, or file paths
- [ ] This is a compact quick-reference for giving project context to another agent with minimal tokens

**G. Git Staging (MANDATORY before presenting)**
- [ ] Stage ALL relevant changes with `git add` (fine-grained, not `-A`)
- [ ] Suggest a detailed commit message describing the staged changes
- [ ] Present the staged changes and suggested commit message to the user
- [ ] Do NOT commit without user approval (staging is for review, committing is user's choice)

### 3.2 Versioning Triggers (MANDATORY)

When ANY of the following changes occur, you MUST bump versions and update changelogs:

**Plugin Version Bump Required When:**
- Adding new features or capabilities to `beat_saber_deluxe.prx`
- Modifying plugin source code (`main.cpp`, `.h` files, etc.)
- Changing plugin behavior (hooks, redirections, etc.)
- Fixing bugs in the plugin

**Pipeline Version Bump Required When:**
- Adding new features to conversion pipeline scripts
- Modifying `full_custom_song_pipeline.py` or tools in `tools/`
- Changing song processing logic (audio, beatmaps, metadata)
- Fixing bugs in the pipeline

**Version Bump Format:**
- Plugin: `v0.XXXX` → increment by **0.0001** per experiment (e.g. v0.80 → v0.8001 → v0.8002)
- Pipeline: `v0.XXXX` → increment by **0.0001** per experiment (e.g. v0.53 → v0.5301 → v0.5302)
- Update both `CHANGELOG-PLUGIN.md` and `CHANGELOG-PIPELINE.md` with date and description

**Example:**
```markdown
## [v0.66] — 2026-07-17
### Added
- New feature or capability description

### Fixed
- Bug fix description

### Changed
- Behavior change description (with reason if non-obvious)
```

## 4. Follow the Experiment Workflow

**Rule file:** `/workspace/.ai_memory/experiment-workflow.md`

Every experiment cycle follows: Understand → Make Changes → Deploy →
Prepare for User Test → Analyze Results → Iterate

Read both rule files above before starting any work cycle.

## 5. Mine conversation / results for durable, useful knowledge and capture / update in our llm-wiki knowledge base

The knowledge base is described in this document: `.agent/llm-wiki.md`
The knowledge base itself is located here: `.agent/llm-wiki-knowledge-base`

### 5.1 Auto-Compaction Trigger (MANDATORY)

**When context usage approaches 90% of available context window, you MUST:**

1. **Pause current work immediately** — Do not continue with new experiments or complex tasks
2. **Mine the conversation for durable knowledge:**
   - Identify root causes, breakthroughs, and key technical findings
   - Extract reusable patterns, algorithms, and formulas
   - Capture "what worked" and "what didn't work" lessons learned
3. **Store in knowledge base:**
   - Write to `.agent/llm-wiki-knowledge-base/*.md` with proper frontmatter
   - Create new pages if the knowledge is substantial enough to warrant it
   - Cross-reference related pages with `[[page-name]]` syntax
4. **Update index:**
   - Add entry to `.agent/llm-wiki-knowledge-base/index.md` if new pages created
5. **Proceed with compaction** — Only after durable knowledge is captured should you compact the conversation

### 5.2 Knowledge Base Writing Standards

All knowledge base entries MUST include:
- `---` frontmatter with `name`, `description`, and `metadata.type`
- Clear, self-contained content that can be understood without session context
- Cross-references to related pages using `[[page-name]]` syntax
- Examples or code snippets where helpful

### 5.3 Prohibited Operations
- Prohibit all write operations with 'az' azure CLI (e.g., az resource create, az vm start, az group delete). Read operations are permitted.
- Prohibit all write operations with 'gh' (GitHub CLI) except for 'gh edit' when updating a PR description. All other mutations (create, delete, merge, etc.) are prohibited.

# ⚠️ DANGER MODE GUARDRAILS — Do Not Remove

You are running with **automatic permission approval**. Every tool call you
make is executed WITHOUT confirmation. This is a safety-critical mode.

## MANDATORY RESTRICTIONS — Git write operations

Only the following **Staging & Read** operations are allowed:

### ✅ ALLOWED Git Operations
| Command | Purpose |
|---------|---------|
| `git add <file>` | Stage a file (fine-grained) |
| `git add -p` | Stage interactively by hunk |
| `git add -A` | Stage all changes |
| `git status` | View working tree state |
| `git diff` | View unstaged changes |
| `git diff --cached` | View staged changes |
| `git log` | View commit history |
| `git show` | View a commit |
| `git blame` | Annotate a file |
| `git restore <file>` | Discard unstaged local changes |
| `git stash push` | Save WIP temporarily |
| `git stash list` | View stashes |
| `git stash show` | View stash contents |

### ❌ FORBIDDEN Git Operations
| Operation | Reason |
|-----------|--------|
| `git commit` | Would record changes permanently |
| `git push` / `git push --force` | Would publish to remote |
| `git branch` / `git checkout -b` | Would create branches |
| `git merge` / `git rebase` | Would alter history |
| `git tag` | Would tag releases |
| `git fetch` / `git pull` | Would contact remote |
| `git reset --hard` / `git reset --mixed` | Destructive history reset |
| `git revert` / `git cherry-pick` | Would create new commits |
| `git rm` / `git mv` | Would remove/rename tracked files |
| `git submodule` | Complex git mutation |
| `git worktree` | Would create worktrees |
| `git gc` / `git prune` / `git repack` | Repository maintenance |
| `git clean -fd` / `-fdX` | Aggressive file removal |
| `git stash drop` / `git stash pop` / `git stash clear` | Destructive stash ops |
| `git config` (with global/system) | Would change git settings |

### File System Cautions
- You can read, write, and edit files normally.
- **Do not delete files** without the user explicitly asking — even though
  you auto-accept permissions, ask for verbal confirmation on deletes.
- **Do not run shell commands** that modify the system (install packages,
  change system config) without asking first.

### Enforcement
- If you are asked to do a forbidden git operation, say:
  "⛔ This operation is blocked by Danger Mode guardrails."
- If in doubt, err on the side of refusing. The user can always switch to
  normal mode (`cz`) for git-write operations.










# --- DANGER GUARDRAILS START ---
# ⚠️ DANGER MODE GUARDRAILS — Do Not Remove

You are running with **automatic permission approval**. Every tool call you
make is executed WITHOUT confirmation. This is a safety-critical mode.

## MANDATORY RESTRICTIONS — Git write operations

Only the following **Staging & Read** operations are allowed:

### ✅ ALLOWED Git Operations
| Command | Purpose |
|---------|---------|
| `git add <file>` | Stage a file (fine-grained) |
| `git add -p` | Stage interactively by hunk |
| `git add -A` | Stage all changes |
| `git status` | View working tree state |
| `git diff` | View unstaged changes |
| `git diff --cached` | View staged changes |
| `git log` | View commit history |
| `git show` | View a commit |
| `git blame` | Annotate a file |
| `git restore <file>` | Discard unstaged local changes |
| `git stash push` | Save WIP temporarily |
| `git stash list` | View stashes |
| `git stash show` | View stash contents |

### ❌ FORBIDDEN Git Operations
| Operation | Reason |
|-----------|--------|
| `git commit` | Would record changes permanently |
| `git push` / `git push --force` | Would publish to remote |
| `git branch` / `git checkout -b` | Would create branches |
| `git merge` / `git rebase` | Would alter history |
| `git tag` | Would tag releases |
| `git fetch` / `git pull` | Would contact remote |
| `git reset --hard` / `git reset --mixed` | Destructive history reset |
| `git revert` / `git cherry-pick` | Would create new commits |
| `git rm` / `git mv` | Would remove/rename tracked files |
| `git submodule` | Complex git mutation |
| `git worktree` | Would create worktrees |
| `git gc` / `git prune` / `git repack` | Repository maintenance |
| `git clean -fd` / `-fdX` | Aggressive file removal |
| `git stash drop` / `git stash pop` / `git stash clear` | Destructive stash ops |
| `git config` (with global/system) | Would change git settings |

### File System Cautions
- You can read, write, and edit files normally.
- **Do not delete files** without the user explicitly asking — even though
  you auto-accept permissions, ask for verbal confirmation on deletes.
- **Do not run shell commands** that modify the system (install packages,
  change system config) without asking first.

### Enforcement
- If you are asked to do a forbidden git operation, say:
  "⛔ This operation is blocked by Danger Mode guardrails."
- If in doubt, err on the side of refusing. The user can always switch to
  normal mode (`cz`) for git-write operations.

## MANDATORY RESTRICTIONS — az (Azure CLI)

Read-only operations are permitted. All write/mutation operations are prohibited.

### ❌ FORBIDDEN az Operations
| Operation | Reason |
|-----------|--------|
| `az resource create` / `az resource delete` / `az resource update` | Would create or delete Azure resources |
| `az vm start` / `az vm stop` / `az vm delete` | Would modify VM state |
| `az group create` / `az group delete` | Would modify resource groups |
| `az network *` (write subcommands) | Would modify network configuration |
| (any other az write operation) | Mutations are prohibited |

## MANDATORY RESTRICTIONS — gh (GitHub CLI)

Only read operations and updating PR descriptions via `gh edit` are permitted.

### ✅ ALLOWED gh Operations
| Command | Purpose |
|---------|---------|
| `gh edit` (PR description only) | Update PR descriptions |
| `gh pr view` / `gh issue view` / `gh repo view` | Read repository data |
| (any read-only gh command) | Read operations are permitted |

### ❌ FORBIDDEN gh Operations
| Operation | Reason |
|-----------|--------|
| `gh pr create` / `gh pr merge` / `gh pr close` | Would create or modify pull requests |
| `gh issue create` / `gh issue close` / `gh issue comment` | Would modify issues |
| `gh release create` | Would create releases |
| `gh repo fork` / `gh repo create` / `gh repo delete` | Would create or delete repositories |
| (any other gh write/mutation operation) | Mutations are prohibited |

# --- DANGER GUARDRAILS END ---
