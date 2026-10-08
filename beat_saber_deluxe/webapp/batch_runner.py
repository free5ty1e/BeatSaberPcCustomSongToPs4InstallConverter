#!/usr/bin/env python3
"""
batch_runner.py — execute a batch of pipeline deploys serially.

Invoked by the web app's Batch tab (never by users directly):
    python3 webapp/batch_runner.py --jobs '<json argv list>'

Runs each deploy as a subprocess with the pipeline's own argv, streaming
every line; STOPS at the first failure (exit != 0) so a broken song never
gets silently skipped — the same semantics as the chained example scripts
(script1 && script2). One deploy at a time is the runner's rule; this driver
IS the single job.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

WEBAPP = Path(__file__).resolve().parent
PROJECT = WEBAPP.parent
RELEASE_ROOT = PROJECT.parent
PIPELINE = PROJECT / "tools" / "full_custom_song_pipeline.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--jobs", required=True,
                        help="JSON list of pipeline argv lists")
    args = parser.parse_args()

    try:
        batch = json.loads(args.jobs)
    except json.JSONDecodeError as e:
        print(f"batch_runner: invalid --jobs payload: {e}", file=sys.stderr)
        return 2

    if not isinstance(batch, list) or not batch:
        print("batch_runner: empty batch", file=sys.stderr)
        return 2

    print(f"=== Batch deploy: {len(batch)} songs ===")
    for i, argv in enumerate(batch, 1):
        label = " ".join(argv)
        print(f"\n--- [{i}/{len(batch)}] {' '.join(label.split())} ---", flush=True)
        result = subprocess.run(
            ["python3", str(PIPELINE), *argv],
            cwd=str(RELEASE_ROOT),
            text=True, bufsize=1)
        if result.returncode != 0:
            print(f"\n❌ Batch STOPPED: song [{i}/{len(batch)}] failed "
                  f"(exit {result.returncode}). Fix it and re-run the batch; "
                  f"songs before this one are deployed.", flush=True)
            return result.returncode
    print(f"\n✅ Batch complete: {len(batch)}/{len(batch)} songs deployed.",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
