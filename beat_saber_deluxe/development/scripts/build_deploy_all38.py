"""Build + deploy all 38 custom-song bundles via the pipeline.

For each slot in the pipeline config's `mass_deploy.slots`, resolves the
songs_repo source directory (by matching song_metadata display name -> repo
_songName), then runs `full_custom_song_pipeline.py --song-dir <src> --target
<slot> --pcm16 --no-pad --deploy` to build + upload. Slots whose source cannot
be resolved are skipped with a warning so the run still completes the rest.

Usage:
    python3 development/scripts/build_deploy_all38.py [--dry-run]
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = "/workspace/beat-saber-ps4-custom-songs/songs_repo"
PIPE = os.path.join(ROOT, "tools", "full_custom_song_pipeline.py")
CFG = os.path.join(ROOT, "ps4_config.json")
META = os.path.join(ROOT, "song_metadata.json")


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def load_slots():
    src = open(os.path.join(ROOT, "tools", "full_custom_song_pipeline.py")).read()
    m = re.search(r'"slots":\s*\[(.*?)\]', src, re.S)
    return re.findall(r'"([^"]+)"', m.group(1))


def build_repo_index():
    idx = {}
    for h in os.listdir(REPO):
        info = os.path.join(REPO, h, "Info.dat")
        if os.path.isfile(info):
            try:
                n = json.load(open(info)).get("_songName", "").strip()
            except Exception:
                n = ""
            idx[h] = n
    return idx


def resolve(slots, idx):
    meta = json.load(open(META))["song_names"]
    key_by_slot = {}
    for s in slots:
        for k in meta:
            if norm(k) == norm(s):
                key_by_slot[s] = k
                break
    out = {}
    for s in slots:
        k = key_by_slot.get(s)
        disp = meta.get(k, "")
        key = disp.split("/")[0].strip().lower()
        cands = [h for h, n in idx.items() if n.strip().lower() == key]
        if len(cands) == 1:
            out[s] = cands[0]
    return out


def main():
    dry = "--dry-run" in sys.argv
    slots = load_slots()
    idx = build_repo_index()
    resolved = resolve(slots, idx)
    print(f"total slots={len(slots)} resolved={len(resolved)} "
          f"unresolved={len(slots) - len(resolved)}", flush=True)
    for s in slots:
        if s not in resolved:
            print(f"  SKIP (unresolved source) {s}", flush=True)
            continue
        h = resolved[s]
        cmd = [
            sys.executable, PIPE,
            "--song-dir", os.path.join(REPO, h),
            "--target", s,
            "--pcm16", "--no-pad",
            "--deploy",
        ]
        print(f"=== BUILD+DEPLOY {s} <- {h} ===", flush=True)
        if dry:
            print("  (dry-run) " + " ".join(cmd), flush=True)
            continue
        r = subprocess.run(cmd)
        print(f"  -> exit={r.returncode}", flush=True)


if __name__ == "__main__":
    main()
