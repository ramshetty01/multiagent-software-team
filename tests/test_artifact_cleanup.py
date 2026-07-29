from __future__ import annotations

import os
import time

from mast.artifacts import ArtifactStore


def test_artifact_cleanup_supports_dry_run(tmp_path):
    run = tmp_path / "old-run"
    run.mkdir()
    old = time.time() - 10 * 86400
    os.utime(run, (old, old))
    store = ArtifactStore(tmp_path)
    assert store.cleanup_older_than(7) == [str(run)]
    assert run.exists()
    store.cleanup_older_than(7, dry_run=False)
    assert not run.exists()

