"""Tests for the separate run-family executability closure gate."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_graph_artifact_closure.py"
spec = importlib.util.spec_from_file_location("validate_graph_artifact_closure", SCRIPT)
assert spec and spec.loader
closure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(closure)


def write_yaml(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def manifest(artifact_id: str, home: str, entries: str, consumes: str) -> str:
    return f"""\
manifest_version: '0.1.0'
artifact_id: {artifact_id}
artifact_kind: runprogram
canonical_home: {home}/README.md
artifact_version: 1.0.0
interface_version: '1'
lifecycle: active
promotion_target: '{home}/README.md'
promotion_gate: 'requestor approval'
steward: ai_ops
content_sha256: {'a' * 64}
entry_artifacts: {entries}
parameter_profiles: {{}}
consumes: {consumes}
"""


class ClosureTests(unittest.TestCase):
    def test_internal_and_external_inputs_pass(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "00_Admin/runbooks/program"
            write_yaml(
                home / "manifest.yaml",
                manifest("program", "00_Admin/runbooks/program", "[external_input]", "[]"),
            )
            write_yaml(
                home / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: start
                        kind: operator
                        interface:
                          binding: resolved_per_run
                          consumes: [external_input]
                          produces: [prepared]
                    """
                ),
            )
            self.assertEqual(closure.validate_closure(root), [])

    def test_unsatisfied_input_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "00_Admin/runbooks/program"
            write_yaml(
                home / "manifest.yaml",
                manifest("program", "00_Admin/runbooks/program", "[]", "[]"),
            )
            write_yaml(
                home / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: render
                        kind: deterministic
                        determinism:
                          idempotent: true
                          content_hashed: true
                        interface:
                          binding: resolved_per_run
                          consumes: [missing_input]
                          produces: [rendered]
                    """
                ),
            )
            findings = closure.validate_closure(root)
            self.assertEqual(len(findings), 1)
            self.assertIn("missing_input", findings[0])

    def test_self_produced_input_does_not_count_as_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "00_Admin/runbooks/program"
            write_yaml(
                home / "manifest.yaml",
                manifest("program", "00_Admin/runbooks/program", "[]", "[]"),
            )
            write_yaml(
                home / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: loop
                        kind: deterministic
                        determinism:
                          idempotent: true
                          content_hashed: true
                        interface:
                          binding: resolved_per_run
                          consumes: [looped]
                          produces: [looped]
                    """
                ),
            )
            findings = closure.validate_closure(root)
            self.assertEqual(len(findings), 1)
            self.assertIn("looped", findings[0])

    def test_legacy_entry_label_does_not_satisfy_closure(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            home = root / "00_Admin/runbooks/program"
            write_yaml(
                home / "manifest.yaml",
                manifest(
                    "program",
                    "00_Admin/runbooks/program",
                    "[Legacy external label]",
                    "[]",
                ),
            )
            write_yaml(
                home / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: render
                        kind: deterministic
                        determinism:
                          idempotent: true
                          content_hashed: true
                        interface:
                          binding: resolved_per_run
                          consumes: [legacy_input]
                          produces: [rendered]
                    """
                ),
            )
            findings = closure.validate_closure(root)
            self.assertEqual(len(findings), 1)
            self.assertIn("legacy_input", findings[0])

    def test_composed_provider_satisfies_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            provider = root / "00_Admin/runbooks/provider"
            consumer = root / "00_Admin/runbooks/consumer"
            write_yaml(
                provider / "manifest.yaml",
                manifest("provider", "00_Admin/runbooks/provider", "[]", "[]"),
            )
            write_yaml(
                provider / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: source
                        kind: operator
                        interface:
                          binding: resolved_per_run
                          consumes: []
                          produces: [provider_output]
                    """
                ),
            )
            write_yaml(
                consumer / "manifest.yaml",
                manifest(
                    "consumer",
                    "00_Admin/runbooks/consumer",
                    "[]",
                    "[{provider_id: provider}]",
                ),
            )
            write_yaml(
                consumer / "execution_graph.yaml",
                dedent(
                    """
                    nodes:
                      - id: use
                        kind: deterministic
                        determinism:
                          idempotent: true
                          content_hashed: true
                        interface:
                          binding: resolved_per_run
                          consumes: [provider_output]
                          produces: [consumer_output]
                    """
                ),
            )
            self.assertEqual(closure.validate_closure(root), [])


if __name__ == "__main__":
    unittest.main()
