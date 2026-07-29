from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    template: str

    def render(self, **kwargs) -> str:
        return self.template.format(**kwargs)


PROMPTS = {
    "architect.plan": PromptTemplate(
        "architect.plan",
        "2026-07-30",
        "Decompose this GitHub issue into JSON with a `subtasks` array. Title: {title}\n\nBody:\n{body}",
    ),
    "coder.patch": PromptTemplate(
        "coder.patch",
        "2026-07-30",
        "Implement exactly this subtask and return a unified diff only.\n\nSubtask:\n{subtask}\n\nFiles:\n{files}",
    ),
    "reviewer.diff": PromptTemplate(
        "reviewer.diff",
        "2026-07-30",
        "Review only this merged diff. Return structured JSON.\n\nOwnership:\n{ownership}\n\nDiff:\n{diff}",
    ),
}


def get_prompt(name: str) -> PromptTemplate:
    return PROMPTS[name]

