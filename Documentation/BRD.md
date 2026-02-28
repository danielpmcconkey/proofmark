# Proofmark — Business Requirements Document

**Version:** 1.0
**Date:** 2026-02-28
**Status:** Draft
**Classification:** Internal — Working Document

---

## 1. Executive Summary

Proofmark is a proof-of-concept output comparison and validation tool for ETL pipeline governance. It exists to answer a single question: when an AI agent rewrites an ETL job, does the rewritten job produce equivalent output to the original?

Proofmark is **not** the production tool. It is a functional specification and architectural proof of concept. The production comparison tool will be built by an independent systems integrator (Infosys, Accenture, or equivalent), using Proofmark as the spec. This achieves true organizational independence — different vendor, different team, different management chain — and eliminates the "one person built the whole thing" governance risk.

The name comes from proof marks on firearms: the stamp from an independent proof house certifying that a weapon has been pressure-tested. The proof house doesn't care who built the gun. It cares whether it passes.

### What Proofmark Proves

1. **The comparison architecture works.** Format-agnostic engine, pluggable readers, three-tier threshold model, hash-sort-diff pipeline.
2. **The information isolation model is viable.** Builder agents never see Proofmark's internals, architecture, or authorship. As far as they know, it is a pre-existing COTS product evaluating their work.
3. **The governance story holds up under scrutiny.** Deterministic comparison that mathematically cannot be gamed, producing self-contained evidence reports suitable for regulatory review.

### Attestation Disclaimer

**Output equivalence certifies equivalence to the original, NOT correctness in an absolute sense.** If the original job contains a bug that produces incorrect output, and the rewrite faithfully reproduces that bug, Proofmark will report PASS. Proofmark certifies that two outputs match. It does not validate business logic correctness. This distinction must appear in every evidence package that includes a Proofmark report.

---

## 2. Scope

### In Scope (POC)

- **Delta Parquet comparison** — ADLS Delta Parquet part files. This pattern also covers off-platform database outputs (Oracle, SQL Server) and vanilla Salesforce, because those targets are driven by ADF loading a parquet file. The comparison target is the parquet file, not the downstream database or SFDC instance.
- **CSV comparison** — Simple DataFrame-to-CSV dumps (approximately 76% of production output by volume) and CSV files with trailing control records (header rows, trailer rows with checksums or row counts).
- **Three-tier column classification** — Per-target configuration of excluded, exact match, and tolerance columns.
- **Hash-sort-diff pipeline** — Order-independent comparison via row hashing, sorting by hash, and sequential diff.
- **JSON comparison reports** — One report per comparison target, machine-parseable and human-readable.
- **YAML configuration** — Per-target configuration with default-strict philosophy and justification requirements.
- **CLI interface** — Single command, stdout output, exit codes for scripting.

### Out of Scope (POC)

- **Database validation** — PostgreSQL, Oracle, SQL Server, Synapse. Trivial to implement but significant setup work. No value-add to the CIO presentation. DB-out jobs write parquet first anyway; the comparison target is the parquet file. *(Revisit for production pilot.)*
- **Synapse validation** — Supposed to mirror ADLS Delta 1:1. That rule has been broken approximately 100 times. Ignored during cloud migration. *(Revisit after ADLS Delta comparison is battle-tested.)*
- **Salesforce** — Vanilla SFDC resolves to parquet comparison. Custom SFDC ADF pipelines are application integration, not ETL. Custom SFDC is permanently out of scope.
- **Exotic MFT formats** — XML, JSON, EBCDIC, zipped/binary outputs. Approximately 4% of the total job estate. The architecture supports them via pluggable readers, but they are not implemented for the POC. *(Revisit after CSV and parquet readers are solid.)*
- **Evidence package assembly** — Proofmark produces a comparison report. Assembly of that report into a governance evidence package is a QA process concern, not a tool concern (see Section 12).
- **Batch mode / orchestration** — Running multiple comparison targets in sequence or parallel is orchestration. Proofmark compares one target at a time.
- **PII/PCI stripping from reports** — Production requirement. The POC runs on synthetic data (see Section 16).

### POC vs. Production Distinction

| Capability | POC (Proofmark) | Production (Vendor Build) |
|---|---|---|
| Comparison engine | Working | Same architecture, enterprise-grade |
| Readers | Parquet, CSV | Parquet, CSV, exotic formats as needed |
| Hash algorithm | MD5 (hardcoded) | Configurable (MD5, SHA256, etc.) |
| CSV dialect handling | Standard parser, same config both sides | Full dialect specification per target |
| Report detail | Full cell values in mismatch output | PII-stripped; values in secured location |
| Verbosity | Single mode | Verbose/quiet/normal flags |
| Output destination | Stdout default, optional file | File default with structured output directory |
| Batch execution | Not supported | Orchestration layer handles batching |

---

## 3. Core Concepts

### 3.1 Comparison Target

The unit of work in Proofmark is a **comparison target**, not a "job."

In the real platform, an OFW trigger can be a single job with one output, a box job producing many outputs in sequence, a job with date-maker logic queuing sequential runs, a job with sub-tasks handing off between ADB and ADF, or a job registered in a federated ETL jobs table across multiple curated zones. There is no clean 1:1 mapping between "OFW job" and "thing to compare."

Proofmark does not know what a job is. A comparison target is:

- A pair of data sources (original output + rewritten output)
- A column configuration (tier 1/2/3 classification)
- A reader type and reader-specific configuration

The mapping from "OFW job" to "comparison targets" is the responsibility of whoever configures Proofmark — the QA agent or human operator. One job might produce five comparison targets. A chain of jobs might result in one comparison target at the end. Proofmark does not care.

**The Accenture test:** If you couldn't sell this tool to another bank running a completely different orchestration framework, you built it wrong. Proofmark knows about files and tabular data. It does NOT know about OFW, ADF, Databricks, Autosys, Oozie, box jobs, date maker, curated zone federation, or any platform-specific concept.

*(Decision 1, Design Session 002)*

### 3.2 No Relationships Between Targets

Proofmark does not model dependencies between comparison targets. It does not know that "target C is the final output of a chain that includes intermediary targets A and B." Grouping targets into validation runs, linking them to jobs, or mapping dependency chains is external context managed by the agent workflow or human process.

Proofmark compares individual targets and produces individual reports.

*(Decision 2, Design Session 002)*

### 3.3 File vs. File Comparison

The real platform produces files — parquet files in ADLS and CSV files through TIBCO/ADF. Proofmark compares files to files. There is no database in the comparison loop.

- Original job produces a file (parquet or CSV)
- Rewritten job produces a file (parquet or CSV)
- Proofmark reads both files, compares, reports

*(Decision 3, Design Session 002)*

### 3.4 Two Readers

Session 001 identified three comparison types: parquet, simple CSV, and CSV with trailing control record. Simple CSV and CSV-with-trailer are the same reader with different configuration. Proofmark has two readers.

**Parquet reader:**
- Input: directory path containing part files
- Reads all `*.parquet` files in the directory
- Assembles into one logical table

**CSV reader:**
- Input: file path
- Configuration: number of header rows to skip (compared as literal strings, in order), number of trailer rows to skip (compared as literal strings, in order)
- Everything between header and trailer is data and goes through the hash-sort-diff pipeline
- Header and trailer rows are compared as exact literal string matches, in order

"Simple CSV" is the CSV reader with `header_rows: 1` (or 0) and `trailer_rows: 0`. Same reader, different config.

*(Decision 6, Design Session 002)*

### 3.5 Parquet Part Files: Directory-Level Comparison

Delta Parquet outputs are spread across multiple part files. The number of part files is a Spark implementation detail (number of partitions). A rewritten job may coalesce into fewer parts as an optimization. The data is identical; the physical layout is different.

The parquet reader reads all part files in a directory, assembles them into one logical table, and proceeds to comparison. Row ordering across parts is meaningless. Comparison is order-independent.

**Critical POC demo point:** The same output spread across 3 part files must compare correctly against the same output optimized into 1 part file.

*(Decision 4, Design Session 002)*

---

## 4. Comparison Pipeline

The pipeline executes in the following order for each comparison target:

### Step 1: Load

Read both sources using the configured reader. For parquet, this means reading a directory of part files and assembling into one logical table. For CSV, this means reading the file, separating header/trailer rows from data rows per configuration.

### Step 2: Exclude

Drop all tier 1 (excluded) columns. These columns do not exist from this point forward. They are not hashed, not compared, not present in downstream steps.

**Why exclusion happens before hashing:** If a tier 1 column (e.g., a UUID) differs between original and rewrite, hashing it would produce completely different hash values, which would produce completely different sort orders, which would make sequential comparison impossible. Exclude first, hash what remains.

### Step 3: Hash

Hash each remaining row (all non-excluded columns) to produce a single hash value per row. The hash captures the complete content of tier 2 and tier 3 columns for that row.

### Step 4: Sort

Sort both datasets by hash value. This produces deterministic ordering regardless of physical file layout, original row order, or part file distribution. No sort key configuration required.

**Why hash-sort instead of sort keys:** The real platform does not have reliable sort keys. During cloud migration, the team hashed entire rows and sorted by hash. This eliminates sort key configuration, null sort edge cases, and composite key debates.

### Step 5: Diff

Walk both hash-sorted datasets row by row:

- **Tier 2 columns:** Exact match. Any difference is a mismatch.
- **Tier 3 columns:** Within configured tolerance (see Section 7). Any difference exceeding tolerance is a mismatch.

**Duplicate row handling:** This is multiset comparison, not set comparison. If the original has 2 identical rows (after tier 1 exclusion), the rewrite must also have exactly 2. Row counts matter.

### Step 6: Report

All mismatches are reported regardless of pass/fail. The threshold determines the stamp, not the visibility. A comparison target that passes at 99.5% still shows every mismatch in the report.

*(Decision 5, Design Session 002)*

---

## 5. Column Classification

Proofmark uses a three-tier column classification model. Every column in a comparison target belongs to exactly one tier.

### Tier 1: Excluded

Known non-deterministic columns — UUIDs, timestamps, sequence IDs, runtime-assigned identifiers. These columns are dropped before hashing and are not compared.

**Requirement:** Every tier 1 exclusion must include a documented justification in the configuration. The justification flows into the comparison report and the evidence package. "We excluded it because it didn't match" is not a justification.

### Tier 2: Exact Match

Business-critical fields. Byte-level exact match required. No tolerance, no normalization (except where encoding/line break strictness is explicitly relaxed per Section 8).

**This is the default.** Any column not explicitly classified as tier 1 or tier 3 is tier 2.

### Tier 3: Tolerance

Columns with expected minor variance — floating point rounding, precision differences between computation engines. Per-column configurable tolerance with both absolute and relative modes (see Section 7).

**Requirement:** Every tier 3 classification must include a documented justification and an explicit tolerance value and type. "Floating point is weird" is not a justification. "Rounding variance between Spark and ADF engines, tolerance +-0.01 absolute" is.

### Default-Strict Philosophy

If no column configuration is provided for a comparison target, every column is tier 2 (exact match). This is the strictest possible default.

The QA agent's or operator's job is to carve out exceptions and justify each one. The burden of proof is on relaxing the standard, not on tightening it. The evidence package shows: "We compared 47 columns exactly and excluded 3, here's why for each."

*(Decision 7, Design Session 002)*

---

## 6. Configuration

### Format: YAML

YAML supports inline comments (natural place for justifications), is less noisy than JSON, is human-editable, and has native Python support. QA agents can generate YAML programmatically as easily as JSON.

### Schema

```yaml
comparison_target: daily_balance_feed    # Human-readable name
reader: csv                              # "csv" or "parquet"
source_a: /data/original/daily_balance.csv
source_b: /data/rewrite/daily_balance.csv

# Reader-specific config (omit section if not applicable)
csv:
  header_rows: 1      # Rows to skip before data (compared as literal strings)
  trailer_rows: 1      # Rows to skip after data (compared as literal strings)

# Strictness settings (both default to "strict")
encoding: strict       # "strict" or "normalize"
line_breaks: strict    # "strict" or "normalize"

# Pass/fail threshold (default 100.0)
threshold: 100.0

# Column classification
# Everything NOT listed here defaults to tier 2 (exact match)
columns:
  tier_1:  # Excluded before hashing — requires justification
    - name: run_id
      reason: Non-deterministic UUID assigned at runtime
    - name: load_timestamp
      reason: Execution timestamp, varies per run

  tier_3:  # Tolerance match — requires justification and tolerance value
    - name: interest_accrued
      tolerance: 0.01
      tolerance_type: absolute
      reason: Floating point rounding between Spark and ADF engines
    - name: market_value
      tolerance: 0.001
      tolerance_type: relative
      reason: Rounding variance scales with value magnitude
```

### Design Notes

- Parquet configs omit the `csv` section entirely. The parquet reader only needs directory paths (`source_a`, `source_b`).
- If `encoding`, `line_breaks`, `threshold`, or `columns` are omitted, the strictest possible defaults apply. Relaxation requires explicit configuration plus justification.
- The `reason` field on tier 1 and tier 3 columns flows into the report's column classification section. It is the audit trail.
- There is no `tier_2` list. Everything unlisted is tier 2 by default. Listing tier 2 columns would be redundant noise.
- The configuration file is the single source of truth. No CLI flags override config values.

*(Decision 11, Design Session 002)*

---

## 7. Tolerance Specification

Tier 3 columns support two tolerance modes, configurable per column. There are no hardwired defaults on tolerance type — the person configuring it makes a conscious choice and justifies it.

### Absolute Tolerance

Match condition: `|a - b| <= tolerance`

Use when the acceptable variance is a fixed value regardless of magnitude (e.g., rounding to the nearest cent).

### Relative Tolerance

Match condition: `|a - b| / max(|a|, |b|) <= tolerance`

Division uses the larger absolute value. Use when acceptable variance scales with value magnitude (e.g., large dollar amounts where a fixed tolerance is too tight or too loose).

### Edge Cases

- **Both values are 0:** Match. Zero delta.
- **One value is 0, other is not:** Math works naturally. `|0 - 0.0001| / max(0, 0.0001) = 1.0` — 100% relative difference, fails any reasonable tolerance. No special case needed.

### Requirements

- `tolerance_type` is **required** on every tier 3 column. There is no default. This forces an explicit, justified choice.
- `tolerance` (the numeric value) is required on every tier 3 column.
- There is no "percentage" type. Relative tolerance with `tolerance: 0.01` *is* 1%. A third label for the same math creates confusion for zero value-add.

*(Decision 14, Design Session 002)*

---

## 8. Null Handling

### Parquet

Non-issue. Parquet has a typed schema with native null support. Null is null — not empty string, not the literal text `"NULL"`. The format enforces this. Two nulls match. Null vs. empty string is a mismatch, correctly, because the schema says they are different things.

### CSV

The wild west of null representation:

- Empty field: `,,`
- Empty quoted string: `,"",`
- Literal text: `NULL`, `null`, `\N`, `NA`, `N/A`, `NaN`
- Whitespace: `, ,`

Every upstream system has its own opinion. If the original wrote `NULL` and the rewrite writes an empty field, that is a **legitimate mismatch**. Downstream systems with brittle parsers treat these differently. Real consequences.

### The Rule

**Byte-level comparison. No null normalization.** `NULL` is not equal to an empty field, is not equal to `""`, is not equal to `null`. If the bytes are different, it is a mismatch. This is consistent with the default-strict philosophy throughout the system.

The *rewrite process* is responsible for matching the original's null representation. If Proofmark flags a null mismatch, the fix is in the rewrite — cast your nulls to match the expected format. The comparison tool does not paper over differences.

### Null Handling in Hashing

No special treatment. Nulls (however represented) are bytes in the row. They hash like everything else.

*(Decision 17, Design Session 002)*

---

## 9. Line Break and Encoding Strictness

### The Real-World Context

During cloud migration, encoding and line break mismatches were showstoppers at the start. By the end, the consensus was "fix your downstream ingestion process to be less brittle." Proofmark needs to support both stances.

### Configuration

Per comparison target:

- **Line breaks:** `strict` (CRLF and LF must match exactly) or `normalize` (treat all line break styles as equivalent)
- **Encoding:** `strict` (byte-level must match) or `normalize` (decode both to a common encoding, compare characters)

### Defaults

Both default to `strict`. Relaxation requires documented justification. Early in the program, everything is strict. Later, configs relax as teams document why.

The evidence package reflects the setting: "compared with strict encoding" or "normalized line endings per approved exception [reference]."

*(Decision 8, Design Session 002)*

---

## 10. Hash Algorithm

**POC:** MD5. It is fast, universally available, and produces excellent distribution for row comparison and sorting. Collision risk is irrelevant — this is a comparison hash, not a security function. Nobody is crafting adversarial ETL outputs.

**Optics management:** The algorithm name is not surfaced in report output. Reports show row hashes for mismatch identification. The algorithm that produced them is an implementation detail. If asked: "It's a comparison hash, not a security function."

**Production:** The hash algorithm should be configurable. The vendor can offer SHA256 if it makes compliance happy. It is slower for zero benefit in this use case, but the architecture does not care — hash is hash, swap the function, pipeline works the same.

*(Decision 16, Design Session 002)*

---

## 11. Report Output

### Format

JSON. One report per comparison target. JSON serves two audiences: the QA agent (machine consumer needing structured data to parse pass/fail) and the human reviewer (needing a readable summary for governance). Machine-parseable and human-readable enough for a POC.

### Report Contents

**Metadata:**
- Timestamp
- Proofmark version
- Comparison target name
- Config file path

**Config echo:**
- Full configuration used for this comparison, embedded in the report so it is self-contained

**Column classification:**
- Which columns are tier 1, tier 2, tier 3
- Justifications echoed from configuration

**Summary:**
- Row counts (source A, source B)
- Match count
- Mismatch count
- Match percentage
- Pass/fail stamp
- Threshold used

**Mismatches:**
- Every mismatch, regardless of pass/fail: row hash, column name, value A, value B, tier
- For tier 3 mismatches: tolerance, tolerance type, and actual delta

### What Is Not in the Report

- **Matched rows.** Nobody needs 10 million "yep, same" entries. Row counts and match percentage cover it.
- **Platform-specific context.** Job names, OFW IDs, orchestration metadata — not Proofmark's domain.

### Pass/Fail Logic

- Threshold is in the configuration (e.g., 99.5% match required).
- Default threshold: 100.0% (consistent with default-strict philosophy).
- The report always shows ALL mismatches regardless of pass/fail.
- Pass = match percentage >= threshold with all tier 2 columns exact and all tier 3 columns within tolerance.
- Fail = anything else.

### Production Constraint (Documented, Not Solved)

In production, mismatch detail containing actual cell values is a PII/PCI/SOX problem. The report itself becomes a classified artifact. The production version must strip values from mismatch detail — showing row hash, column name, tier, match/fail, but no actual data. Detail values go to a secured location with restricted access. The rest of the report (metadata, summary, classification, stamp) remains clean.

This is vendor-build territory. The POC includes full values because it runs on synthetic data.

*(Decision 10, Design Session 002)*

---

## 12. CLI Interface

### Invocation

```bash
proofmark compare --config path/to/target.yaml
```

One config, one comparison, one report. The config file is the single source of truth.

### Output

JSON report to stdout by default. `--output path/to/report.json` to write to file.

Stdout is ideal for agent workflows — pipe it, parse it, move on. File output is for evidence packaging.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Comparison ran, PASS |
| `1` | Comparison ran, FAIL |
| `2` | Error (bad config, file not found, parse failure) |

Exit codes allow the QA agent to script pass/fail decisions without parsing the report.

### What It Does Not Have (By Design)

- **No verbosity flags.** The POC runs one way. Verbose/quiet/normal is a vendor NFR.
- **No batch mode.** Running multiple configs is orchestration, not Proofmark's concern.
- **No dry-run.** Nothing useful to validate without actually running the comparison.
- **No CLI flags to override config values.** The config file is authoritative.

*(Decision 12, Design Session 002)*

---

## 13. Evidence Package

Proofmark produces a comparison report. That report is one *input* to a governance evidence package. Assembly of the evidence package is a QA process concern — human or agent — not a tool concern.

### Evidence Package Contents (External to Proofmark)

An evidence package includes things Proofmark has no business knowing about:

- Which OFW job(s) map to this comparison target
- Business context ("daily balance feed to downstream system X")
- Job owner / SME sign-off
- Proofmark comparison report(s) — linked, not embedded
- Exception approvals (why tier 1 exclusions were accepted)
- Attestation statement: "Output equivalence certifies equivalence to original, NOT correctness in an absolute sense"

### Why Proofmark's Report Works as Evidence

The report is self-contained. It includes the full configuration echo, column classification with justifications, complete mismatch detail, and a pass/fail stamp. It can be dropped into an evidence package and interpreted without external context.

### POC Approach

Define what an evidence package looks like conceptually (markdown template or directory structure), but do not build assembly tooling. Proofmark outputs JSON. Packaging is manual for the demo.

*(Decision 13, Design Session 002)*

---

## 14. Test Data Strategy

### The Problem

If the MockEtlFramework produces both "original" and "rewritten" outputs using the same libraries, floating point behavior, timestamp formatting, and rounding are identical on both sides. Tier 3 tolerance logic never gets exercised against real variance. The demo would show a feature that was never actually stress-tested.

### The Decision

MockEtlFramework must produce original and rewritten outputs using **different libraries or settings** for specific jobs. This creates the kind of variance that actually shows up during a real migration — where a 500-line PySpark job importing six random libraries gets replaced with clean Spark SQL, and every library has opinions about rounding, null coercion, date formatting, and encoding.

### POC Approach: Toggle Library Behavior Per Job

- **Job A:** `ROUND_HALF_UP` (original) vs. `ROUND_HALF_EVEN` / banker's rounding (rewrite) — exercises tier 3 tolerance comparison
- **Job B:** Timestamp precision difference (seconds vs. microseconds) — exercises tier 1 exclusion or strict mismatch detection
- **Job C:** Identical output on both sides — exact match happy path

This produces three demo scenarios: tolerance pass (variance within threshold), tolerance fail (variance exceeds threshold), and exact match. All realistic, all from one framework toggling behavior.

### Why This Matters

"We tested tolerance comparison against actual library-level variance, not synthetic data" is a stronger statement than "we tweaked some numbers by hand." It mirrors the real migration challenge — replacing bespoke external modules with standardized Spark SQL and proving the outputs are equivalent within documented tolerances.

*(Decision 15, Design Session 002)*

---

## 15. CSV Dialect: Known Landmine

"CSV" is not a standard. It is a gentleman's agreement everyone interprets differently. Quoting rules, escape characters, delimiter handling, null representation — every writer has opinions.

The prior QBV tool used Python's standard CSV library, which parsed correctly. But downstream systems had custom parsers that behaved differently. The ETL framework's PySpark CSV writer had its own quirks.

### POC Approach

Use a standard parser (Python `csv` module or pandas). Read both files with the same parser configuration. If both were written by the same framework, they should parse the same way.

### Production Landmine

The comparison target configuration will eventually need to specify CSV dialect — delimiter, quote character, escape character, null representation. This is significant effort and **must be documented in the BRD for the vendor build**. There is a realistic chance this becomes a waterfall BRD item for an offshore team.

*(Decision 9, Design Session 002)*

---

## 16. SDLC Flow

The agreed development flow from business requirements through code:

| Step | Artifact | Description |
|------|----------|-------------|
| 1 | **BRD** | This document. Formalizes business requirements from design sessions 001 and 002. |
| 2 | **Test Architecture + BDD Scenarios** | What we are testing. Acceptance criteria organized by feature. Given/When/Then against business requirements, not implementation. |
| 3 | **Adversarial Review** | Gaps in the test plan. What scenarios are not covered? Independent Claude reviewers attack the test architecture. |
| 4 | **Test Data Management** | Design and generate fixtures covering BDD scenarios. Parquet multi-part files, CSVs with trailers, rounding variance, null representation mismatches, happy-path exact matches. Test data derives from BDD scenarios, independent of code structure. |
| 5 | **FSD** | Modules, interfaces, function signatures, data flow. The code architecture. |
| 6 | **Unit Tests** | pytest code written against FSD interfaces, using test data from step 4. |
| 7 | **Code** | Make the tests pass. |

### Why This Ordering

- BDD scenarios are testable requirements without implementation assumptions. They bridge business requirements and code.
- Test data and FSD are independent — test data derives from BDD scenarios, FSD derives from BRD. They could be parallel, but sequential is acceptable for a POC.
- Unit tests need both the FSD (to know what to call) and test data (to know what to feed). They come after both.
- Test data fixtures double as demo assets for the CIO presentation.
- Dan reviews and approves every test case personally. This is the "asshole quality engineer" role, intentionally.

*(Decision 18, Design Session 002)*

---

## 17. Out of Scope

### Out of Scope for POC

| Item | Rationale | Revisit When |
|------|-----------|--------------|
| Database validation (PostgreSQL, Oracle, SQL Server, Synapse) | Trivial to implement but significant setup work. DB-out jobs write parquet first; compare the parquet. | Production pilot |
| Synapse validation | Supposed to mirror ADLS Delta 1:1. Rule broken ~100 times. Ignored during cloud migration. | After ADLS Delta comparison is battle-tested |
| Vanilla Salesforce (directly) | Same ADF parquet pattern; resolves to parquet comparison | When parquet comparison is proven in production |
| Exotic MFT formats (XML, JSON, EBCDIC, binary) | ~4% of estate. Architecture supports via pluggable readers but not implementing now | After CSV and parquet readers are solid |
| Evidence package assembly tooling | QA process concern, not a tool concern | Never (Proofmark's scope ends at the report) |
| Batch / orchestration | One target at a time. Batching is external. | Vendor build |

### Permanently Out of Scope

- **Custom Salesforce ADF pipeline** — Application integration, not ETL. Not Proofmark's problem. Recommendation: tell the CIO it is out of scope entirely.

---

## 18. Production Considerations

The following items are explicitly documented as vendor-build requirements. They are not solved by the POC but must be addressed by the production tool.

### PII/PCI Value Stripping

Production mismatch reports cannot contain actual cell values. Row hash, column name, tier, and match/fail are clean. Actual values go to a secured location with restricted access. The report metadata, summary, classification, and stamp remain unclassified.

### CSV Dialect Specification

Per-target configuration of delimiter, quote character, escape character, and null representation. This is a significant effort. The POC uses standard parsers with uniform configuration.

### Verbosity Flags

The POC runs one way. The production tool needs verbose, quiet, and normal output modes.

### Hash Algorithm Configurability

The POC uses MD5. The production tool must allow the algorithm to be configured (SHA256, etc.) for compliance purposes, even though it provides zero functional benefit for a comparison hash.

### File Output Default

The POC defaults to stdout. The production tool should likely default to file output with a structured output directory.

### Batch Execution

The POC handles one target per invocation. The production tool may need a batch mode or an integration point for orchestration frameworks.

### Exotic Format Readers

XML, JSON, EBCDIC, and other MFT format readers. The pluggable reader architecture supports this; the readers themselves need to be built.

---

## Appendix A: Decision Traceability

Every requirement in this BRD traces to a specific decision in the design sessions.

| BRD Section | Source Decision | Design Session |
|---|---|---|
| 3.1 Comparison Target | Decision 1 | 002 |
| 3.2 No Relationships Between Targets | Decision 2 | 002 |
| 3.3 File vs. File Comparison | Decision 3 | 002 |
| 3.4 Two Readers | Decision 6 | 002 |
| 3.5 Parquet Part Files | Decision 4 | 002 |
| 4. Comparison Pipeline | Decision 5 | 002 |
| 5. Column Classification | Decision 7 | 002 |
| 6. Configuration | Decision 11 | 002 |
| 7. Tolerance Specification | Decision 14 | 002 |
| 8. Null Handling | Decision 17 | 002 |
| 9. Line Break and Encoding | Decision 8 | 002 |
| 10. Hash Algorithm | Decision 16 | 002 |
| 11. Report Output | Decision 10 | 002 |
| 12. CLI Interface | Decision 12 | 002 |
| 13. Evidence Package | Decision 13 | 002 |
| 14. Test Data Strategy | Decision 15 | 002 |
| 15. CSV Dialect | Decision 9 | 002 |
| 16. SDLC Flow | Decision 18 | 002 |
| 17. Out of Scope | — | 001 + out-of-scope.md |
| 18. Production Considerations | Decisions 9, 10, 12, 16 | 002 |

Foundational architecture (format-agnostic engine, pluggable readers, three-tier threshold model, information isolation model, SDLC approach) originates from Design Session 001 (2026-02-27). All 18 numbered decisions originate from Design Session 002 (2026-02-28).

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| **Comparison target** | A pair of data sources plus a column configuration and reader config. The unit of work in Proofmark. |
| **Tier 1** | Excluded columns. Dropped before hashing. Not compared. |
| **Tier 2** | Exact match columns. Byte-level equivalence required. The default for all columns. |
| **Tier 3** | Tolerance columns. Match within a configured absolute or relative tolerance. |
| **Part file** | One of multiple physical files comprising a single logical Parquet dataset. Produced by Spark partitioning. |
| **Evidence package** | A governance deliverable assembled outside Proofmark. Includes Proofmark report(s), business context, sign-offs, and attestation disclaimer. |
| **Default-strict** | The design philosophy where omitting configuration yields the strictest possible comparison. Relaxation requires explicit config and justification. |
| **COTS** | Commercial off-the-shelf. Proofmark is presented to builder agents as if it were a COTS product, maintaining information isolation. |
| **OFW** | The real platform's orchestration framework. Proofmark does not know about it. |
