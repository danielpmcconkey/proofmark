# ATC POC3 Alignment — Proofmark

**Date:** 2026-03-01
**Audience:** Internal strategy team, future Claude sessions, CIO presentation prep
**Classification:** Internal Only — NOT for vendor distribution

This document maps Proofmark to the ATC POC3 program context. It contains everything
that was deliberately removed from the BRD to maintain vendor-facing COTS framing (per
decision S-1 in the BRD Revision Log). The BRD tells a vendor *what* to build.
This document tells *us* why we're building it and how it fits our program.

---

## 1. What Proofmark Proves

Proofmark exists to demonstrate three things for the CIO presentation (2026-03-24):

1. **The comparison architecture works.** Format-agnostic engine, pluggable readers,
   three-tier threshold model (STRICT/FUZZY/EXCLUDED), hash-sort-diff pipeline. It
   proves like-for-like output equivalence within the constraints inherent to specific
   output formats.

2. **The information isolation model is viable.** Builder agents cannot see or game the
   validator. Proofmark is presented to builder agents as a COTS product. They receive
   the BRD and nothing else. They don't know it was built over a weekend by a tech lead
   and an AI. They don't know the comparison algorithm. They build their rewrites blind
   to the validation mechanism. This is the "AI doesn't grade its own homework" story.

3. **The governance story holds up under scrutiny.** The evidence package format —
   comparison reports, column classification justifications, attestation disclaimers,
   exception approvals — survives adversarial review by CRO, risk partners, and
   independent evaluators.

---

## 2. The Production Path (Build vs. Buy)

**Recommendation to leadership:** Hire an independent systems integrator (Infosys,
Accenture, TCS, Cognizant, or equivalent) to build the production comparison tool.

This achieves:
- True organizational independence (different vendor, different team, different
  management chain)
- Satisfies regulatory segregation of duties requirements ("people," not just
  "AI instances")
- Removes the "one guy built it over a weekend" attack surface entirely
- Proofmark's BRD serves as the functional specification — "build this, but for real"

An alternative path: humans build it internally with heavy AI assistance, but under
a separate team's ownership with formal SDLC governance.

The final pitch will recommend "buy from vendor or commission vendor to build."

*(Decision T-13, BRD Revision Log)*

---

## 3. Platform Deployment Context

This section documents how Proofmark maps to our specific platform. None of this
belongs in the BRD, but it's critical context for deployment planning.

### 3.1 Our Output Landscape

| Format | Platform Pattern | Volume | Proofmark Reader |
|--------|-----------------|--------|-----------------|
| Delta Parquet | ADLS Delta Parquet part files via ADF/Databricks | ~20% | Parquet reader |
| Parquet (via DB-out) | Oracle, SQL Server, PostgreSQL outputs driven by ADF loading parquet | ~4% | Parquet reader (compare the parquet, not the DB) |
| Parquet (vanilla SFDC) | Vanilla Salesforce via standard ADF pipelines | <1% | Parquet reader |
| CSV | DataFrame-to-CSV dumps via TIBCO/ADF | ~76% | CSV reader |

**Key insight:** Database-out jobs and vanilla Salesforce resolve to parquet comparison.
The comparison target is the parquet file, not the downstream database or SFDC instance.
Custom SFDC ADF pipelines are application integration, not ETL — permanently out of scope.

### 3.2 Our Orchestration Complexity

Our OFW (orchestration framework) produces comparison targets through patterns that
don't map 1:1 to "jobs":

- A single OFW trigger can be one job with one output
- A "box job" producing many outputs in sequence
- A job with "date maker" logic that queues up sequential runs for missed days
- A job with sub-tasks that hand off between ADB and ADF
- A job registered in a federated ETL jobs table across multiple curated zones

This is why the BRD defines the unit of work as a "comparison target," not a "job."
The mapping from OFW triggers to comparison targets is the QA agent's problem (or the
human operator's). Proofmark doesn't know OFW exists.

### 3.3 The Portability Test

Originally called the "Accenture test." Renamed for the BRD because naming specific
vendors is not appropriate in a product spec.

The principle: if you couldn't sell this tool to another bank running Autosys instead of
OFW, Oozie instead of ADF, S3 instead of ADLS — you built it wrong. Proofmark must
have zero platform-specific knowledge baked in.

This isn't just good architecture. It's a governance defense. "The comparison tool has no
knowledge of our platform" is a stronger independence statement than "the comparison tool
was built by a different team."

### 3.4 Part File Demo Point

**Critical for the CIO presentation:** The same output spread across 3 part files must
compare correctly against the same output optimized into 1 part file. This demonstrates
that Proofmark handles Spark's partitioning behavior — a real-world scenario where the
rewrite coalesces partitions as an optimization.

### 3.5 File Output, Not Database

The real platform produces files. ADLS parquet files and CSV files through TIBCO/ADF
pipelines. PostgreSQL was a convenient stand-in for MockEtlFramework POC2. It's not
part of the comparison architecture. MockEtlFramework produces real file output (parquet
and CSV) for POC3 comparison.

---

## 4. Information Isolation Strategy

### The Model

Builder agents (the ones rewriting ETL jobs) receive Proofmark's BRD and nothing else.
From their perspective, Proofmark is a COTS product that some vendor built. They don't
know:

- That it was built by Claude over a weekend
- What algorithm it uses for comparison
- How its hashing works
- What tolerance it applies or doesn't apply
- Any internal details about the validation mechanism

This creates true information isolation. The builder cannot game the validator because
the builder doesn't know how the validator works. This is the same principle as an
independent auditor — they don't show you their checklist before the audit.

### Why This Matters for Governance

The CIO/CRO presentation needs to answer: "How do you prevent the AI from grading its
own homework?" The answer is architectural, not procedural:

1. The comparison tool is specified as a COTS product (BRD)
2. Builder agents receive only the BRD — no source code, no algorithm details
3. The comparison tool is built by a separate process (different Claude session,
   different context, different instructions)
4. Production recommendation: vendor-built by an independent SI

The information isolation model survives even if someone discovers the MVP was built
in-house, because the architecture was designed to be vendored out. The MVP proves
the architecture. The vendor build proves the independence.

---

## 5. Evidence Package Format

Proofmark produces a comparison report. That report is one *input* to a governance
evidence package. The evidence package is assembled by the QA process (human or agent),
not by Proofmark.

### What Goes in an Evidence Package

- Which OFW job(s) map to this comparison target
- Business context ("daily balance feed to downstream system X")
- Job owner / SME sign-off
- Proofmark comparison report(s) — linked, not embedded
- Exception approvals (why EXCLUDED columns were accepted, why FUZZY tolerances
  were set to their values)
- Attestation statement: "Output equivalence certifies equivalence to the original,
  NOT correctness in an absolute sense"

### Why Proofmark's Report Works as Evidence

The report is self-contained. Config echo, column classification with justifications,
full mismatch detail, pass/fail stamp. You can drop it into an evidence package and
it's interpretable without external context. This was a deliberate design choice.

### PII/PCI/SOX Implications

In production, mismatch detail with actual cell values is a PII/PCI/SOX problem.
The report itself becomes a classified artifact. The production version must:

- Strip values from mismatch detail — show row hash, column name, tier, match/fail,
  but no actual data
- Route detail to a secured location with restricted access
- Keep metadata, summary, classification, and stamp clean (unclassified)

The MVP includes full values because it runs on synthetic data and makes the exercise
faster. Nobody's looking at real PII.

---

## 6. Test Data Strategy

### The Problem

If MockEtlFramework produces both "original" and "rewritten" outputs using the same
libraries, floating point behavior, timestamp formatting, and rounding are identical on
both sides. FUZZY tolerance logic never gets exercised against real variance. The demo
would show a feature that was never stress-tested.

### The Solution

MockEtlFramework produces original and rewritten outputs using different libraries or
settings for specific jobs. This creates the kind of variance that actually shows up
during a real migration — where a 500-line PySpark job importing six random libraries
gets replaced with clean Spark SQL, and every library has opinions about rounding, null
coercion, date formatting, and encoding.

### POC Approach — Toggle Library Behavior Per Job

- **Job A:** `ROUND_HALF_UP` (original) vs. `ROUND_HALF_EVEN` / banker's rounding (rewrite)
- **Job B:** Timestamp precision difference (seconds vs. microseconds)
- **Job C:** Identical output on both sides (exact match happy path)

Three demo scenarios: tolerance pass (variance within threshold), tolerance fail
(variance exceeds threshold), and exact match. All realistic, all from one framework
toggling behavior.

### Why This Matters for the CIO Deck

"We tested tolerance comparison against actual library-level variance, not synthetic
data" is a much stronger statement than "we tweaked some numbers by hand." It mirrors
the real migration challenge — replacing bespoke external modules with standardized
Spark SQL and proving the outputs are equivalent within documented tolerances.

---

## 7. Cloud Migration Lessons Learned

These are the real-world experiences that informed Proofmark's design. They don't belong
in a vendor BRD, but they're the reason certain features exist.

### Hash-Sort Design

During cloud migration, the team needed to compare outputs without reliable sort keys.
They hashed the entire row and sorted by hash. No sort key config, no null sort edge
cases, no composite key debates. It worked. Proofmark's pipeline is directly descended
from that approach.

### Encoding and Line Breaks

At the start of cloud migration, encoding and line break mismatches were showstoppers.
By the end, the consensus was "fix your downstream ingestion process to be less brittle."
Proofmark needs to support both stances — that's why encoding is configurable and line
break mismatch is a fail flag that still runs the full comparison. Teams evolve their
stance over the course of a program.

### CSV Dialect

The prior QBV (Quick Byte Validator) tool whiffed on CSV dialect. It used Python's
standard CSV lib, which parsed correctly. But downstream systems had custom parsers that
behaved differently. The ETL framework's PySpark CSV writer had its own quirks.

This is a known landmine documented in the BRD (Section 14). The MVP uses standard
parsers. The production tool needs full dialect specification per target.

---

## 8. Out-of-Scope Platform Commentary

### Synapse

Supposed to mirror ADLS Delta 1:1. That rule has been broken approximately 100 times.
Ignored during cloud migration. Revisit after ADLS Delta comparison is battle-tested.

### Custom Salesforce

Custom SFDC ADF pipelines are application integration, not ETL. Permanently out of scope.
Program stakeholders should be informed that these workflows are out of scope due to
the overwhelming complexity of the custom integration logic.

### Database Validation

PostgreSQL, Oracle, SQL Server, Synapse — all implementable but significant setup work.
DB-out jobs write parquet first anyway; the comparison target is the parquet file.
No value-add to the CIO presentation. Revisit for production pilot.

### Exotic Formats

XML, JSON, EBCDIC, zipped/binary outputs — approximately 4% of the total job estate.
The architecture supports them via pluggable readers. Not implemented for MVP. Revisit
after CSV and parquet readers are solid.

---

## 9. CIO Presentation Narrative Arc

*(To be developed closer to March 24th)*

Key beats:
1. The problem: 1,200+ ETL jobs need to be migrated/rewritten
2. The AI can do the rewriting (POC2 proved this — 32 jobs, 100% equivalence)
3. But who validates the AI's work? The AI can't grade its own homework.
4. Enter Proofmark: independent, vendor-specifiable comparison tool
5. Information isolation: builder agents don't know how validation works
6. Evidence package: governance artifacts that survive CRO scrutiny
7. Recommendation: commission vendor to build production version

---

## 10. Relationship to Other ATC Documents

| Document | Purpose | Lives In |
|----------|---------|----------|
| **BRD (v3, approved)** | What to build. Vendor-handoff-ready product spec. | `BusinessRequirements/BRD-v3-approved.md` |
| **This document** | Why we're building it and how it fits our program. | `AtcDocumentation/poc3-alignment.md` |
| **Scope and Intent** | What Proofmark IS and IS NOT. The production path. | `AtcDocumentation/scope-and-intent.md` |
| **BRD v3 Provenance** | How the BRD was produced, authorship model, skeptic rebuttals. | `AtcDocumentation/brd-v3-provenance.md` |
| **Test Architecture** | BDD scenarios for the MVP build. | `Documentation/test-architecture.md` |
| **TAR Register** | Adversarial review — every concern the CIO/CRO might raise. | `ai-dev-playbook/Projects/ATC/adversarial-review/06-program-tar-register.md` |
| **Design Sessions** | Raw decision logs from Dan + Claude design conversations. | `BusinessRequirements/SupportingDocumentation/design-sessions/` |
| **BRD Revision Log** | Every decision from the BRD review cycle. | `BusinessRequirements/SupportingDocumentation/brd-revision-log.md` |

---

## Content Provenance

This document incorporates content removed from BRD v1 per structural decision S-1
(split BRD into vendor-facing spec + internal alignment doc). The 20 content items
listed in BRD v3's "Content Moved" appendix are accounted for here:

| BRD v3 Moved Item | Alignment Doc Section |
|---|---|
| 1. "What Proofmark Proves" block | Section 1 |
| 2. "Not the production tool" paragraph | Section 2 |
| 3. In Scope platform-specific commentary | Section 3.1 |
| 4. Out of Scope platform-specific rationale | Section 8 |
| 5. Platform-specific orchestration examples | Section 3.2 |
| 6. "Accenture test" naming context | Section 3.3 |
| 7. "The real platform" references | Section 3.5 |
| 8. "Critical POC demo point" callout | Section 3.4 |
| 9. "During cloud migration" hash-sort context | Section 7 |
| 10. "During cloud migration" encoding context | Section 7 |
| 11. Encoding strict/normalize options | Section 7 |
| 12. Production Constraint PII/PCI block | Section 5 |
| 13. Evidence Package full section | Section 5 |
| 14. Test Data Strategy full section | Section 6 |
| 15. Custom Salesforce "tell the CIO" language | Section 8 |
| 16. Platform-specific out-of-scope commentary | Section 8 |
| 17. "AI agent rewrites" references | Section 4 |
| 18. Named internal platform references | Sections 3.1, 3.2, 8 |
| 19. Build-vs-buy rationale (T-13) | Section 2 |
| 20. COTS/information-isolation glossary context | Section 4 |
