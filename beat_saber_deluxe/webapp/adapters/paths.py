"""
paths.py — single source of location truth for the web app.

The web app is a THIN LAYER over the pipeline (plan §9.4 invariant 1): it must
spawn `tools/full_custom_song_pipeline.py` with CWD = the release/checkout root
(the pipeline derives PROJECT_ROOT from its own __file__, and its default config
paths are devcontainer-absolute — release finding #1). These helpers resolve
everything relative to THIS file so the webapp works from an extracted release
zip or a dev checkout unchanged.
"""

from __future__ import annotations

from pathlib import Path

# webapp/adapters/paths.py -> webapp -> beat_saber_deluxe -> release root
WEBAPP_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = WEBAPP_DIR.parent          # .../beat_saber_deluxe
RELEASE_ROOT = PROJECT_DIR.parent        # the release/checkout root

PIPELINE = PROJECT_DIR / "tools" / "full_custom_song_pipeline.py"
CONFIG_PATH = PROJECT_DIR / "ps4_config.json"
EXAMPLE_CONFIG_PATH = PROJECT_DIR / "ps4_config.example.json"
SONG_CATALOG = PROJECT_DIR / "beat_saber_song_ids.json"
FEATURES_LOCAL = PROJECT_DIR / "features.json"
VALIDATOR = RELEASE_ROOT / ".agent" / "docs" / "release-validation-test-procedure.sh"
DUMPER_CFG_REFERENCE = RELEASE_ROOT / "ps4_dump" / "dumper.cfg"
# Shipped inside the release zip at webapp/static/dumper.cfg (wizard download link)
DUMPER_CFG_BUNDLED = WEBAPP_DIR / "static" / "dumper.cfg"


def release_default_dump_dir() -> Path:
    """Where the README tells users to put their dump: <release>/ps4_dump."""
    return RELEASE_ROOT / "ps4_dump"


def is_release_layout(path: Path | None = None) -> bool:
    """True when running from an extracted release zip (no .git, no .agent)."""
    root = path or RELEASE_ROOT
    return not (root / ".git").exists()


def find_pipeline() -> Path:
    """Locate the pipeline script; raise with a useful message if absent."""
    if PIPELINE.exists():
        return PIPELINE
    raise FileNotFoundError(
        f"Pipeline not found at {PIPELINE}. The web app must run from a "
        "release/checkout containing beat_saber_deluxe/tools/."
    )
