# 📋 PROJECT-SPECIFIC RULES — Beat Saber PS4 Custom Songs

You MUST follow these rules for every task in this project. These rules are
enforced by the files they reference — read them if you haven't already.

## 1. MANDATORY Documentation Before Performing Work

**Rule file:** `/workspace/.ai_memory/project-summary-update-rule.md`

Before proceeding with work, upon receiving experiment results, you MUST update ALL of these with experiment results and findings:

1. Download & analyze the PS4 log first, then archive the log with an appropriate file name for historical purposes in `experiment_logs`
2. Update `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` with experiment results
3. Update `.ai_memory/beat-saber-ps4-custom-songs/song_testing_log.md` if received new song testing results
4. Update `.agent/project_summary.md` with current status
5. Update llm-wiki style knowledge base files in `.agent/llm-wiki-knowledge-base/` if new findings affect durable knowledge
6. Update `.agent/roadmap.md` if appropriate

## 2. Rules For Performing Work

- If making changes to the Beat Saber Deluxe Plugin, you must bump the version in `main.cpp` and create an appropriate entry in `beat_saber_deluxe/CHANGELOG-PLUGIN.md`
- If making changes to the Beat Saber Deluxe Song Conversion Pipeline, you must bump the version in `beat_saber_deluxe/VERSION` and create an appropriate entry in `beat_saber_deluxe/CHANGELOG-PIPELINE.md`
- **Development scripts go in `beat_saber_deluxe/development/scripts/`.** Only after a script is proven to work correctly should it be integrated into the production pipeline (e.g., moved to `tools/`, `full_custom_song_pipeline.py`, or the plugin source). This keeps the codebase clean and prevents experimental code from being accidentally deployed or committed as production.
- If any new tools or prerequisites are needed, you have permission to install them; we are in a devcontainer so it is safe. If the tool is useful at all, please persist it along with its prerequisites in the devcontainer definition files so that our full toolset survives a devcontainer rebuild.
- If it makes sense to do so, attempt to deploy latest changes to the PS4 for experimentation

## 3. MANDATORY Documentation Updates Before Presenting

Before presenting a message to the user after performing work or research:

### 3.1 Documentation Checklist (MUST Complete All Items)

You MUST complete ALL of the following documentation updates BEFORE presenting results to the user. This is non-negotiable and must be done in order:

**A. Experiment Log Update**
- [ ] Append a new sequential experiment entry to `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`
- [ ] Include: Date, What was attempted, Key findings/results, Next steps/status
- [ ] Use the format from previous entries for consistency

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

**G. Git Staging & Commit Suggestion**
- [ ] Stage all relevant changes with `git add` (fine-grained, not `-A`)
- [ ] Suggest a detailed commit message describing the staged changes
- [ ] Present this to the user for review before they decide to commit

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
- Plugin: `v0.XX` → increment last digit for patch, middle for minor, first for major
- Pipeline: `v1.XX` → same convention
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
