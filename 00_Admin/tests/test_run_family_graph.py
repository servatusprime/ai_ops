"""Unittest coverage for run-family validation, resolution, and views."""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

ADMIN = Path(__file__).resolve().parents[1]
SCRIPTS = ADMIN / "scripts"
FIXTURES = Path(__file__).parent / "fixtures" / "run_family"
VALID = FIXTURES / "run_family_shared_valid.yaml"


def load_module(name: str):
    path = SCRIPTS / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_run_family_graph")
resolver = load_module("resolve_run_family")
generator = load_module("generate_run_family_views")
repo_validator = load_module("validate_repo_rules")


def load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class RunFamilyGraphTests(unittest.TestCase):
    def test_vs036_orchestrates_contract_and_drift_checks(self):
        completed = subprocess.CompletedProcess([], 0, stdout="pass", stderr="")
        with mock.patch.object(
            repo_validator.subprocess, "run", side_effect=[completed, completed]
        ) as run:
            errors = []
            repo_validator.check_run_family_graph_contract(
                {
                    "validator_script": "00_Admin/scripts/validate_run_family_graph.py",
                    "generator_script": "00_Admin/scripts/generate_run_family_views.py",
                    "registry": "00_Admin/runbooks/run_family_registry.yaml",
                    "runbooks_readme": "00_Admin/runbooks/README.md",
                },
                str(ADMIN.parent),
                errors,
            )
        self.assertEqual(errors, [])
        self.assertEqual(run.call_count, 2)
        validator_command = run.call_args_list[0].args[0]
        generator_command = run.call_args_list[1].args[0]
        self.assertIn("--discover", validator_command)
        self.assertIn("--check-files", validator_command)
        self.assertIn("--check", generator_command)

    def test_track_b_ranges_and_both_reuse_levels(self):
        graph = validator.validate_graph(load(VALID))
        edges = {
            (edge["consumer_id"], edge["provider_id"]): edge
            for edge in graph["consumes"]
        }
        self.assertEqual(
            edges[("runprogram-alpha", "runbundle-shared")]["version_constraint"],
            ">=1.2,<2",
        )
        self.assertEqual(
            edges[("runbundle-shared", "runbook-shared")]["version_constraint"],
            ">=2,<3",
        )
        self.assertIn(("runprogram-beta", "runbundle-shared"), edges)
        self.assertIn(("runbundle-secondary", "runbook-shared"), edges)
        alpha_edge = edges[("runprogram-alpha", "runbundle-shared")]
        self.assertTrue(alpha_edge["gates"])
        self.assertTrue(alpha_edge["entry_artifacts"])
        self.assertTrue(alpha_edge["exit_artifacts"])
        self.assertEqual(
            alpha_edge["idempotency"]["key_fields"], ["run_instance_id"]
        )

    def test_version_range_evaluation_is_sole_provider_only(self):
        self.assertTrue(validator.version_satisfies(">=1.2,<2", "1.2.0"))
        self.assertTrue(validator.version_satisfies(">=2,<3", "2.0.0"))
        self.assertFalse(validator.version_satisfies(">=2,<3", "1.2.0"))
        graph = load(VALID)
        graph["consumes"][0]["version_constraint"] = ">=2,<3"
        with self.assertRaisesRegex(
            validator.ContractError, "version constraint not satisfied"
        ):
            validator.validate_graph(graph)

    def test_all_negative_fixtures_fail(self):
        cases = {
            "run_family_duplicate_home.yaml": "duplicate canonical_home",
            "run_family_missing_home.yaml": "missing fields: canonical_home",
            "run_family_cycle.yaml": "consumption cycle",
            "run_family_incompatible_interface.yaml": "incompatible interface",
            "run_family_manual_reverse_index.yaml": "top-level consumed_by",
            "run_family_copied_fork.yaml": "copied implementation hash",
        }
        for filename, message in cases.items():
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(validator.ContractError, message):
                    validator.validate_graph(
                        load(FIXTURES / "negative" / filename)
                    )

    def test_hidden_parent_default_fails(self):
        graph = load(VALID)
        target = next(
            row for row in graph["artifacts"]
            if row["artifact_id"] == "runbundle-shared"
        )
        target["canonical_home"] = (
            "00_Admin/runbooks/run_program_alpha/"
            "run_bundles/rnb_shared/manifest.yaml"
        )
        with self.assertRaisesRegex(
            validator.ContractError, "hidden parent default"
        ):
            validator.validate_graph(graph)

    def test_retired_module_runbook_home_fails(self):
        graph = load(VALID)
        target = next(
            row for row in graph["artifacts"]
            if row["artifact_id"] == "runbook-shared"
        )
        target["canonical_home"] = (
            "02_Modules/example/runbooks/rb_shared.md"
        )
        with self.assertRaisesRegex(
            validator.ContractError, "retired module runbooks home"
        ):
            validator.validate_graph(graph)

    def test_alias_records_and_fields_fail_closed(self):
        graph = load(VALID)
        graph["aliases"] = [{"alias_id": "old-runbook"}]
        with self.assertRaisesRegex(
            validator.ContractError, "unsupported top-level fields: aliases"
        ):
            validator.validate_graph(graph)

        graph = load(VALID)
        graph["artifacts"][0]["alias_id"] = "old-runprogram"
        with self.assertRaisesRegex(
            validator.ContractError, "unsupported fields: alias_id"
        ):
            validator.validate_graph(graph)

        graph = load(VALID)
        graph["consumes"][0]["alias_id"] = "old-edge"
        with self.assertRaisesRegex(
            validator.ContractError, "unsupported fields: alias_id"
        ):
            validator.validate_graph(graph)

    def test_missing_affected_consumer_disposition_fails(self):
        graph = validator.validate_graph(load(VALID))
        receipt = load(FIXTURES / "run_receipt_valid.yaml")
        receipt["affected_consumers"] = [
            row for row in receipt["affected_consumers"]
            if row["consumer_id"] != "runprogram-beta"
        ]
        with self.assertRaisesRegex(
            validator.ContractError,
            "missing affected-consumer disposition: runprogram-beta",
        ):
            validator.validate_affected_consumer_dispositions(
                graph, receipt, {"runbook-shared"}
            )

    def test_provider_receipt_valid_passes(self):
        receipt = load(FIXTURES / "provider_receipt_valid.yaml")
        self.assertIsNone(validator.validate_provider_receipt(receipt))

    def test_provider_receipt_negatives_fail(self):
        base = load(FIXTURES / "provider_receipt_valid.yaml")

        incomplete = {**base}
        del incomplete["substantiated_by"]
        with self.assertRaisesRegex(
            validator.ContractError, "missing fields: substantiated_by"
        ):
            validator.validate_provider_receipt(incomplete)

        bad_capability = {**base, "validated_capabilities": [{"capability": "x"}]}
        with self.assertRaisesRegex(
            validator.ContractError, r"capability\[0\] needs capability and evidence_ref"
        ):
            validator.validate_provider_receipt(bad_capability)

        bad_authority = {**base, "authority": "canonical"}
        with self.assertRaisesRegex(
            validator.ContractError, "authority must be derived_non_authoritative"
        ):
            validator.validate_provider_receipt(bad_authority)

    def test_intake_receipt_valid_passes(self):
        receipt = load(FIXTURES / "intake_receipt_valid.yaml")
        self.assertIsNone(validator.validate_intake_receipt(receipt))

    def test_intake_receipt_negatives_fail(self):
        no_disposition = load(FIXTURES / "intake_receipt_valid.yaml")
        del no_disposition["items"][0]["disposition"]
        with self.assertRaisesRegex(
            validator.ContractError, "disposition must be one of"
        ):
            validator.validate_intake_receipt(no_disposition)

        no_provenance = load(FIXTURES / "intake_receipt_valid.yaml")
        del no_provenance["items"][0]["provenance"]
        with self.assertRaisesRegex(
            validator.ContractError, "missing provenance"
        ):
            validator.validate_intake_receipt(no_provenance)

        admitted_no_evidence = load(FIXTURES / "intake_receipt_valid.yaml")
        del admitted_no_evidence["items"][0]["evidence_ref"]
        with self.assertRaisesRegex(
            validator.ContractError, "requires evidence_ref"
        ):
            validator.validate_intake_receipt(admitted_no_evidence)

    def test_execution_graph_valid_passes(self):
        graph = load(FIXTURES / "execution_graph_valid.yaml")
        self.assertIsNone(validator.validate_execution_graph(graph))

    def test_execution_graph_negatives_fail(self):
        no_owner = load(FIXTURES / "execution_graph_valid.yaml")
        del no_owner["reasoning_owner"]
        with self.assertRaisesRegex(
            validator.ContractError, "missing fields: reasoning_owner"
        ):
            validator.validate_execution_graph(no_owner)

        agentic_no_pack = load(FIXTURES / "execution_graph_valid.yaml")
        del agentic_no_pack["nodes"][0]["onboarding"]
        with self.assertRaisesRegex(
            validator.ContractError, r"\(agentic\) needs a non-empty"
        ):
            validator.validate_execution_graph(agentic_no_pack)

        det_no_hash = load(FIXTURES / "execution_graph_valid.yaml")
        det_no_hash["nodes"][2]["determinism"]["content_hashed"] = False
        with self.assertRaisesRegex(
            validator.ContractError, r"\(deterministic\) must declare"
        ):
            validator.validate_execution_graph(det_no_hash)

        unbounded_loop = load(FIXTURES / "execution_graph_valid.yaml")
        del unbounded_loop["edges"][1]["loop"]["max_cycles"]
        with self.assertRaisesRegex(
            validator.ContractError, "needs max_cycles"
        ):
            validator.validate_execution_graph(unbounded_loop)

        bad_escalation = load(FIXTURES / "execution_graph_valid.yaml")
        bad_escalation["edges"][1]["loop"]["on_exceed"]["escalate_to"] = "reviewer"
        with self.assertRaisesRegex(
            validator.ContractError, "reasoning_owner or operator"
        ):
            validator.validate_execution_graph(bad_escalation)

        undeclared_cycle = load(FIXTURES / "execution_graph_valid.yaml")
        undeclared_cycle["edges"].append(
            {"from": "accept", "to": "intake", "condition": "restart"}
        )
        with self.assertRaisesRegex(
            validator.ContractError, "undeclared cycle"
        ):
            validator.validate_execution_graph(undeclared_cycle)

        unknown_node = load(FIXTURES / "execution_graph_valid.yaml")
        unknown_node["edges"][0]["to"] = "ghost"
        with self.assertRaisesRegex(
            validator.ContractError, "unknown node id: ghost"
        ):
            validator.validate_execution_graph(unknown_node)

        composition_leak = load(FIXTURES / "execution_graph_valid.yaml")
        composition_leak["nodes"][0]["consumes"] = ["something"]
        with self.assertRaisesRegex(
            validator.ContractError, "must not carry composition/identity"
        ):
            validator.validate_execution_graph(composition_leak)

        agentic_no_gate = load(FIXTURES / "execution_graph_valid.yaml")
        del agentic_no_gate["nodes"][1]["gate"]
        with self.assertRaisesRegex(
            validator.ContractError, r"\(agentic\) must declare a gate"
        ):
            validator.validate_execution_graph(agentic_no_gate)

        agentic_no_handoff = load(FIXTURES / "execution_graph_valid.yaml")
        del agentic_no_handoff["nodes"][1]["handoff"]
        with self.assertRaisesRegex(
            validator.ContractError, "must declare handoff.return_contract"
        ):
            validator.validate_execution_graph(agentic_no_handoff)

        duplicate_id = load(FIXTURES / "execution_graph_valid.yaml")
        duplicate_id["nodes"][1]["id"] = "intake"
        with self.assertRaisesRegex(
            validator.ContractError, "node id is duplicated: intake"
        ):
            validator.validate_execution_graph(duplicate_id)

        bad_checkpoint = load(FIXTURES / "execution_graph_valid.yaml")
        bad_checkpoint["edges"][0]["checkpoint"] = "whenever"
        with self.assertRaisesRegex(
            validator.ContractError, "checkpoint must be one of"
        ):
            validator.validate_execution_graph(bad_checkpoint)

        empty_evidence = load(FIXTURES / "execution_graph_valid.yaml")
        empty_evidence["edges"][0]["entry_evidence"] = "  "
        with self.assertRaisesRegex(
            validator.ContractError, "entry_evidence must be a non-empty string"
        ):
            validator.validate_execution_graph(empty_evidence)

        empty_owner = load(FIXTURES / "execution_graph_valid.yaml")
        empty_owner["owner_id"] = ""
        with self.assertRaisesRegex(
            validator.ContractError, "owner_id must be a non-empty string"
        ):
            validator.validate_execution_graph(empty_owner)

        agentic_no_write_scope = load(FIXTURES / "execution_graph_valid.yaml")
        del agentic_no_write_scope["nodes"][0]["handoff"]["write_scope"]
        with self.assertRaisesRegex(
            validator.ContractError, "must declare handoff.write_scope"
        ):
            validator.validate_execution_graph(agentic_no_write_scope)

        extra_graph_field = load(FIXTURES / "execution_graph_valid.yaml")
        extra_graph_field["foo"] = "bar"
        with self.assertRaisesRegex(
            validator.ContractError, "graph has unsupported fields: foo"
        ):
            validator.validate_execution_graph(extra_graph_field)

        extra_node_field = load(FIXTURES / "execution_graph_valid.yaml")
        extra_node_field["nodes"][0]["foo"] = "bar"
        with self.assertRaisesRegex(
            validator.ContractError, "node .* has unsupported fields: foo"
        ):
            validator.validate_execution_graph(extra_node_field)

        extra_edge_field = load(FIXTURES / "execution_graph_valid.yaml")
        extra_edge_field["edges"][0]["foo"] = "bar"
        with self.assertRaisesRegex(
            validator.ContractError, "edge .* has unsupported fields: foo"
        ):
            validator.validate_execution_graph(extra_edge_field)

        critical_missing_control = load(FIXTURES / "execution_graph_valid.yaml")
        del critical_missing_control["edges"][0]["checkpoint"]
        with self.assertRaisesRegex(
            validator.ContractError, "is critical .* and must declare: checkpoint"
        ):
            validator.validate_execution_graph(critical_missing_control)

        route_ghost = load(FIXTURES / "execution_graph_valid.yaml")
        route_ghost["routes"][0]["sequence"][0]["node"] = "ghost"
        with self.assertRaisesRegex(
            validator.ContractError, "route .* references unknown node: ghost"
        ):
            validator.validate_execution_graph(route_ghost)

        bad_depends = load(FIXTURES / "execution_graph_valid.yaml")
        bad_depends["routes"][1]["depends_on_route"] = "nope"
        with self.assertRaisesRegex(
            validator.ContractError, "depends_on_route references unknown route: nope"
        ):
            validator.validate_execution_graph(bad_depends)

        dup_route = load(FIXTURES / "execution_graph_valid.yaml")
        dup_route["routes"][1]["route_id"] = "intake_main"
        with self.assertRaisesRegex(
            validator.ContractError, "route_id is duplicated: intake_main"
        ):
            validator.validate_execution_graph(dup_route)

    def test_execution_graph_nested_parity_rejected(self):
        base = load(FIXTURES / "execution_graph_valid.yaml")
        cases = [
            (lambda d: d["nodes"][0]["interface"].__setitem__("foo", "x"), "interface has unsupported"),
            (lambda d: d["nodes"][0]["handoff"].__setitem__("foo", "x"), "handoff has unsupported"),
            (lambda d: d["nodes"][2]["determinism"].__setitem__("foo", "x"), "determinism has unsupported"),
            (lambda d: d["nodes"][0]["onboarding"].__setitem__("foo", "x"), "onboarding has unsupported"),
            (lambda d: d["edges"][1]["loop"].__setitem__("foo", "x"), "loop has unsupported"),
            (lambda d: d["edges"][1]["loop"]["on_exceed"].__setitem__("foo", "x"), "on_exceed has unsupported"),
            (lambda d: d["edges"][0].__setitem__("critical", "true"), "critical must be a boolean"),
            (lambda d: d["routes"][0].__setitem__("foo", "x"), "route .* has unsupported"),
            (lambda d: d["routes"][0]["sequence"][0].__setitem__("foo", "x"), "step has unsupported"),
            (lambda d: d["routes"][0].__setitem__("depends_on_route", "intake_main"), "cannot depend on itself"),
            (lambda d: d["routes"][0]["sequence"][1].__setitem__("order", 1), "duplicate step order"),
        ]
        for mutate, message in cases:
            with self.subTest(message=message):
                graph = load(FIXTURES / "execution_graph_valid.yaml")
                mutate(graph)
                with self.assertRaisesRegex(validator.ContractError, message):
                    validator.validate_execution_graph(graph)
        self.assertIsNone(validator.validate_execution_graph(base))

    def test_run_state_nested_parity_rejected(self):
        graph = load(FIXTURES / "execution_graph_valid.yaml")
        counter_extra = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        counter_extra["loop_counters"][0]["foo"] = "x"
        with self.assertRaisesRegex(validator.ContractError, "loop_counter.* has unsupported"):
            validator.validate_execution_graph_run_state(counter_extra, graph)
        bad_receipt = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        bad_receipt["handoff_receipts"].append(123)
        with self.assertRaisesRegex(validator.ContractError, "handoff_receipts must be non-empty"):
            validator.validate_execution_graph_run_state(bad_receipt, graph)

    def test_canonical_execution_graph_template_validates(self):
        template = load(
            ADMIN.parent
            / "01_Resources/templates/workflows/execution_graph_template.yaml"
        )
        self.assertIsNone(validator.validate_execution_graph(template))

    def test_execution_graph_run_state_valid_passes(self):
        state = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        graph = load(FIXTURES / "execution_graph_valid.yaml")
        self.assertIsNone(validator.validate_execution_graph_run_state(state, graph))
        # standalone (no graph) still validates shape
        self.assertIsNone(validator.validate_execution_graph_run_state(state))

    def test_execution_graph_run_state_negatives_fail(self):
        graph = load(FIXTURES / "execution_graph_valid.yaml")

        running_no_current = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        del running_no_current["current_node"]
        with self.assertRaisesRegex(
            validator.ContractError, "status running needs current_node"
        ):
            validator.validate_execution_graph_run_state(running_no_current, graph)

        wrong_hash = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        wrong_hash["graph_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            validator.ContractError, "does not match the supplied graph"
        ):
            validator.validate_execution_graph_run_state(wrong_hash, graph)

        loop_exceeds = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        loop_exceeds["loop_counters"][0]["count"] = 9
        with self.assertRaisesRegex(
            validator.ContractError, "exceeded max_cycles"
        ):
            validator.validate_execution_graph_run_state(loop_exceeds, graph)

        ghost_node = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        ghost_node["current_node"] = "ghost"
        with self.assertRaisesRegex(
            validator.ContractError, "current_node is not a graph node"
        ):
            validator.validate_execution_graph_run_state(ghost_node, graph)

        owner_mismatch = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        owner_mismatch["owner_id"] = "run_program_other"
        with self.assertRaisesRegex(
            validator.ContractError, "owner_id .* does not match graph owner_id"
        ):
            validator.validate_execution_graph_run_state(owner_mismatch, graph)

        empty_state_owner = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        empty_state_owner["owner_id"] = ""
        with self.assertRaisesRegex(
            validator.ContractError, "owner_id must be a non-empty string"
        ):
            validator.validate_execution_graph_run_state(empty_state_owner)

        extra_state_field = load(FIXTURES / "execution_graph_run_state_valid.yaml")
        extra_state_field["foo"] = "bar"
        with self.assertRaisesRegex(
            validator.ContractError, "run-state has unsupported fields: foo"
        ):
            validator.validate_execution_graph_run_state(extra_state_field, graph)

    def test_standalone_validator_cli_routes(self):
        script = SCRIPTS / "validate_run_family_graph.py"
        for arg, fixture in (
            ("--execution-graph", "execution_graph_valid.yaml"),
            ("--provider-receipt", "provider_receipt_valid.yaml"),
            ("--intake-receipt", "intake_receipt_valid.yaml"),
        ):
            with self.subTest(arg=arg):
                result = subprocess.run(
                    [sys.executable, str(script), arg, str(FIXTURES / fixture)],
                    check=False, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
        # no source and no standalone arg -> contract error (exit 1)
        empty = subprocess.run(
            [sys.executable, str(script)], check=False,
            capture_output=True, text=True,
        )
        self.assertEqual(empty.returncode, 1)
        self.assertIn("supply a composition source", empty.stderr)

    def test_registry_readme_parity_fails(self):
        registry = {
            "artifacts": [
                {
                    "artifact_id": "runbook-shared",
                    "artifact_kind": "runbook",
                }
            ]
        }
        with self.assertRaisesRegex(
            validator.ContractError, "README/registry parity"
        ):
            validator.validate_registry_readme_parity(
                registry, "# Runbooks Index\n"
            )

    def test_resolver_locks_exact_versions_and_is_deterministic(self):
        graph = load(VALID)
        first = resolver.resolve(
            graph,
            root_id="runprogram-alpha",
            run_instance_id="test-run-001",
        )
        second = resolver.resolve(
            graph,
            root_id="runprogram-alpha",
            run_instance_id="test-run-001",
        )
        self.assertEqual(first, second)
        lock, context = first
        self.assertEqual(
            [row["artifact_id"] for row in lock["resolved_artifacts"]],
            ["runbook-shared", "runbundle-shared", "runprogram-alpha"],
        )
        self.assertEqual(
            {edge["artifact_version"] for edge in lock["resolved_edges"]},
            {"1.2.0", "2.0.0"},
        )
        self.assertFalse(
            any(
                any(symbol in edge["artifact_version"] for symbol in "<>=")
                for edge in lock["resolved_edges"]
            )
        )
        self.assertEqual(
            context["selected_artifact_ids"],
            ["runbook-shared", "runbundle-shared", "runprogram-alpha"],
        )
        self.assertEqual(
            lock["selected_route"],
            ["runprogram-alpha", "runbundle-shared", "runbook-shared"],
        )
        self.assertTrue(lock["gates"])
        self.assertTrue(lock["receipt_references"])
        self.assertEqual(context["resolved_interfaces"]["runbook-shared"], "2")
        self.assertEqual(context["required_gates"], lock["gates"])

    def test_generated_reverse_edges_are_derived_and_deterministic(self):
        first = generator.build_views(load(VALID))
        second = generator.build_views(load(VALID))
        self.assertEqual(first, second)
        registry = first["registry"]
        self.assertEqual(registry["authority"], "derived_non_authoritative")
        shared_bundle = next(
            row for row in registry["artifacts"]
            if row["artifact_id"] == "runbundle-shared"
        )
        self.assertEqual(
            shared_bundle["consumed_by"],
            ["runprogram-alpha", "runprogram-beta"],
        )

    def test_governance_routing_projects_workflows_specs_and_vs036(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            routing = root / "00_Admin/configs/context_routing.yaml"
            validator_config = (
                root / "00_Admin/configs/validator/validator_config.yaml"
            )
            workflow = root / ".ai_ops/workflows/work.md"
            routing.parent.mkdir(parents=True)
            validator_config.parent.mkdir(parents=True)
            workflow.parent.mkdir(parents=True)
            routing.write_text(
                "commands:\n"
                "  work:\n"
                "    default:\n"
                "      read_on_demand:\n"
                "        - ai_ops/00_Admin/specs/spec_artifact_graph_identity.md\n",
                encoding="utf-8",
            )
            validator_config.write_text(
                "rules:\n"
                "  - id: VS036\n"
                "    enabled: true\n"
                "    params:\n"
                "      validator_script: 00_Admin/scripts/validate_run_family_graph.py\n"
                "      generator_script: 00_Admin/scripts/generate_run_family_views.py\n"
                "      registry: 00_Admin/runbooks/run_family_registry.yaml\n"
                "      runbooks_readme: 00_Admin/runbooks/README.md\n",
                encoding="utf-8",
            )
            workflow.write_text(
                "# Work\n\n### Run-Family Graph Hook\n",
                encoding="utf-8",
            )
            view = generator.build_governance_routing_view(root)
        self.assertEqual(view["authority"], "derived_non_authoritative")
        self.assertEqual(
            view["scope"], "run_family_workflow_spec_validator_projection"
        )
        node_ids = {node["id"] for node in view["nodes"]}
        self.assertIn("command:work", node_ids)
        self.assertIn("validator:VS036", node_ids)
        self.assertIn(
            "artifact:00_Admin/specs/spec_artifact_graph_identity.md",
            node_ids,
        )
        edge_kinds = {edge["kind"] for edge in view["edges"]}
        self.assertTrue({"implemented_by", "reads_on_demand", "invokes"} <= edge_kinds)

    def test_example_evidence_is_non_authoritative(self):
        lock = load(FIXTURES / "run_instance_lock_valid.yaml")
        context = load(FIXTURES / "run_family_context_pack_valid.yaml")
        receipt = load(FIXTURES / "run_receipt_valid.yaml")
        self.assertEqual(lock["authority"], "derived_resolution_evidence")
        self.assertEqual(context["authority"], "derived_non_authoritative")
        self.assertEqual(
            receipt["authority"], "execution_evidence_non_authoritative"
        )
        self.assertTrue(lock["selected_route"])
        self.assertTrue(lock["receipt_references"])
        self.assertTrue(context["resolved_interfaces"])
        self.assertTrue(context["required_gates"])
        self.assertTrue(receipt["inputs"])
        self.assertTrue(receipt["gates"])

    def test_generator_write_check_and_drift_modes(self):
        script = SCRIPTS / "generate_run_family_views.py"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write = subprocess.run(
                [
                    sys.executable, str(script), "--repo-root", str(root),
                    "--input", str(VALID), "--write",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(write.returncode, 0, write.stderr)
            check = subprocess.run(
                [
                    sys.executable, str(script), "--repo-root", str(root),
                    "--input", str(VALID), "--check",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(check.returncode, 0, check.stderr)
            target = (
                root / "00_Admin" / "reports" / "generated" / "graphs"
                / "run_family_graph.yaml"
            )
            target.write_text(
                target.read_text(encoding="utf-8") + "# drift\n",
                encoding="utf-8",
            )
            drift = subprocess.run(
                [
                    sys.executable, str(script), "--repo-root", str(root),
                    "--input", str(VALID), "--check",
                ],
                check=False, capture_output=True, text=True,
            )
            self.assertEqual(drift.returncode, 1)
            self.assertIn("drift:", drift.stderr)

    def test_dedicated_validator_cli_and_schema_yaml(self):
        script = SCRIPTS / "validate_run_family_graph.py"
        positive = subprocess.run(
            [sys.executable, str(script), "--input", str(VALID)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(positive.returncode, 0, positive.stderr)
        negative = subprocess.run(
            [
                sys.executable,
                str(script),
                "--input",
                str(FIXTURES / "negative" / "run_family_cycle.yaml"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(negative.returncode, 1)
        self.assertIn("consumption cycle", negative.stderr)
        for name in (
            "schema_run_family_consumption.yaml",
            "schema_run_family_registry.yaml",
            "schema_run_family_manifest.yaml",
            "schema_run_instance_lock.yaml",
            "schema_run_family_context_pack.yaml",
            "schema_run_receipt.yaml",
            "schema_run_family_provider_receipt.yaml",
            "schema_run_family_intake_receipt.yaml",
            "schema_execution_graph.yaml",
            "schema_execution_graph_run_state.yaml",
        ):
            schema = load(ADMIN / "configs" / "validator" / name)
            self.assertTrue(schema["$schema"].endswith("2020-12/schema"))

    def test_schema_matches_runtime_edge_and_manifest_contract(self):
        consumption = load(
            ADMIN / "configs" / "validator"
            / "schema_run_family_consumption.yaml"
        )
        manifest = load(
            ADMIN / "configs" / "validator"
            / "schema_run_family_manifest.yaml"
        )
        required_edge_fields = {
            "gates", "entry_artifacts", "exit_artifacts", "idempotency"
        }
        consumption_edge = consumption["$defs"]["consumes_edge"]
        manifest_edge = manifest["$defs"]["consumer_edge"]
        self.assertTrue(required_edge_fields <= set(consumption_edge["required"]))
        self.assertTrue(required_edge_fields <= set(manifest_edge["required"]))
        self.assertIn("content_sha256", manifest["required"])
        self.assertTrue(
            validator.ARTIFACT_REQUIRED <= set(manifest["required"])
        )
        self.assertTrue(
            validator.ARTIFACT_REQUIRED
            <= set(consumption["$defs"]["artifact"]["required"])
        )
        self.assertTrue(validator.EDGE_REQUIRED <= set(consumption_edge["required"]))
        self.assertTrue(validator.EDGE_REQUIRED <= set(manifest_edge["required"]))
        consumption_pattern = consumption["$defs"]["version_constraint"]["pattern"]
        manifest_pattern = manifest_edge["properties"]["version_constraint"]["pattern"]
        for pattern in (consumption_pattern, manifest_pattern):
            for edge in load(VALID)["consumes"]:
                self.assertIsNotNone(
                    re.fullmatch(pattern, edge["version_constraint"])
                )
            self.assertIsNotNone(re.fullmatch(pattern, "1.2.0"))
            self.assertIsNone(re.fullmatch(pattern, "latest"))


if __name__ == "__main__":
    unittest.main()
