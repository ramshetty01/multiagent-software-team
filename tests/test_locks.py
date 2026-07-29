from __future__ import annotations

from mast.locks import RunLock


def test_run_lock_blocks_duplicate_holder(tmp_path):
    with RunLock(tmp_path, "r1"):
        try:
            with RunLock(tmp_path, "r1"):
                pass
        except RuntimeError:
            pass
        else:
            raise AssertionError("expected duplicate lock failure")

