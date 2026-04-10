<!--
Sync Impact Report
==================
Version change: (unfilled template) → 1.0.0
Modified principles: N/A — first ratification; all placeholders resolved.
Added sections:
  - Core Principles (I–V)
  - Development Workflow
  - Quality & Compliance
  - Governance
Removed sections: None (template HTML comments stripped; no content removed)
Templates checked:
  - .specify/templates/plan-template.md      ✅ no changes needed (Constitution Check is dynamically filled by /speckit-plan)
  - .specify/templates/spec-template.md      ✅ mandatory sections align with Principle II and Quality & Compliance
  - .specify/templates/tasks-template.md     ✅ phase structure aligns with Principle IV
  - .specify/templates/agent-file-template.md ✅ no outdated agent-specific references
  - .specify/templates/checklist-template.md  ✅ compatible with Quality & Compliance gate
Follow-up TODOs:
  - None — all placeholders resolved. RATIFICATION_DATE set to first fill date (2026-04-09).
-->

# SDD Constitution

## Core Principles

### I. Spec-First Development

Every feature MUST start with a written specification before any implementation begins.
Specifications MUST be technology-agnostic, written for non-technical stakeholders, and
organized as independently testable user stories. Implementation MUST NOT begin until the
spec passes all Specification Quality Checklist items.

**Rationale**: Prevents costly rework by aligning intent before effort is committed.
The spec is the single source of truth for what is being built and why.

### II. User-Story-Centric Design

Features MUST be broken into independently testable user stories (P1, P2, P3…).
Each story MUST be deliverable, demonstrable, and testable without requiring other stories
to be complete. Task organization in `tasks.md` MUST map 1-to-1 to user stories from
`spec.md`. A feature with no independently testable user story MUST NOT proceed to planning.

**Rationale**: Enables incremental delivery, parallel team execution, and genuine MVP
definitions. Prevents all-or-nothing delivery and untestable monolithic scopes.

### III. Constitution-Gated Planning

All implementation plans MUST include a Constitution Check gate evaluated before Phase 0
research and re-evaluated after Phase 1 design. Plans with unjustified constitution
violations MUST NOT proceed to task generation. Every violation MUST be logged in the
Complexity Tracking table with explicit justification.

**Rationale**: Checking governance compliance at plan-time — not post-hoc — keeps the
cost of correction low and prevents drift from accumulating silently.

### IV. Phase-Validated Execution

Implementation MUST proceed phase-by-phase: Setup → Foundational → User Stories (P1 first)
→ Polish. Each phase MUST be validated before the next begins. All incomplete checklist
items MUST be resolved or explicitly waived (with written rationale) before implementation
starts. Tasks within a phase that are marked `[P]` MAY run in parallel; all others MUST
run sequentially.

**Rationale**: Phase gates prevent compounding defects and ensure each increment is a
genuine, releasable unit of value rather than a partially integrated state.

### V. Simplicity & Minimalism

Complexity MUST be justified in writing. The Complexity Tracking table in `plan.md` MUST
capture every deviation from the simplest viable approach. YAGNI (You Aren't Gonna Need It)
applies by default. Speculative abstractions, premature generalization, and over-engineering
are prohibited. Three similar concrete implementations are preferred over one premature
abstraction.

**Rationale**: Complexity is the primary source of maintenance debt. Making trade-offs
explicit forces intentional design decisions rather than accidental accumulation.

## Development Workflow

The canonical workflow for every feature in this project is:

1. `/speckit-specify` — Write the feature specification (user stories, requirements, success
   criteria). **This step is never optional.**
2. `/speckit-clarify` — Resolve open questions before planning (recommended when any
   `[NEEDS CLARIFICATION]` markers remain after `/speckit-specify`).
3. `/speckit-plan` — Research, design, and produce implementation artifacts (research.md,
   data-model.md, contracts/, quickstart.md).
4. `/speckit-tasks` — Generate a dependency-ordered, user-story-mapped task list.
5. `/speckit-implement` — Execute tasks phase-by-phase, marking each complete in `tasks.md`.
6. `/speckit-checklist` — Create or review quality checklists at any stage as needed.
7. `/speckit-constitution` — Amend this document when governance changes are required.

Skipping steps requires explicit team agreement and documented rationale in the plan.
Skipping `/speckit-specify` is never permitted under any circumstance.

## Quality & Compliance

- Every specification MUST pass the Specification Quality Checklist before planning begins.
- Functional requirements MUST be testable and unambiguous. Vague language ("should",
  "might", "as needed") MUST be replaced with MUST/SHOULD/MAY with explicit rationale.
- Success criteria MUST be measurable, technology-agnostic, and expressed from the user or
  business perspective — never in terms of internal system metrics.
- A maximum of 3 `[NEEDS CLARIFICATION]` markers are permitted per spec. All MUST be
  resolved before implementation begins.
- All PRs and code reviews MUST verify compliance with this constitution.
- The agent context file MUST be updated via the agent context script after every Phase 1
  design to reflect current technologies and project structure.

## Governance

This constitution supersedes all other development practices in this repository. In the
event of conflict between this document and any other guide, this document prevails.

**Amendment procedure**:
1. Propose the change via `/speckit-constitution` (preferred) or direct edit with rationale.
2. Increment the version following the versioning policy below.
3. Update the Sync Impact Report HTML comment at the top of this file.
4. Propagate amendments to all dependent templates and agent context files.
5. Record the amendment date in the `Last Amended` field.

**Versioning policy**:
- MAJOR: Backward-incompatible principle removals, redefinitions, or workflow reorderings.
- MINOR: New principle or section added; materially expanded guidance.
- PATCH: Clarifications, wording improvements, typo fixes, non-semantic refinements.

**Compliance review**: This constitution MUST be reviewed whenever a new speckit version
is adopted (check `.specify/init-options.json` → `speckit_version`) or at minimum every
6 months, whichever comes first.

**Version**: 1.0.0 | **Ratified**: 2026-04-09 | **Last Amended**: 2026-04-09
