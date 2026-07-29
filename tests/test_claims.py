from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from mast.board import JsonlTaskBoard
from mast.messages import Message


def test_claim_subtask_is_atomic_under_parallel_workers(tmp_path):
    board = JsonlTaskBoard(tmp_path / "claims-board.jsonl")
    for index in range(10):
        board.append(Message(type="subtask", run_id="r1", role="architect", subtask_id=f"s{index}", payload={"title": str(index), "contract": {"files": [f"{index}.py"]}}))

    def claim(index: int):
        return board.claim_subtask("r1", f"worker-{index}")

    with ThreadPoolExecutor(max_workers=10) as pool:
        claims = [claim for claim in pool.map(claim, range(10)) if claim]

    assert len(claims) == 10
    assert len({claim.subtask_id for claim in claims}) == 10


def test_expired_lease_can_be_reclaimed(tmp_path):
    board = JsonlTaskBoard(tmp_path / "expired-claims-board.jsonl")
    board.append(Message(type="subtask", run_id="r1", role="architect", subtask_id="s1", payload={"title": "s1", "contract": {"files": ["a.py"]}}))
    assert board.claim_subtask("r1", "old-worker", lease_seconds=0)

    claim = board.claim_subtask("r1", "new-worker", lease_seconds=1)

    assert claim is not None
    assert claim.role == "new-worker"
