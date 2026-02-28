# Proofmark — Scope and Intent

## What Proofmark IS

Proofmark is a **proof-of-concept stand-in** for an independently built output comparison and validation tool. It exists to demonstrate that:

1. The comparison architecture works (format-agnostic engine, pluggable readers, three-tier threshold model)
2. The information isolation model is viable (builder agents can't see or game the validator)
3. The governance story holds up under scrutiny

## What Proofmark IS NOT

Proofmark is **not** the production tool. It is not intended to pass through the Phase 1 prototype control gate as-is.

## The Production Path

Dan's recommendation to leadership: **hire an independent systems integrator (Infosys, Accenture, or equivalent) to build the production comparison tool.** This achieves:

- True organizational independence (different vendor, different team, different management chain)
- Satisfies regulatory segregation of duties requirements ("people," not just "AI instances")
- Removes the "one guy built it over a weekend" attack surface entirely
- Proofmark serves as the functional specification — "build this, but for real"

An alternative path: humans build it internally with heavy AI assistance, but under a separate team's ownership with formal SDLC governance.

## Why Build Proofmark At All?

Because you can't demo a concept with a PowerPoint slide. The POC needs a working comparison tool to:

- Run the expanded MockEtlFramework (50 jobs, multiple output types, planted gotchas)
- Produce real comparison reports that demonstrate the evidence package format
- Show the CIO/CRO/board what "the AI doesn't grade its own homework" looks like in practice
- Prove the architecture before spending seven figures on a vendor build

## Decision Date

2026-02-27. Documented during adversarial evaluation exercise.
