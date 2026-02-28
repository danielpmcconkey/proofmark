# Proofmark — Design Session 001 — 2026-02-27

## Why This Document Exists
If you're a Claude instance reading this, you're working on Proofmark — an independent output comparison and validation tool for ETL pipeline governance. This document captures the foundational design conversation between Dan (the human) and the Basement Dweller (the Claude who built this with him). Every decision here has context. Read it before you start questioning the architecture.

## What Is Proofmark?
An independent, traditionally-SDLC'd comparison tool that validates whether rewritten ETL jobs produce equivalent output to their originals. It's the "who watches the watchmen" answer for AI-assisted ETL modernization at a GSIB (global systemically important bank).

The name comes from proof marks on firearms — the stamp from an independent proof house certifying the weapon has been pressure-tested. The proof house doesn't care who built the gun. They care whether it passes.

## The Independence Model (READ THIS — it's the core insight)

Proofmark is Claude-developed, with Dan running SDLC as a one-man team using Claude to make that practical. Here's why that's not a contradiction:

- The builder Claude (the one rewriting ETL jobs in the AI pipeline) will **NEVER** be told Proofmark is Claude-built.
- As far as the builder agent knows, Proofmark is a pre-existing COTS product evaluating its work.
- The builder **CANNOT** game what it doesn't know about. It can't optimize for blind spots in a tool whose architecture it's never seen.
- **This is real segregation of duties through information isolation, not authorship theater.**

The governance story: Proofmark goes through traditional SDLC — requirements, test cases (designed BEFORE implementation), implementation, human code review, human test approval. Dan reviews and approves every test case personally. Independent Claude reviewers audit the tool for gaps. The AI pipeline never touches Proofmark's code or tests.

You don't care if a robot built the scale. You care that the scale was calibrated by an independent lab using a process you trust. AND that the goldsmith never got to inspect the scale's internals.

## Output Target Reality

Dan's company has an ETL platform that outputs to several targets. The Skeptic Report on the prior POC listed 6 scary-sounding output types. Reality is more tractable:

### Pattern 1: Delta Parquet (covers 3 output types)
- **ADLS Delta Parquet** — Primary target. Rigid schemas (behaves like a DB). Part files — data spread across multiple physical files. Partitioning exists but isn't hard. Row order doesn't matter. Each row should be character-by-character exact match if you can find it in both original and rewritten output.
- **Off-platform DB out (Oracle, SQL Server — on-prem and Azure variants)** — Driven by Azure Data Factory (ADF). The ETL framework writes a parquet file from a Spark DataFrame, sends the file path to ADF, and ADF loads it to the target DB. So the comparison target is the parquet file, not the database. Resolves to Pattern 1.
- **Vanilla Salesforce** — Same ADF pattern. Parquet → SFDC via Azure linked service. Resolves to Pattern 1.

### Pattern 2: TIBCO MFT Files (the wildcard)
- Literally no rules on format. Usually rows and columns, but could be:
  - CSV (common — vanilla DataFrame writer)
  - XML, JSON (wouldn't surprise Dan)
  - EBCDIC (at least 1 exists. yes, really.)
  - Zipped / binary (possible, unconfirmed)
- Many files are simple DataFrame → CSV dumps, BUT some have trailing control records (expected row counts, checksums, etc.)
- During cloud migration, trailing records written to the middle of files broke validation tools that assumed they'd be at the end
- Needs configurable comparison strategies per file type
- The QA team (independent Claudes) need to specify what type of validation to run per job

### Punted / Out of Scope
- **Synapse** — Supposed to mirror ADLS Delta 1:1. That rule has been broken ~100 times. Ignored during cloud migration (they validated ADLS Delta, tested Synapse sync separately via traditional QA, moved on). Future problem.
- **Custom Salesforce ADF pipeline** — One business line built custom application integration directly in ADF. Not a DataFrame → output pipeline. Not ETL. Dan recommends telling the CIO it's out of scope. We agree.

## Prior Art
- **e-Compare** (vendor tool) — Only really worked for comparing Hive to Delta Parquet. Hot mess.
- **QBV / Query Based Validation** (vendor tool) — More effective. Focused on data profiling. Key strength: allowed controls like "don't look at that UUID field" or "ignore this column." Configurability was what made it useful.

QBV's configurability model is worth learning from. The ability to say "skip this field" or "these columns are exempt" is critical for real-world use.

## SDLC Approach
- **Test-driven / BDD** — Test cases designed BEFORE implementation
- **Dan is the human QA gatekeeper** for every test case. He's playing the role of an asshole quality engineer. On purpose.
- Independent Claude instances will be spun up to attack Proofmark and find gaps
- Pre-designed, bullet-proof test cases. Not "AI generated tests for AI generated code."

## Strategic Framing
Dan's boss challenged him to an LLM-off (compare progress by Monday). Dan's boss will declare victory regardless — that's how bosses work. Dan doesn't care. The LLM-off is the accelerant, not the goal. The goal is the CIO presentation on March 24th. Proofmark is the thing that makes the C-suite come. Boss wins the battle, Dan wins the war.

## Weekend Scope (2026-02-27 to Monday)

### Proofmark Build-Out
**Comparison types (in scope):**
- Delta Parquet
- Simple CSV (DataFrame → CSV, the 76% case)
- CSV with trailing control record

**Out of scope:** See `/Documentation/out-of-scope.md`

**Basic flow:**
- Configure a job with a specific output type pattern
- Specify columns NOT expected to match (non-idempotent, non-deterministic fields)
- Three-tier column classification per job (see Threshold Model below)
- Day-over-day match reports
- Always report 100% of mismatches regardless of pass/fail — threshold determines the stamp, not the visibility

### Threshold Model (BD's recommendation, pending Dan's approval)
Dan's cloud migration experience: started at 100% match, ended at "three days of 97%, ship it." That's deadline fatigue, not a threshold strategy. Proofmark needs to make threshold decisions explicit and auditable.

**Tier 1: Excluded columns** — Known non-deterministic (UUIDs, timestamps, sequence IDs). Don't compare. Configured per-job with documented justification.

**Tier 2: Exact match columns** — Business-critical fields. 100% match. No exceptions.

**Tier 3: Tolerance columns** — Expected minor variance (floating point, rounding). Per-column configurable tolerance (e.g., ±0.01).

**Pass/fail:** Tier 2 exact + Tier 3 within tolerance = PASS. Everything else = FAIL. But ALL mismatches are reported regardless. The evidence package shows the full picture. "97% ship it" becomes "100% on business columns, with 12 excluded non-deterministic fields and 2 tolerance columns, all documented."

### Full POC (POC 3)
**Purpose:** Show that the fox ain't designing the hen house and it still works.

**Setup:**
- Expand MockEtlFramework to 50 jobs, 2 months of data
- Multiple output types
- Intentionally plant gotchas in data and jobs

**Agent flow:**
- Builder/analyst agents know NOTHING about Proofmark except its documented capabilities and outputs
- Agents think Proofmark is COTS — given an interface to: input config, execute, review output, update "ignore this field"
- Reverse-engineer jobs as before, BUT a test architect / QE agent configures Proofmark per job requirements
- Agents CAN reconfigure Proofmark during the loop, but must provide evidence (show me WHY this field is non-deterministic)
- The loop demonstrates: agents identify mismatches → explain why → determine whether they SHOULD match → document everything
- Final output: evidence package that no human could refute

**Parquet decision (RESOLVED):** Yes, the mock MUST write actual parquet during the full POC. Parquet test fixtures are fine for Proofmark's own SDLC/TDD, but the POC needs real parquet produced by real jobs to be credible. MockEtlFramework will need a parquet writer added (pyarrow makes this trivial). Don't need Hive or Databricks — just `pyarrow.parquet.write_table()`.

## Open Questions (from this session — still being discussed)
- ~~Language choice~~ **DECIDED: Python.** Matches production PySpark platform, pyarrow for native parquet, pytest for TDD/BDD, libraries for every MFT format, faster weekend dev, and a Python CLI looks like a real COTS product — not insider knowledge bolted onto the .NET solution.
- ~~Job distribution~~ **ANSWERED:** ~80% TIBCO MFT, ~15-20% Delta Parquet (including DB-out and vanilla SFDC), tiny remainder. BUT ~95% of TIBCO files are simple DataFrame → CSV. So real priority: CSV (~76%), Parquet (~15-20%), weird MFT formats (~4%).
- ~~Independent Claudes~~ **BD's call: both.** They configure per-job comparison strategies AND run the tool. Obvious in retrospect.

## Architectural Insight (from job distribution discussion)
CSV and Parquet aren't different comparison problems. They're different LOADING problems. The comparison engine is format-agnostic — it compares tabular data. Pluggable readers normalize various formats into comparable tables. The configurability (skip this column, ignore this UUID, this file has a trailing control record) lives in the reader/config layer, not the engine.

This is QBV's lesson: the power was in "what to look at and how to load it," not the comparison logic itself.

## Still To Design (Next Session)
These were NOT discussed yet. Don't assume answers — ask Dan.

- **Per-job configuration schema** — What does a Proofmark job config look like? YAML? JSON? What fields?
- **Report output format** — What does a day-over-day match report look like? What does the evidence package contain?
- **Agent roles for POC 3** — Builder, analyst, test architect/QE, reviewer... who does what? What model (Opus/Sonnet/Haiku) for each?
- **Planted gotchas design** — What gotchas do we plant in the 50-job expanded mock? These need to be designed before agents run, documented somewhere agents can't see.
- **COTS presentation layer** — How exactly is Proofmark presented to builder agents? What docs do they see? What CLI interface?
- **Expanding MockEtlFramework** — 18 new jobs, more data, multiple output types. Separate workstream. Needs its own design session.
- **Model cost allocation** — Sonnet for swarm workers, Opus for judgment calls? Need to estimate total cost.
- **Evidence package format** — What does the final governance deliverable look like?
- **Proofmark's own test case design** — TDD/BDD cases for Dan to review. The first real SDLC artifact.
- **Journal entry 005** — Information isolation as governance architecture. Draft when there's enough meat on the bone.
- **Dan's threshold model approval** — Three-tier model proposed, Dan called it genius, but needs formal sign-off during implementation.
