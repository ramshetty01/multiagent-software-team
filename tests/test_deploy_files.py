from __future__ import annotations

from pathlib import Path


def test_kubernetes_manifests_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "deploy/k8s/configmap.yaml").exists()
    assert "HorizontalPodAutoscaler" in (root / "deploy/k8s/deployments.yaml").read_text()

