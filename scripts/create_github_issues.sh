#!/usr/bin/env sh
set -eu

repo="${1:?usage: scripts/create_github_issues.sh owner/repo}"

python3 - "$repo" <<'PY'
import re
import subprocess
import sys
import tempfile
from pathlib import Path

repo = sys.argv[1]
text = Path("docs/github-issues.md").read_text()
blocks = re.split(r"\n## \d+\. ", text)[1:]

for block in blocks:
    title, body = block.split("\n", 1)
    labels_match = re.search(r"^Labels: `([^`]+)`(?:, `([^`]+)`)?", body, re.M)
    labels = []
    if labels_match:
        labels = [value for value in labels_match.groups() if value]
        body = re.sub(r"^Labels: .*\n\n", "", body, count=1, flags=re.M)

    for label in labels:
        subprocess.run(
            ["gh", "label", "create", label, "--repo", repo, "--force"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    with tempfile.NamedTemporaryFile("w", delete=False) as handle:
        handle.write(body.strip() + "\n")
        body_file = handle.name

    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title.strip(), "--body-file", body_file]
    for label in labels:
        cmd.extend(["--label", label])
    subprocess.run(cmd, check=True)
PY
