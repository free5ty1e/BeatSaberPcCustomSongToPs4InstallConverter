---
name: ps4-deploys-pipeline-only
description: Beat Saber PS4 project — all deploys/tests must run through the pipeline; fixes go in pipeline code; no manual file manipulation
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b0f9dafb-7c52-4826-b3ce-94c3539962c4
  modified: 2026-08-25T20:03:40.253Z
---

In the Beat Saber PS4 custom songs project (2026-08-25, Exp 198/199 era), the user explicitly directed: "please do not rely on any further manual manipulation of files. Everything we try must be through the pipeline... Any fixes need to be in the pipeline. All this manual manipulation and ephemeral testing takes us in circles."

**Why:** Ad-hoc deploys (hand-written lftp scripts, hand-crafted redirects/catalog variants like `redirects_test_*.json`) accumulated undocumented console states that contradicted local docs and made crash attribution impossible — several experiment cycles were spent rediscovering what was actually deployed.

**How to apply:**
- Deploy only via `tools/full_custom_song_pipeline.py` flags (`--deploy-pack-modes --deploy-config --verify-ps4`, pack subset via a committed `--config development/ps4_config_*.json`).
- Fix root causes in `tools/` code with regression tests, then redeploy via pipeline — never patch artifacts or remote files by hand.
- Before any boot test, reconcile: what is ACTUALLY on the PS4 (pull + md5) vs what docs claim. The console state is ground truth.
- Clearing `bs_log.txt` before a test is fine (log hygiene, not asset manipulation).
