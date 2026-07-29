from __future__ import annotations

from .messages import Message
from .models import ModelProvider, ModelRequest, complete_with_retry
from .prompts import architect_prompt, parse_architect_json
from .schema import InterfaceContract, Subtask, validate_dag


def plan_from_issue(run_id: str, title: str, body: str, provider: ModelProvider | None = None, model: str = "claude-opus") -> list[Message]:
    if not title.strip() or len(body.strip()) < 20:
        return [
            Message(
                type="replan_needed",
                run_id=run_id,
                role="architect",
                tags=["architect"],
                payload={"reason": "issue is too ambiguous to decompose"},
            )
        ]
    model_text = None
    if provider:
        response = complete_with_retry(
            provider,
            ModelRequest(run_id=run_id, role="architect", model=model, prompt=architect_prompt(title, body)),
        )
        model_text = response.text
        try:
            subtasks = parse_architect_json(response.text)
        except (KeyError, TypeError, ValueError):
            subtasks = []
        if subtasks:
            return _messages_from_subtasks(run_id, title, body, subtasks, model_text)

    subtasks = [
        Subtask("task-board", "Implement task board", InterfaceContract(["mast/board.py", "mast/messages.py"], ["JsonlTaskBoard"], ["tests/test_board.py"])),
        Subtask("worker", "Implement coder worker", InterfaceContract(["mast/coder.py", "mast/scope.py"], ["CoderWorker"], ["tests/test_flow.py"]), ["task-board"]),
        Subtask("gates", "Implement review and test gates", InterfaceContract(["mast/reviewer.py", "mast/tester.py"], ["Reviewer", "Tester"], ["tests/test_flow.py"]), ["worker"]),
        Subtask("report", "Implement metrics and report", InterfaceContract(["mast/observability.py", "mast/reporting.py"], ["TraceLog"], ["tests/test_flow.py"]), ["gates"]),
    ]
    validate_dag(subtasks)
    return _messages_from_subtasks(run_id, title, body, subtasks, model_text)


def _messages_from_subtasks(run_id: str, title: str, body: str, subtasks: list[Subtask], model_text: str | None) -> list[Message]:
    messages = [
        Message(
            type="plan_request",
            run_id=run_id,
            role="architect",
            tags=["architect"],
            payload={"title": title, "issue_body": body[:2000], "model_output": model_text, "subtask_ids": [task.id for task in subtasks]},
        )
    ]
    for task in subtasks:
        messages.append(
            Message(
                type="subtask",
                run_id=run_id,
                role="architect",
                tags=["coder", task.id],
                subtask_id=task.id,
                payload={
                    "title": task.title,
                    "depends_on": task.depends_on,
                    "contract": {
                        "files": task.contract.files,
                        "public_functions": task.contract.public_functions,
                        "test_impact": task.contract.test_impact,
                    },
                },
            )
        )
    return messages
