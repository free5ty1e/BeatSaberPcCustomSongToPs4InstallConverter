# ⚠️ DANGER MODE GUARDRAILS — Do Not Remove

You are running with **automatic permission approval**. Every tool call you
make is executed WITHOUT confirmation. This is a safety-critical mode.

## MANDATORY RESTRICTIONS — Git write operations

Only the following **Staging & Read** operations are allowed:

### ✅ ALLOWED Git Operations

| Command              | Purpose                        |
| -------------------- | ------------------------------ |
| `git add <file>`     | Stage a file (fine-grained)    |
| `git add -p`         | Stage interactively by hunk    |
| `git add -A`         | Stage all changes              |
| `git status`         | View working tree state        |
| `git diff`           | View unstaged changes          |
| `git diff --cached`  | View staged changes            |
| `git log`            | View commit history            |
| `git show`           | View a commit                  |
| `git blame`          | Annotate a file                |
| `git restore <file>` | Discard unstaged local changes |
| `git stash push`     | Save WIP temporarily           |
| `git stash list`     | View stashes                   |
| `git stash show`     | View stash contents            |

### ❌ FORBIDDEN Git Operations

| Operation                                              | Reason                            |
| ------------------------------------------------------ | --------------------------------- |
| `git commit`                                           | Would record changes permanently  |
| `git push` / `git push --force`                        | Would publish to remote           |
| `git branch` / `git checkout -b`                       | Would create branches             |
| `git merge` / `git rebase`                             | Would alter history               |
| `git tag`                                              | Would tag releases                |
| `git fetch` / `git pull`                               | Would contact remote              |
| `git reset --hard` / `git reset --mixed`               | Destructive history reset         |
| `git revert` / `git cherry-pick`                       | Would create new commits          |
| `git rm` / `git mv`                                    | Would remove/rename tracked files |
| `git submodule`                                        | Complex git mutation              |
| `git worktree`                                         | Would create worktrees            |
| `git gc` / `git prune` / `git repack`                  | Repository maintenance            |
| `git clean -fd` / `-fdX`                               | Aggressive file removal           |
| `git stash drop` / `git stash pop` / `git stash clear` | Destructive stash ops             |
| `git config` (with global/system)                      | Would change git settings         |

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

---

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
- If any new tools or prerequisites are needed, you have permission to install them; we are in a devcontainer so it is safe. If the tool is useful at all, please persist it along with its prerequisites in the devcontainer definition files so that our full toolset survives a devcontainer rebuild.
- If it makes sense to do so, attempt to deploy latest changes to the PS4 for experimentation

## 3. MANDATORY Documentation Updates Before Presenting

Before presenting a message to the user after performing work or research:

- Update `.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md` with a new sequential experiment entry describing what we are attempting
- Update `.agent/project_summary.md` with current status
- Update `README.md` to reflect any new user-facing features, limitations, requirements, parameters, or usage notes
- Update llm-wiki style knowledge base files in `.agent/llm-wiki-knowledge-base/` if new work or research affects durable knowledge
- Update `.agent/roadmap.md` if appropriate
- Update `beat_saber_deluxe/CHANGELOG-PIPELINE.md` and `beat_saber_deluxe/CHANGELOG-PLUGIN.md` as appropriate
- Update `current-song-replacements-on-chris-ps4.md` when deployed custom songs change. This is the mapping file that lets the user find custom songs in-game manually.
- Stage all relevant changes in git
- Suggest a detailed commit message that describe the staged changes as part of the report / message to the user, for the user to review and possibly use

## 4. Follow the Experiment Workflow

**Rule file:** `/workspace/.ai_memory/experiment-workflow.md`

Every experiment cycle follows: Understand → Make Changes → Deploy →
Prepare for User Test → Analyze Results → Iterate

Read both rule files above before starting any work cycle.

## 5. Mine conversation / results for durable, useful knowledge and capture / update in our llm-wiki knowledge base

The knowledge base is described in this document: `.agent/llm-wiki.md`
The knowledge base itself is located here: `.agent/llm-wiki-knowledge-base`

# --- DANGER GUARDRAILS START ---

- Prohibit all write operations with 'az' azure CLI (e.g., az resource create, az vm start, az group delete). Read operations are permitted.
- Prohibit all write operations with 'gh' (GitHub CLI) except for 'gh edit' when updating a PR description. All other mutations (create, delete, merge, etc.) are prohibited.

# --- DANGER GUARDRAHILS END ---
