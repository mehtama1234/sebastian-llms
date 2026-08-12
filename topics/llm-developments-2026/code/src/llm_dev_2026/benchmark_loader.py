from __future__ import annotations

import json
from pathlib import Path

from .benchmark_schema import BenchmarkManifest, manifest_from_dict


def load_benchmark_manifest(path: str | Path) -> BenchmarkManifest:
    raw = json.loads(Path(path).read_text())
    return manifest_from_dict(raw)


def validate_manifest_paths(manifest: BenchmarkManifest) -> list[str]:
    """Return missing repo roots.

    The loader itself does not require the repos to exist locally, because a
    manifest may be moved between machines or evaluated in CI. This helper is
    the operational check used when a run needs concrete local snapshots.
    """
    missing: list[str] = []
    for repo in manifest.repos:
        if not repo.root_path().exists():
            missing.append(repo.root)
    return missing
