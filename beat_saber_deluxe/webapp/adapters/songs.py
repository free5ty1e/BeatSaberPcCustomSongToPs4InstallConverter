"""
songs.py — local song-folder validation, map-zip intake, and staging (M13).

The Pick-a-Song tab's sections 2 (Beat Sage) and 3 (local folder) both end
at the same place: a VALIDATED local song directory that flows into the
existing Deploy tab unchanged (`--song-dir <dir> --target <slot>`).

The validation rules MIRROR THE PIPELINE'S OWN (thin-layer doctrine — this
adapter reads, the pipeline converts; the contract is:
  - `Info.dat` (or lowercase `info.dat`) must exist and parse as JSON
    (V2/V3: `_songName`/`_songAuthorName`/`_beatsPerMinute`; V4: nested
    `song`/`audio` objects — the pipeline's Exp 228 format-aware reads)
  - at least one audio file (.wav/.ogg/.flac/.mp3/.aiff/.egg — the
    pipeline's Step 0 search list) must be present
  - at least one beatmap file (.dat) must be discoverable
Everything else (missing Easy, missing Expert/ExpertPlus, V2 vs V3 schema)
is a WARNING the Deploy flow already handles (Expert/E+ get auto-filled;
V2 converts with --convert-to-v3, the default).

Staging (plan §4): staged songs persist on disk across web-app restarts —
  webapp/staged_songs/manifest.json   one entry per staged song
  webapp/staged_songs/<id>/           extracted zips live here
Path-staged songs (a user folder that stays where it is) record the path;
zip-staged songs (uploaded zips, Beat Sage downloads) are extracted into the
staging dir the web app owns. Deploy ALWAYS re-checks existence — a moved
or deleted folder produces a clear error, never a mystery.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from . import paths

STAGING_DIR = paths.WEBAPP_DIR / "staged_songs"
MANIFEST_PATH = STAGING_DIR / "manifest.json"

# The pipeline's Step 0 audio search list (full_custom_song_pipeline.py) —
# keep in sync with it (an audio format accepted here must convert there).
AUDIO_EXTENSIONS = (".wav", ".ogg", ".flac", ".mp3", ".aiff", ".egg")
DIFFICULTY_ORDER = ["Easy", "Normal", "Hard", "Expert", "ExpertPlus"]


@dataclass
class SongValidation:
    """Result of validating one candidate song directory."""

    ok: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    dir: str = ""
    name: str = ""
    artist: str = ""
    bpm: float | None = None
    schema: str = ""          # "V2" | "V3" | "V4" | ""
    difficulties: list[str] = field(default_factory=list)  # Standard, ordered
    modes: list[str] = field(default_factory=list)
    beatmap_count: int = 0
    audio_files: list[str] = field(default_factory=list)

    def summary_line(self) -> str:
        diffs = "/".join(self.difficulties) if self.difficulties else "?"
        return f"{self.name or 'Unknown song'} by {self.artist or '?'} — {self.schema or '?'} · {diffs} · BPM {self.bpm or '?'}"


def _sort_diffs(diffs: list[str]) -> list[str]:
    order = {d: i for i, d in enumerate(DIFFICULTY_ORDER)}
    return sorted(set(diffs), key=lambda d: order.get(d, 99))


def _read_info(path: Path) -> tuple[dict | None, str]:
    """Read Info.dat/info.dat → (parsed dict or None, error message)."""
    for fname in ("Info.dat", "info.dat"):
        candidate = path / fname
        if candidate.is_file():
            try:
                with open(candidate, encoding="utf-8") as f:
                    return json.load(f), ""
            except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
                return None, f"{fname} is not valid JSON ({e}). To fix: the map may be corrupt or half-downloaded — re-download or re-extract it."
    return None, ""


def _info_schema(info: dict) -> str:
    version = str(info.get("_version", "") or "")
    if version.startswith("4"):
        return "V4"
    if version.startswith("3"):
        return "V3"
    if version.startswith("2"):
        return "V2"
    # V4 without _version but with the nested song/audio shape
    if "song" in info and "audio" in info:
        return "V4"
    return ""


def _info_difficulties(info: dict) -> list[str]:
    """Standard-characteristic difficulties declared in Info.dat.

    V2/V3: _difficultyBeatmapSets[] with _beatmapCharacteristicName
    "Standard" and _difficultyRank names; V4: top-level difficultyBeatmaps[]
    with characteristic "Standard" + difficulty fields.
    """
    out: list[str] = []
    if isinstance(info.get("_difficultyBeatmapSets"), list):
        for beatmap_set in info["_difficultyBeatmapSets"]:
            if not isinstance(beatmap_set, dict):
                continue
            if str(beatmap_set.get("_beatmapCharacteristicName", "")).lower() != "standard":
                continue
            for bm in beatmap_set.get("_difficultyBeatmaps", []) or []:
                if isinstance(bm, dict):
                    diff = bm.get("_difficulty")
                    if isinstance(diff, str):
                        out.append(diff)
    if isinstance(info.get("difficultyBeatmaps"), list):  # V4 shape
        for bm in info["difficultyBeatmaps"]:
            if isinstance(bm, dict) and str(bm.get("characteristic", "")).lower() == "standard":
                diff = bm.get("difficulty")
                if isinstance(diff, str):
                    out.append(diff)
    return _sort_diffs(out)


def validate_dir(path_str: str) -> SongValidation:
    """Validate a candidate song folder against the pipeline's contract.
    Every error carries a suggested course of action (project rule)."""
    result = SongValidation()
    raw = (path_str or "").strip()
    if not raw:
        result.errors.append("No folder path given. To fix: type or paste the folder that contains Info.dat.")
        return result
    path = Path(raw).expanduser()
    if not path.is_dir():
        result.errors.append(
            f"Folder not found: {raw}. To fix: check the path — it should be the folder that directly contains Info.dat (not its parent).")
        return result
    result.dir = str(path.resolve())

    info, parse_error = _read_info(path)
    if info is None:
        if parse_error:
            result.errors.append(parse_error)
        else:
            result.errors.append(
                f"No Info.dat found in {raw}. To fix: pick the folder that contains Info.dat directly "
                "(a BeatSaver/Beat Sage map zip extracts to one folder with Info.dat inside — select that folder).")
        return result
    if not isinstance(info, dict):
        result.errors.append("Info.dat parsed but is not a JSON object. To fix: re-download the map — the file is corrupt.")
        return result

    result.schema = _info_schema(info)
    # Format-aware reads — the pipeline's Exp 228 rules
    name = info.get("_songName")
    artist = info.get("_songAuthorName")
    if not name or not artist:
        v4_song = info.get("song") or {}
        name = name or v4_song.get("title") or v4_song.get("songName")
        artist = artist or v4_song.get("author") or v4_song.get("songAuthorName")
    result.name = str(name) if name else ""
    result.artist = str(artist) if artist else ""
    bpm = info.get("_beatsPerMinute")
    if bpm is None:
        bpm = (info.get("audio") or {}).get("bpm")
    try:
        result.bpm = float(bpm) if bpm is not None else None
    except (TypeError, ValueError):
        result.bpm = None

    # Audio: the pipeline's Step 0 list
    result.audio_files = sorted(
        f.name for f in path.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS)
    if not result.audio_files:
        result.errors.append(
            "No audio file found (expected .wav/.ogg/.flac/.mp3/.aiff/.egg). To fix: re-download the map — "
            "its audio is missing (Beat Sage and BeatSaver zips always include one).")
        return result

    # Beatmaps: mirror the pipeline's detect_song_modes (filename-based —
    # it handles V2/V3 .dat names and V4 '.beatmap.dat' variants alike)
    result.difficulties, result.modes, result.beatmap_count = _detect_beatmaps(path)
    if result.beatmap_count == 0:
        result.errors.append(
            "No beatmap .dat files found. To fix: re-download the map — the difficulty files are missing "
            "(or extract the FULL zip, not just Info.dat).")
        return result

    # Declared-in-Info.dat difficulties fill gaps the filenames missed
    declared = _info_difficulties(info)
    if declared and not result.difficulties:
        result.difficulties = declared

    # Warnings (the Deploy flow handles all of these — informational)
    if "Easy" not in result.difficulties:
        result.warnings.append(
            "No Easy difficulty (Beat Sage can't generate one; the song will just not offer Easy).")
    missing_hi = [d for d in ("Expert", "ExpertPlus") if d not in result.difficulties]
    if missing_hi:
        result.warnings.append(
            f"Missing {', '.join(missing_hi)} — the pipeline auto-fills Expert/Expert+ during the deploy (the safe default).")
    if not result.schema:
        result.warnings.append(
            "Info.dat carries no schema version — the pipeline will treat it as V2/V3 and convert as needed.")
    if result.bpm is None:
        result.warnings.append("No BPM in Info.dat — the pipeline falls back to a beatmap-derived estimate.")
    result.ok = True
    return result


def _detect_beatmaps(path: Path) -> tuple[list[str], list[str], int]:
    """Filename-based mode/difficulty detection — mirrors the pipeline's
    detect_song_modes() classification rules for files on disk."""
    diffs: set[str] = set()
    modes: set[str] = set()
    count = 0
    known_modes = {"Standard", "NoArrows", "OneSaber", "90Degree", "360Degree",
                  "Legacy", "Lightshow", "Lawless"}
    aliases = {"OneSaber": "OneSaber", "90degree": "90Degree"}
    for f in sorted(path.iterdir()):
        if not f.is_file() or f.suffix.lower() not in (".dat", ".json"):
            continue
        lower = f.name.lower()
        if lower in ("info.dat", "info.json", "bpminfo.dat", "bpminfo.json"):
            continue
        if "lightshow" in lower or "audiodata" in lower:
            continue
        stem = f.stem
        # V4 '.beatmap.dat' variant: ExpertPlus.beatmap.dat → ExpertPlus
        if stem.lower().endswith(".beatmap"):
            stem = stem[:-len(".beatmap")]
        count += 1
        # prefix style: OneSaberExpert → (OneSaber, Expert)
        matched = False
        for mode in sorted(known_modes, key=len, reverse=True):
            if stem.lower().startswith(mode.lower()) and len(stem) > len(mode):
                rest = stem[len(mode):]
                if rest in DIFFICULTY_ORDER:
                    canonical = aliases.get(mode.lower(), mode)
                    modes.add(canonical)
                    diffs.add(rest)
                    matched = True
                    break
        if matched:
            continue
        # suffix style: ExpertPlusOneSaber → (OneSaber, ExpertPlus)
        for mode in sorted(known_modes - {"Standard"}, key=len, reverse=True):
            if stem.lower().endswith(mode.lower()) and len(stem) > len(mode):
                head = stem[:-len(mode)]
                if head in DIFFICULTY_ORDER:
                    canonical = aliases.get(mode.lower(), mode)
                    modes.add(canonical)
                    diffs.add(head)
                    matched = True
                    break
        if matched:
            continue
        # bare difficulty: Standard
        if stem in DIFFICULTY_ORDER:
            modes.add("Standard")
            diffs.add(stem)
    return _sort_diffs(list(diffs)), sorted(modes), count


# ---------------------------------------------------------------- staging

def _load_manifest() -> dict:
    try:
        with open(MANIFEST_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_manifest(manifest: dict) -> None:
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")


def _slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")
    return (slug[:40] or "song").lower()


def _entry_from_validation(v: SongValidation, kind: str, source: str,
                           staged_dir: str) -> dict:
    return {
        "id": "",  # caller assigns
        "kind": kind,          # "path" (user's folder) | "zip" (we extracted it)
        "source": source,      # "local-folder" | "zip" | "beatsage"
        "dir": staged_dir,
        "name": v.name or Path(staged_dir).name,
        "artist": v.artist,
        "bpm": v.bpm,
        "schema": v.schema,
        "difficulties": v.difficulties,
        "modes": v.modes,
        "beatmap_count": v.beatmap_count,
        "audio_files": v.audio_files,
        "warnings": v.warnings,
        "staged_at": time.time(),
    }


def stage_dir(path_str: str, source: str = "local-folder") -> dict:
    """Validate a user folder and record it (path-staging — files stay put).
    Returns the manifest entry. Raises ValueError with a To-fix message on
    validation failure (the caller maps it to a 400 with the error list)."""
    v = validate_dir(path_str)
    if not v.ok:
        raise ValueError("\n".join(v.errors))
    manifest = _load_manifest()
    # Stable ID per resolved path: re-validating the same folder refreshes
    # the entry instead of duplicating it
    sid = hashlib.sha1(v.dir.encode()).hexdigest()[:12]
    entry = _entry_from_validation(v, kind="path", source=source, staged_dir=v.dir)
    entry["id"] = sid
    manifest[sid] = entry
    _save_manifest(manifest)
    return entry


def extract_zip_bytes(data: bytes, dest_root: Path) -> Path:
    """Extract a map zip safely → the song dir (Info.dat's folder).

    Zip-slip guarded: no absolute paths, no '..' traversal, no drive letters.
    BeatSaver/Beat Sage zips hold the files at the root; some tools wrap
    them in one folder — descend into a lone directory until Info.dat is
    found (max 3 levels)."""
    if not data[:2] == b"PK":
        raise ValueError("Not a zip file (missing the PK header). To fix: drop the map zip itself — some browsers save the 'download' HTML page by mistake.")
    dest_root.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(__import__("io").BytesIO(data)) as zf:
            for info in zf.infolist():
                name = info.filename
                if info.is_dir():
                    continue
                # Reject traversal/absolute/backslash tricks
                if name.startswith(("/", "\\")) or ":" in name.split("/")[0] or ".." in Path(name).parts:
                    raise ValueError(
                        f"Refusing to extract unsafe zip entry: {name!r}. To fix: re-download the map from its original source — this zip is malformed.")
                target = dest_root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as out:
                    out.write(src.read())
    except zipfile.BadZipFile as e:
        raise ValueError(f"The zip is corrupt ({e}). To fix: re-download it — interrupted downloads zip badly.") from e
    # Descend to the Info.dat folder
    cur = dest_root
    for _ in range(3):
        if _read_info(cur)[0] is not None or any(
                f.name.lower() == "info.dat" for f in cur.iterdir() if f.is_file()):
            return cur
        children = [d for d in cur.iterdir() if d.is_dir()]
        files = [f for f in cur.iterdir() if f.is_file()]
        if len(children) == 1 and not files:
            cur = children[0]
        else:
            break
    return cur


def stage_zip_bytes(data: bytes, source: str = "zip",
                    display_name: str = "") -> dict:
    """Extract an uploaded map zip into staging + validate + record.
    Raises ValueError (with To-fix messages) on any failure."""
    sid = f"{int(time.time())}_{hashlib.sha1(data).hexdigest()[:8]}"
    dest_root = STAGING_DIR / sid
    try:
        song_dir = extract_zip_bytes(data, dest_root)
    except ValueError:
        # cleanup the partial extraction so staging stays tidy
        import shutil
        shutil.rmtree(dest_root, ignore_errors=True)
        raise
    v = validate_dir(str(song_dir))
    if not v.ok:
        import shutil
        shutil.rmtree(dest_root, ignore_errors=True)
        raise ValueError("\n".join(v.errors))
    manifest = _load_manifest()
    entry = _entry_from_validation(v, kind="zip", source=source, staged_dir=str(song_dir))
    entry["id"] = sid
    entry["display_name"] = display_name or entry["name"]
    manifest[sid] = entry
    _save_manifest(manifest)
    return entry


def list_staged() -> list[dict]:
    """Recent staged songs, newest first; prunes entries whose folder vanished."""
    manifest = _load_manifest()
    live: dict = {}
    changed = False
    for sid, entry in manifest.items():
        if Path(entry.get("dir", "")).is_dir():
            live[sid] = entry
        else:
            changed = True
    if changed:
        _save_manifest(live)
    return sorted(live.values(), key=lambda e: e.get("staged_at", 0), reverse=True)


def remove_staged(sid: str) -> bool:
    """Remove a staged song. Zip-extracted folders are deleted from disk;
    path-staged folders stay (they were never ours)."""
    manifest = _load_manifest()
    entry = manifest.pop(sid, None)
    if entry is None:
        return False
    if entry.get("kind") == "zip":
        import shutil
        root = Path(entry.get("dir", ""))
        # the extraction dir (up to staged_songs/<sid>) — dir may be nested
        try:
            top = root
            while top.parent != STAGING_DIR and top != STAGING_DIR:
                top = top.parent
            if top.parent == STAGING_DIR:
                shutil.rmtree(top, ignore_errors=True)
        except OSError:
            pass
    _save_manifest(manifest)
    return True
