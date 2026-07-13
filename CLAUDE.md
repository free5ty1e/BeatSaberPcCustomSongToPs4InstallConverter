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

## 1. MANDATORY Documentation Before Reporting

**Rule file:** `/workspace/.ai_memory/project-summary-update-rule.md`

Before presenting results to the user, you MUST update ALL of these:

1. Download & analyze the PS4 log first
2. Update `experiment_log.md` with a new sequential experiment entry
3. Update `song_testing_log.md` if testing songs
4. Update `project_summary.md` with current status
5. Update knowledge base files if new findings affect durable knowledge
6. Stage everything in git

## 2. Follow the Experiment Workflow

**Rule file:** `/workspace/.ai_memory/experiment-workflow.md`

Every experiment cycle follows: Understand → Make Changes → Deploy →
Prepare for User Test → Analyze Results → Iterate

Read both rule files above before starting any work cycle.

## 3. ALWAYS Bump Version on Plugin Changes

Every change to `/workspace/beat_saber_deluxe/src/main.cpp` MUST increment
the `PLUGIN_VERSION` number. No exceptions. Format: `v0.<major>.<minor>`.

This rule also applies to any pipeline changes that affect deployment.

## 4. Keep All Docs Current

- `current-song-replacements-on-chris-ps4.md` — update when songs change
- `song_testing_log.md` — update after every PS4 test
- `experiment_log.md` — sequential entries for every cycle
- `project_summary.md` — keep the one-line status current

## 5. Mine conversation / results for durable, useful knowledge and capture / update in our llm-wiki knowledge base

The knowledge base is described in this document: `.agent/llm-wiki.md`
The knowledge base itself is located here: `.agent/llm-wiki-knowledge-base`
