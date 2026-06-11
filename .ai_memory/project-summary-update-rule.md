---
name: project-summary-update-rule
description: "Enforcement: always update /workspace/.agent/project_summary.md after every task completion or before reporting to user"
metadata:
  type: feedback
---

## Rule: Update project_summary.md Before Reporting

**Enforcement:** After every task completion, deployment, experiment result, or significant discovery — and **before** reporting back to the user — update `/workspace/.agent/project_summary.md` first.

### What to update:
1. **Current Status header** (line 3) — update experiment statuses and add latest discovery
2. **Experiment Timeline** — add new experiments or update results, always keep the [CURRENT] tag on the active one
3. **Build System** — keep compiler flags, entry point, CRT info, output format in sync with the actual Makefile
4. **File Reference** — update descriptions when files change
5. **Key Technical Decisions** — add new numbered items for significant discoveries
6. **Recent Findings** — add new entries for new memory/experiment files
7. **RB4DX Comparison Table** — keep the "ours" column accurate
8. **Phase 5 Iterate** — update decision tree with latest experiment results

### Why:
Without this, the summary falls out of sync with reality. The user specifically reviews this document to understand current state, and stale info causes confusion and wasted iteration.

### How to apply:
When you feel the need to stop and report to the user, always first update `/workspace/.agent/project_summary.md`. Then report.

**See also:** [[research-index-update]] for keeping RESEARCH_INDEX.md in sync.
