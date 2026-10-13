"""Synchronize versioned, bundled report runs onto persistent storage."""
from __future__ import annotations

import json
import os
import shutil
import uuid
from pathlib import Path


def _bundle_revision(manifest_path: str | os.PathLike[str]) -> int:
    try:
        manifest = json.loads(Path(manifest_path).read_text())
    except (OSError, ValueError, TypeError):
        return 0
    if not isinstance(manifest, dict):
        return 0
    revision = manifest.get("bundle_revision", 0)
    if isinstance(revision, bool):
        return 0
    if isinstance(revision, int):
        return max(0, revision)
    if isinstance(revision, str) and revision.isdecimal():
        return int(revision)
    return 0


def _overlay_bundled_run(source: str | os.PathLike[str], target: str | os.PathLike[str]) -> None:
    """Atomically replace bundled files, leaving extra per-run files intact.

    The manifest is copied last so an interrupted update is still recognized as
    stale and retried on the next startup.
    """
    source, target = Path(source), Path(target)
    target.mkdir(parents=True, exist_ok=True)
    files = [p for p in source.rglob("*") if p.is_file() and not p.is_symlink()]
    files.sort(key=lambda p: (p.name == "manifest.json", str(p.relative_to(source))))
    for original in files:
        destination = target / original.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name(f".{destination.name}.bundle-{uuid.uuid4().hex}.tmp")
        try:
            shutil.copy2(original, temporary)
            os.replace(temporary, destination)
        finally:
            if temporary.exists():
                temporary.unlink()


def sync_bundled_runs(
    bundled_dir: str | os.PathLike[str],
    storage_dir: str | os.PathLike[str],
    deleted_reports=(),
) -> list[str]:
    """Install missing bundled runs and newer explicitly-versioned updates.

    Generated reports live on a persistent volume in production. Keep their
    stable IDs, but allow an intentional bundled revision to refresh that same
    report instead of creating a duplicate dashboard entry. Increment the
    report's ``bundle_revision`` when publishing a new bundled version.
    """
    bundled_dir, storage_dir = os.fspath(bundled_dir), os.fspath(storage_dir)
    if os.path.realpath(bundled_dir) == os.path.realpath(storage_dir):
        return []
    if not os.path.isdir(bundled_dir):
        return []
    os.makedirs(storage_dir, exist_ok=True)
    deleted = set(deleted_reports)
    updated = []
    for rid in sorted(os.listdir(bundled_dir), reverse=True):
        if rid.startswith(".") or rid in deleted:
            continue
        source = os.path.join(bundled_dir, rid)
        source_manifest = os.path.join(source, "manifest.json")
        if not os.path.isfile(source_manifest) or os.path.islink(source):
            continue
        target = os.path.join(storage_dir, rid)
        if not os.path.exists(target):
            _overlay_bundled_run(source, target)
            updated.append(rid)
            continue
        if os.path.islink(target) or not os.path.isdir(target):
            continue
        source_revision = _bundle_revision(source_manifest)
        target_revision = _bundle_revision(os.path.join(target, "manifest.json"))
        if source_revision > target_revision:
            _overlay_bundled_run(source, target)
            updated.append(rid)
    return updated
