from __future__ import annotations

from pathlib import Path


def test_container_files_define_cli_entrypoint():
    root = Path(__file__).resolve().parents[1]
    assert 'ENTRYPOINT ["python3", "-m", "mast.cli"]' in (root / "Dockerfile").read_text()
    assert ".env" in (root / ".dockerignore").read_text()

