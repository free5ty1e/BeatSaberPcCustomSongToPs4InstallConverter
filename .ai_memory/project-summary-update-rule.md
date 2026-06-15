---
name: project-summary-update-rule
description: "Enforcement: always update /workspace/.agent/project_summary.md after every task completion or before reporting to user"
metadata:
  type: feedback
---

## Rule: Update Documentation Before Reporting

**Enforcement:** After every task completion, deployment, experiment result, or significant discovery — and **before** reporting back to the user — update project documentation FIRST.

### Documents to update:

**1. `/workspace/.ai_memory/beat-saber-ps4-custom-songs/experiment_log.md`** (EVERY test cycle)
- Add a new entry for each test/experiment with:
  - Test number (sequential)
  - What changed
  - Result (✅ success / ❌ failed / ⏳ pending)
  - What was learned
- Update the "Working Configuration" section if the build process changes
- Update the "What We Know" section with confirmed findings

**2. `/workspace/.agent/project_summary.md`** (after each significant result)
- **Current Status header** — one-line summary of current state and what's being tested
- **Phase 5 Iterate** — update with latest findings and next steps
- **Workflow sections** — keep deployment commands and test procedure current
- **File Reference** — update if files/changes are made

**3. `/workspace/.ai_memory/MEMORY.md`** (when new documents are created)
- Add links to new memory files

### Why:
Without this, the documents fall out of sync with reality. The user specifically reviews these to understand current state, and stale info causes confusion and wasted iteration.

### How to apply:
Before reporting to the user:
1. Update `experiment_log.md` with the latest test result
2. Update `project_summary.md` status header and workflow
3. Update `MEMORY.md` if needed
4. Then report

**See also:** [[research-index-update]] for keeping RESEARCH_INDEX.md in sync.
