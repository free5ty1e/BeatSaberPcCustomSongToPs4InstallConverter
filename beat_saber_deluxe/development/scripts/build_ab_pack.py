#!/usr/bin/env python3
"""
build_ab_pack.py — M15's evaluation pack (the user's A/B design): fill the
lizzo pack with test-song variants — the SAME song twice, once with
engine-descended lower difficulties, once with Beat Sage's own — distinct
in-game titles/artists for the play-test.

The chain per song: Beat Sage run (the audio from /workspace/test_songs/) →
stage → prepare the two variants (theirs = the full map; ours = strip the
lowers + descend from E+) → deploy each with --song-name/--artist.

Run: python3 development/scripts/build_ab_pack.py [--dry-run]
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEBAPP = ROOT / "webapp"
TEST_SONGS = ROOT.parent / "test_songs"
sys.path.insert(0, str(WEBAPP))
sys.path.insert(0, str(WEBAPP.parent / "tools"))

BASE = "http://127.0.0.1:8765"


def api(path: str, method: str = "GET", timeout: int = 30, **kw):
    req = urllib.request.Request(f"{BASE}{path}", method=method, **kw)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def wait_job(timeout: int = 900) -> tuple[int, list]:
    """Poll the job to completion; return (exit_code, lines)."""
    after = 0
    deadline = time.time() + timeout
    while time.time() < deadline:
        j = api(f"/api/jobs/lines?after={after}", timeout=60)
        after = j.get("index", after)
        if not j.get("running"):
            job = j.get("job") or {}
            return job.get("exit_code"), j.get("lines", [])
        time.sleep(4)
    return -1, ["TIMEOUT"]


def beatsage_generate(wav: Path, title: str, difficulties: str) -> Path:
    """One Beat Sage run → the staged dir."""
    import uuid
    boundary = f"----BSD{uuid.uuid4().hex[:12]}"
    parts = []
    fields = {
        "title": title, "artist": "BSD Chiptune Synth",
        "difficulties": difficulties, "modes": "Standard",
        "events": "DotBlocks,Obstacles", "environment": "DefaultEnvironment",
        "system_tag": "v2",
    }
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                     f"name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    audio = wav.read_bytes()
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; "
                 f"name=\"audio\"; filename=\"{wav.name}\"\r\n"
                 f"Content-Type: audio/wav\r\n\r\n".encode())
    parts.append(audio)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)
    j = api("/api/jobs/beatsage", method="POST", timeout=120, data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    print(f"  Beat Sage job {j['job_id']} accepted…")
    code, lines = wait_job(timeout=600)
    for ln in lines:
        if "STAGED" in ln:
            print(f"  {ln.strip()}")
    if code != 0:
        raise SystemExit(f"Beat Sage generation failed (exit {code})")
    # find the newest staged dir matching the title
    manifest = json.loads((WEBAPP / "staged_songs" / "manifest.json").read_text())
    best = max((e for e in manifest.values()
                if e.get("name") == title or title in e.get("display_name", "")),
               key=lambda e: e.get("staged_at", 0))
    return Path(best["dir"])


def prepare_variants(staged_dir: Path, song_key: str, work_dir: Path) -> tuple[Path, Path]:
    """(theirs, ours): theirs = the full Beat Sage map; ours = the lowers
    stripped + descended from E+ by the engine."""
    theirs = work_dir / f"{song_key}_beatsage"
    ours = work_dir / f"{song_key}_descent"
    for d in (theirs, ours):
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(staged_dir, d)
    # ours: strip the lower difficulties + the mode variants, then descend
    for f in os.listdir(ours):
        if f.startswith(("Easy", "Normal", "Hard", "Expert.")) and f.endswith(".dat"):
            os.remove(ours / f)
    import full_custom_song_pipeline as fp  # noqa: PLC0415
    filled = fp.fill_missing_standard_difficulties(str(ours), bpm=120.0)
    print(f"  descended: {filled}")
    return theirs, ours


def deploy(song_dir: Path, target: str, title: str, artist: str) -> None:
    body = json.dumps({"map_id": "", "song_dir": str(song_dir), "target": target,
                       "song_name": title, "artist": artist}).encode()
    j = api("/api/jobs/deploy", method="POST", timeout=60, data=body,
            headers={"Content-Type": "application/json"})
    print(f"  deploying → {target} (“{title}” by {artist}) — job {j['job_id']}")
    code, lines = wait_job(timeout=900)
    for ln in lines:
        if "PASSED" in ln or "FAILED" in ln or "DESCENDED" in ln:
            print(f"  {ln.strip()}")
    if code != 0:
        raise SystemExit(f"deploy to {target} failed (exit {code})")


# the A/B plan: (song_key, wav, target_theirs, target_ours, base_title)
PLAN = [
    ("nes_scale_runner", "bsd_nes_scale_runner.wav", "TruthHurts", None,
     "NES Scale Runner"),   # ours = Juice (already deployed — renamed below)
    ("nes_groove", "bsd_nes_groove.wav", "EverybodysGay", "AboutDamnTime",
     "NES Groove"),
    ("one_and_half_dragons", "bsd_one_and_half_dragons.wav", "Tempo", "GoodAsHell",
     "One And a Half Dragons"),
    ("nes_beattour", "bsd_nes_beattour_2026.wav", None, "CuzILoveYou",
     "NES BeatTour 2026"),
    ("nes_scale_expedition", "bsd_nes_scale_expedition.wav", None, "2BeLoved",
     "NES Scale Expedition"),
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    work = ROOT / "ab_pack_work"
    work.mkdir(exist_ok=True)
    artist_ours = "Descent Engine"
    artist_theirs = "Beat Sage AI"

    # 0. rename Juice's metadata (the already-deployed descent variant)
    if not dry:
        argv = ["--metadata-only", "--song-name", "NES Scale Runner [Descent]",
                "--artist", artist_ours, "--target", "Juice", "--deploy"]
        subprocess.run(["python3", str(ROOT / "beat_saber_deluxe" / "tools" /
                                        "full_custom_song_pipeline.py"), *argv],
                       cwd=str(ROOT), timeout=300)  # ROOT = the pipeline's project dir
        print("✓ Juice renamed to 'NES Scale Runner [Descent]'")

    for song_key, wav_name, target_theirs, target_ours, base_title in PLAN:
        wav = TEST_SONGS / wav_name
        if not wav.exists():
            print(f"⚠️ {wav} missing — skipping {song_key}")
            continue
        print(f"\n=== {base_title} ===")

        # a single Beat Sage run with THEIR difficulty set (no Easy — their
        # v2 offers Normal..ExpertPlus; the descent fills Easy in our variant)
        if target_theirs and not dry:
            staged = beatsage_generate(wav, f"{base_title}", "Normal,Hard,Expert,ExpertPlus")
            theirs, ours = prepare_variants(staged, song_key, work)
            deploy(theirs, target_theirs, f"{base_title} [Beat Sage]", artist_theirs)
            if target_ours:
                deploy(ours, target_ours, f"{base_title} [Descent]", artist_ours)
        elif target_ours and not dry:
            # E+ only → the descent fills all three lowers
            staged = beatsage_generate(wav, f"{base_title}", "ExpertPlus")
            theirs, ours = prepare_variants(staged, song_key, work)
            deploy(ours, target_ours, f"{base_title} [Descent]", artist_ours)
        elif dry:
            print(f"  would generate {wav_name} → {target_theirs}/{target_ours}")
    print("\n✅ The evaluation pack is built — boot Beat Saber and A/B the lizzo pack!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
