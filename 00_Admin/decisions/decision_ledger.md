---
artifact_type: source
status: active
updated: 2026-05-04
moved_from: 00_Admin/context/decision_ledger.md
moved_date: 2026-01-11
---

# Decision Ledger

This ledger records irreversible, cross-cutting governance decisions. Entries are rare and require human approval
(requestor).

## Entries

- **AI-First Governance** - AI agents are the primary execution and reasoning layer; humans supervise/approve.
- **AI-Human Conversations Are Disposable** - Conversations are a drafting surface; the repo is the source of truth.
  Archive chats once outcomes are encoded.
- **Agent-Driven Ledger Detection** - AI agents must flag governance-level decisions; human approval is required before
  logging.
- **AI-Native Source of Truth** - The project is AI-first: AI agents are the primary execution and reasoning layer.
  Human interaction occurs at a supervisory and derivative layer; artifacts are produced for AI consumption first, and
  human-facing views are projections of that core.
- **Artifact-First System of Record** - Work state belongs in repository artifacts;
  conversation is UI, not system of record.
- **Single-Primary-Axis Rule** - Each artifact must have one primary organizing axis;
  mixed-responsibility artifacts are governance drift.
- **Governance-Behavior Separation** - Governance rules are stable and always-on;
  agent communication/personality style is opt-in and layered separately.
- **Portable Governance Outcomes** - Governance intent and validation remain
  repository-owned and must survive runtime/platform differences via graceful degradation.
- **Independent Crosscheck Requirement** - Same-thread self-review is structural
  validation only; crosscheck quality requires an independent review context.
- **Two-Axis Governance Framework Is Canonical** - ai_ops uses organizing axes
  (Intent, Commitment, Execution, Verification, Meta) and quality axes
  (Clarity, Thrift, Context, Governance) as the standard classification and
  review framework for artifacts and operations.
- **Explicit Authority Gate Model Is Mandatory** - Authority levels are explicit
  and enforced; higher-impact changes require structured approval and rationale
  rather than implied permission.
- **Work-Family and Run-Family Separation** - Planning/commitment artifacts and
  reusable execution artifacts remain distinct; workbooks bind to runbooks by
  reference to prevent intent/tool lock and commitment leakage.
- **Canonical Lanes Govern Execution** - Execution responsibilities are
  assigned by canonical lane contracts and constraints, not by personality
  identity; lane behavior is portable across runtimes.
- **Verification Is Embedded, Not Terminal** - Verification is integrated
  throughout the lifecycle via selfcheck, crosscheck, closeout validation, and
  health review, not deferred to an end-only gate.
- **Compacted Context Is Required for Handoff** - Cross-lane/session handoffs
  must use structured compacted context so work can resume from repository files
  without chat-history dependency.
- **Native-Session vs Governed-Work Boundary** - Native platform commands manage
  session/runtime concerns, while ai_ops commands govern scope, authority,
  verification, and artifact lifecycle.
- **Mandatory Policy Decision Record (PDR) at L2+** - At L2+ authority evaluations,
  agents emit a structured `policy_decision:` YAML block per
  `00_Admin/specs/spec_policy_decision_record.md`, making governance decisions observable
  and auditable. Formalizes the implicit decision requirement of the Explicit Authority
  Gate Model.

## How to Propose a New Entry

- Agent raises "Ledger Candidate" with decision, why it qualifies, and expected impact.
- requestor approves/rejects/revises.
- On approval, append under "Entries" with Date and Approved by (ai_ops).
