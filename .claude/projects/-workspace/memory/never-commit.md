---
name: never-commit
description: "Permanent rule: Never run git commit — stage only, user commits"
metadata:
  type: feedback
---

The agent must NEVER run `git commit`. Ever. The agent may only stage changes with `git add` and present a suggested commit message for the user to review. The user commits manually.

**Why:** The user wants full control over what goes into each commit and when. They review every change before it enters the history. Automated commits bypass this review and can introduce unwanted artifacts (compiled binaries, debug files).

**How to apply:**
- Use `git add <paths>` to stage changed files
- Present the staged summary with `git diff --cached --stat`
- Provide a commit message for the user to review
- Never call `git commit`
- Add compiled artifacts to `.gitignore` (`.prx`, `.oelf`, `.bundle`, `.fsb5`, etc.)
