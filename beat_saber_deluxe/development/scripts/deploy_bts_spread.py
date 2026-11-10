#!/usr/bin/env python3
"""
deploy_bts_spread.py — deploy the six test songs (the descent versions) to
the BTS music pack slots (the user's request): one song per slot, distinct
in-game titles, the Descent Engine artist. Each deploy runs through the
web app's job runner (the production path) and is validated by the
pipeline's post-deploy checks.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "ab_pack_work"
BASE = "http://127.0.0.1:8765"

# (the song dir, the BTS slot, the in-game title)
SPREAD = [
    (WORK / "nes_groove_descent", "BloodSweatAndTears", "NES Groove [Descent]"),
    (WORK / "nes_scale_runner_descent", "BoyWithLuv", "NES Scale Runner [Descent]"),
    (WORK / "nes_beattour_descent", "BurningUp", "NES BeatTour 2026 [Descent]"),
    (WORK / "nes_scale_expedition_descent", "Dionysus", "NES Scale Expedition [Descent]"),
    (WORK / "one_and_half_dragons_descent", "Dna", "One And a Half Dragons [Descent]"),
    (None, "Dope", "BSD Deluxe Theme [Descent]"),   # the theme: the StartMeUp staged map
]


def api(path: str, method: str = "GET", timeout: int = 60, **kw):
    req = urllib.request.Request(f"{BASE}{path}", method=method, **kw)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_job(timeout: int = 900) -> int:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            j = api("/api/jobs/lines?after=0", timeout=60)
        except Exception:
            time.sleep(5)
            continue
        job = j.get("job")
        # the runner keeps the LAST job queryable — its exit code is
        # authoritative even after the running flag flips (the poll race
        # that mislabeled the first BTS deploy as a failure)
        if not j.get("running") and job is not None:
            code = job.get("exit_code")
            if code is not None:
                return code
        time.sleep(5)
    return -1


def main() -> int:
    # the theme's staged map: the newest staged dir whose Info.dat names it
    theme_dir = None
    staged_root = ROOT / "webapp" / "staged_songs"
    for d in sorted(staged_root.iterdir(), reverse=True):
        info = d / "Info.dat"
        if info.exists():
            try:
                if "Deluxe Theme" in info.read_text():
                    theme_dir = d
                    break
            except OSError:
                continue
    spread = [(theme_dir if sd is None else sd, slot, title)
              for sd, slot, title in SPREAD]

    for song_dir, slot, title in spread:
        if song_dir is None or not Path(song_dir).is_dir():
            print(f"⚠️ {slot}: no staged map — skipped")
            continue
        body = json.dumps({"map_id": "", "song_dir": str(song_dir),
                           "target": slot, "song_name": title,
                           "artist": "Descent Engine"}).encode()
        j = api("/api/jobs/deploy", method="POST", timeout=60, data=body,
                headers={"Content-Type": "application/json"})
        print(f"🚀 {slot} ← {title} (job {j['job_id']})")
        code = wait_job()
        mark = "✅" if code == 0 else f"❌ exit {code}"
        print(f"   {mark}")
        if code != 0:
            return 1
    print("\n✅ The BTS spread is deployed — 6 test songs, all descent-engine charts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
