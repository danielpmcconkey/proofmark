> **Note:** This document was written 2026-02-28 during Proofmark's original build and is likely outdated. Retained for historical reference.

# Proofmark — Business Requirements Document

**Version:** 3.1
**Date:** 2026-02-28
**Status:** Draft
**Classification:** Internal — Working Document
**Revision:** v3.1 — FSD audit corrections (FUZZY-as-mismatch, match_count semantics, threshold precision)

---

## 1. Executive Summary

Proofmark is an output comparison and validation tool for ETL pipeline governance. It exists to answer a single question: when a technology team rewrites an ETL job, does the rewritten job produce equivalent output to the original?

The name comes from proof marks on firearms: the stamp from an independent proof house certifying that a weapon has been pressure-tested. The proof house doesn't care who built the gun. It cares whether it passes.

### Attestation Disclaimer

**[BR-1.1]** **Output equivalence certifies equivalence to the original, NOT correctness in an absolute sense.** If the original job contains a bug that produces incorrect output, and the rewrite faithfully reproduces that bug, Proofmark will report PASS. Proofmark certifies that two outputs match. It does not validate business logic correctness. This distinction must appear in every evidence package that includes a Proofmark report.

---

## 2. Scope

### In Scope (MVP)

- **[BR-2.1]** **Delta Parquet comparison** — Delta Parquet part files. The comparison target is the parquet file output, not any downstream database or application instance.
- **[BR-2.2]** **CSV comparison** — Simple CSV file outputs and CSV files with trailing control records (header rows, trailer rows with checksums or row counts).
- **[BR-2.3]** **Three-tier column classification** — Per-target configuration of EXCLUDED, STRICT, and FUZZY columns (see Section 5).
- **[BR-2.4]** **Hash-sort-diff pipeline** — Order-independent comparison via row hashing, sorting by hash, and group-count diff.
- **[BR-2.5]** **JSON comparison reports** — One report per comparison target, machine-parseable and human-readable.
- **[BR-2.6]** **Configuration** — Per-target configuration with default-strict philosophy and justification requirements. YAML is the reference implementation format; the requirement is structured configuration with comment support.
- **[BR-2.7]** **CLI interface** — Accepts a configuration path, LHS data path, RHS data path, and optional output path. Exit codes for scripting.

### Out of Scope (MVP)

| Item | Rationale | Revisit When |
|------|-----------|--------------|
| Database validation (PostgreSQL, Oracle, SQL Server, Synapse) | Implementable but significant setup work. Database-out jobs typically write file output first; compare the file. | Production pilot |
| Exotic MFT formats (XML, JSON, EBCDIC, binary) | The architecture supports them via pluggable readers, but they are not implemented for the MVP. | After CSV and parquet readers are solid |
| Evidence package assembly tooling | Proofmark produces a comparison report. Assembly of that report into a governance evidence package is a QA process concern, not a tool concern. | Never (Proofmark's scope ends at the report) |
| Batch mode / orchestration | Running multiple comparison targets in sequence or parallel is orchestration. Proofmark compares one target at a time. | Vendor build |
| PII/PCI stripping from reports | The MVP assumes that users who view Proofmark outputs have appropriate entitlements with respect to source data, that all data is appropriately classified, and that all privacy agreements are in place. | Vendor build |

### MVP vs. Production Distinction

| Capability | MVP (Proofmark) | Production (Vendor Build) |
|---|---|---|
| Comparison engine | Working | Same architecture, enterprise-grade |
| Readers | Parquet, CSV | Parquet, CSV, exotic formats as needed |
| Hash algorithm | MD5 (hardcoded) | Configurable (MD5, SHA256, etc.) |
| CSV dialect handling | Standard parser, same config both sides | Full dialect specification per target |
| Report detail | Full cell values in mismatch output | PII-stripped; values in secured location |
| Verbosity | Single mode | Verbose/quiet/normal flags |
| Output destination | File output with configurable path | File default with structured output directory |
| Batch execution | Not supported | Orchestration layer handles batching |
| Encoding handling | Configurable single encoding (UTF-8 default) | Detection and normalization capabilities |
| Mismatch correlation | Deterministic function for common cases | Full fuzzy matching |

---

## 3. Core Concepts

### 3.1 Comparison Target

The unit of work in Proofmark is a **comparison target**, not a "job." In enterprise ETL platforms, orchestration triggers can be single jobs with one output, multi-step workflows producing many outputs in sequence, date-driven batch runs, jobs with sub-tasks spanning multiple compute engines, or jobs registered across federated task management systems. There is no clean 1:1 mapping between an orchestrated task and the thing to compare.

**[BR-3.1]** Proofmark does not know what a job is. A comparison target is:

- A pair of data sources: the **LHS** (left-hand side — the original output, the source of truth) and the **RHS** (right-hand side — the output being validated)
- A column configuration (STRICT / FUZZY / EXCLUDED classification)
- A reader type and reader-specific configuration

The mapping from orchestrated tasks to comparison targets is the responsibility of whoever configures Proofmark — the QA team or human operator. One job might produce five comparison targets. A chain of jobs might result in one comparison target at the end. Proofmark does not care.

**[BR-3.2]** **The Portability Test:** If you could not sell this tool to another enterprise running a completely different orchestration framework, you built it wrong. Proofmark knows about files and tabular data. It does NOT know about any specific orchestration platform, scheduling system, compute engine, or platform-specific concept.

*(Decision 1, Design Session 002; S-3, S-5, Revision Log)*

### 3.2 No Relationships Between Targets

**[BR-3.3]** Proofmark does not model dependencies between comparison targets. It does not know that "target C is the final output of a chain that includes intermediary targets A and B." Grouping targets into validation runs, linking them to jobs, or mapping dependency chains is external context managed by the workflow or human process.

**[BR-3.4]** Proofmark compares individual targets and produces individual reports.

*(Decision 2, Design Session 002)*

### 3.3 File vs. File Comparison

**[BR-3.5]** Proofmark compares files to files. There is no database in the comparison loop.

- LHS: a file output (parquet or CSV)
- RHS: a file output (parquet or CSV)
- Proofmark reads both files, compares, reports

*(Decision 3, Design Session 002; S-5, Revision Log)*

### 3.4 Two Readers

**[BR-3.6]** There are two reader types: parquet and CSV. Simple CSV and CSV-with-trailer are the same reader with different configuration.

**Parquet reader:**
- **[BR-3.7]** Input: directory path containing part files
- **[BR-3.8]** Reads all `*.parquet` files in the directory
- **[BR-3.9]** Assembles into one logical table

**CSV reader:**
- **[BR-3.10]** Input: file path
- **[BR-3.11]** Configuration: number of header rows (separated from data, preserved in position, compared as literal strings in order), number of trailer rows (separated from data, preserved in position, compared as literal strings in order)
- **[BR-3.12]** Everything between header and trailer is data and goes through the hash-sort-diff pipeline
- **[BR-3.13]** Header and trailer rows are compared as exact literal string matches, in order, independently from the hash-sort-diff pipeline
- **[BR-3.14]** Both header/trailer comparison results and data comparison results appear in the report

"Simple CSV" is the CSV reader with `header_rows: 1` (or 0) and `trailer_rows: 0`. Same reader, different config.

*(Decision 6, Design Session 002; T-5, Revision Log)*

### 3.5 Parquet Part Files: Directory-Level Comparison

Delta Parquet outputs are spread across multiple part files. The number of part files is an implementation detail of the compute engine (e.g., number of partitions). A rewritten job may coalesce into fewer parts as an optimization. The data is identical; the physical layout is different.

**[BR-3.15]** The parquet reader reads all part files in a directory, assembles them into one logical table, and proceeds to comparison. Row ordering across parts is meaningless. Comparison is order-independent.

**[BR-3.16]** The same output spread across multiple part files must compare correctly against the same output coalesced into fewer part files.

*(Decision 4, Design Session 002)*

### 3.6 LHS / RHS Terminology

Throughout this document and in all Proofmark interfaces:

- **[BR-3.17]** **LHS (Left-Hand Side):** The original output. The source of truth. The output that was previously certified or accepted.
- **[BR-3.18]** **RHS (Right-Hand Side):** The output being validated. The rewrite's output that must prove equivalence to the LHS.

This terminology is standard in enterprise reconciliation platforms. LHS is always authoritative. Proofmark's job is to prove RHS reproduces what was certified, not to validate the original.

*(S-5, Revision Log)*

---

## 4. Comparison Pipeline

The pipeline executes in the following order for each comparison target:

### Pre-Comparison: Line Break Check (CSV Only)

**[BR-4.1]** Before the pipeline begins, check the line break style of both LHS and RHS files. If the line break styles differ (e.g., LHS uses CRLF, RHS uses LF):

- **[BR-4.2]** Set a **file-level FAIL flag** ("FAIL — line break mismatch").
- **[BR-4.3]** Normalize both files to a common line break format internally for row-splitting purposes only.
- **[BR-4.4]** **Continue running the full comparison.** The team gets the full picture in one pass — they see the line break problem AND any data mismatches, rather than fixing line breaks, re-running, and discovering additional problems.
- **[BR-4.5]** The report includes the match rate from the data comparison plus the line break mismatch flag. Both are visible.

**[BR-4.6]** This step does not apply to parquet (binary format; line breaks are not relevant).

*(T-12, Revision Log)*

### Step 1: Load

**[BR-4.7]** Read both sources using the configured reader. For parquet, this means reading a directory of part files and assembling into one logical table. For CSV, this means reading the file, separating header/trailer rows from data rows per configuration.

**[BR-4.8]** Both files are read using the same encoding setting (UTF-8 by default, configurable — see Section 9). If either file is not valid in the configured encoding, exit with error (exit code 2).

### Step 2: Schema Validation

**[BR-4.9]** Compare the schemas of LHS and RHS. Any schema difference is an **automatic fail** (exit code 1):

- **[BR-4.10]** Column count mismatch
- **[BR-4.11]** Column name mismatch
- **[BR-4.12]** Column type mismatch (including precision differences, e.g., varchar(200) vs. varchar(400) in parquet)

Rationale: even if no data would be truncated, a schema mismatch indicates the rewrite changed the output structure. That is a logic problem and must be flagged, not silently tolerated.

**[BR-4.13]** For CSV files without embedded schema metadata, column count and header names (if header rows are configured) are validated. Type validation applies to parquet, where the schema is embedded in file metadata.

*(T-10, Revision Log)*

### Step 3: Exclude

**[BR-4.14]** Drop all EXCLUDED columns. These columns do not exist from this point forward. They are not hashed, not compared, not present in downstream steps.

**Why exclusion happens before hashing:** If an EXCLUDED column (e.g., a UUID) differs between LHS and RHS, hashing it would produce completely different hash values, which would produce completely different sort orders, which would make group-count comparison impossible. Exclude first, hash what remains.

### Step 4: Hash

**[BR-4.15]** Concatenate all non-excluded columns for each row into a single string representation. Store this concatenated unhashed value alongside the row.

**[BR-4.16]** Hash only **STRICT columns** to produce a sort key per row. FUZZY columns are excluded from the hash but preserved for tolerance comparison in the Diff step. This ensures that rows differing only in FUZZY columns (within tolerance) land in the same hash group, where their FUZZY column values can be compared against configured tolerances.

*(T-1, Revision Log)*

### Step 5: Sort

**[BR-4.17]** Sort both datasets by hash value. This produces deterministic ordering regardless of physical file layout, original row order, or part file distribution. No sort key configuration required.

**Why hash-sort instead of sort keys:** Reliable sort keys are not guaranteed across ETL platforms. Hashing the row content and sorting by hash eliminates sort key configuration, null sort edge cases, and composite key debates.

### Step 6: Diff

**[BR-4.18]** Group rows by hash value and compare group counts between LHS and RHS:

- **[BR-4.19]** **Hash group exists in both LHS and RHS:** Compare counts. If LHS count equals RHS count, all rows in the group are matched. If counts differ, the surplus rows (|lhsCount - rhsCount|) are unmatched.
- **[BR-4.20]** **Hash group exists in only one side:** All rows in the group are unmatched (0 matches, counted as surplus).

**[BR-4.21]** Within each matched hash group, validate **FUZZY columns** against their configured tolerances (see Section 7). Any FUZZY column value exceeding its tolerance is a mismatch — both the LHS and RHS row in the failed pair are reclassified as unmatched, reducing the matched count for that hash group. FUZZY tolerance violations are first-class mismatches: they reduce the match percentage and are governed by the same threshold as hash-level mismatches. There is no separate FUZZY pass/fail gate.

**[BR-4.22]** **Duplicate row handling:** This is multiset comparison, not set comparison. If the LHS has 3 identical rows (after EXCLUDED column removal and STRICT column hashing), the RHS must also have exactly 3. Row counts per hash group matter.

*(T-1, T-7, Revision Log)*

### Step 7: Report

**[BR-4.23]** All mismatches are reported regardless of pass/fail. The threshold determines the stamp, not the visibility. A comparison target that passes at 99.5% still shows every mismatch in the report.

*(Decision 5, Design Session 002)*

---

## 5. Column Classification

**[BR-5.1]** Proofmark uses a three-tier column classification model. Every column in a comparison target belongs to exactly one tier.

### EXCLUDED

**[BR-5.2]** Known non-deterministic columns — UUIDs, timestamps, sequence IDs, runtime-assigned identifiers. These columns are dropped before hashing and are not compared.

**[BR-5.3]** **Requirement:** Every EXCLUDED column must include a documented justification in the configuration. The justification flows into the comparison report. "We excluded it because it didn't match" is not a justification.

### STRICT (Default)

**[BR-5.4]** Business-critical fields. Byte-level exact match required. No tolerance, no normalization.

**[BR-5.5]** **This is the default.** Any column not explicitly classified as EXCLUDED or FUZZY is STRICT. STRICT columns are hashed for sort ordering and compared via hash group counts.

### FUZZY

**[BR-5.6]** Columns with expected minor variance — floating point rounding, precision differences between computation engines. Per-column configurable tolerance with both absolute and relative modes (see Section 7).

**[BR-5.7]** FUZZY columns are excluded from the hash computation but preserved for tolerance comparison within hash groups during the Diff step. This resolves the inherent tension between hashing (which produces wildly different values for minor differences) and tolerance comparison (which needs to evaluate the magnitude of those differences).

**[BR-5.8]** **Requirement:** Every FUZZY classification must include a documented justification and an explicit tolerance value and type. "Floating point is weird" is not a justification. "Rounding variance between computation engines, tolerance +-0.01 absolute" is.

### Default-Strict Philosophy

**[BR-5.9]** If no column configuration is provided for a comparison target, every column is STRICT (exact match). This is the strictest possible default.

**[BR-5.10]** The operator's job is to carve out exceptions and justify each one. The burden of proof is on relaxing the standard, not on tightening it. The evidence package shows: "We compared 47 columns exactly and excluded 3, here's why for each."

*(Decision 7, Design Session 002; S-4, T-1, Revision Log)*

---

## 6. Configuration

### Requirements

The configuration must:

- **[BR-6.1]** Support inline comments (natural place for justifications and audit trail)
- **[BR-6.2]** Be human-readable and human-editable
- **[BR-6.3]** Be programmatically generatable by automated workflows
- **[BR-6.4]** Be less verbose than JSON for readability

**[BR-6.5]** YAML is the reference implementation format. The requirement is structured, commented configuration — not a specific serialization format.

### Configuration Defines HOW, Not WHAT

**[BR-6.6]** The configuration file defines **how** to compare: reader type, column classifications, tolerances, encoding, threshold. It does NOT contain file paths.

**[BR-6.7]** The CLI invocation provides **what** to compare: LHS path, RHS path.

**[BR-6.8]** **This separation is critical for reusability.** A single configuration (e.g., `daily_balance.yaml`) is valid for every date's comparison of that target. The same config compares Tuesday's LHS to Tuesday's RHS, then Wednesday's LHS to Wednesday's RHS. If a configuration needs to change between dates, that indicates a problem — the same rigor must be applied consistently across all dates. If a config changes, go back to the start date and re-run all comparisons with the updated config.

*(T-3, Revision Log)*

### Reference Configuration Schema (YAML)

```yaml
comparison_target: daily_balance_feed    # Human-readable name
reader: csv                              # "csv" or "parquet"

# Reader-specific config (omit section if not applicable)
csv:
  header_rows: 1      # Rows separated before data (compared as literal strings, in order)
  trailer_rows: 1      # Rows separated after data (compared as literal strings, in order)

# Encoding (default: utf-8)
encoding: utf-8

# Pass/fail threshold (default 100.0)
threshold: 100.0

# Column classification
# Everything NOT listed here defaults to STRICT (exact match)
columns:
  excluded:  # Dropped before hashing — requires justification
    - name: run_id
      reason: Non-deterministic UUID assigned at runtime
    - name: load_timestamp
      reason: Execution timestamp, varies per run

  fuzzy:  # Tolerance match — requires justification and tolerance value
    - name: interest_accrued
      tolerance: 0.01
      tolerance_type: absolute
      reason: Floating point rounding between computation engines
    - name: market_value
      tolerance: 0.001
      tolerance_type: relative
      reason: Rounding variance scales with value magnitude
```

### Design Notes

- Parquet configs omit the `csv` section entirely. The parquet reader only needs the directory paths provided via CLI.
- If `encoding`, `threshold`, or `columns` are omitted, the strictest possible defaults apply. Relaxation requires explicit configuration plus justification.
- The `reason` field on EXCLUDED and FUZZY columns flows into the report's column classification section. It is the audit trail. Justifications must be evidentiary — they must cite specific instances in the data or code that demonstrate why the relaxation is necessary (e.g., "Column `load_timestamp` is assigned at runtime per `DataWriter.cs:47`; values differ between original and rewrite executions"). Vague rationale ("this column changes sometimes") is not acceptable.
- There is no `strict` list. Everything unlisted is STRICT by default. Listing STRICT columns would be redundant noise.
- The configuration file does not override CLI-provided file paths. File paths come exclusively from the CLI invocation.

*(Decision 11, Design Session 002; S-4, S-5, T-3, Revision Log)*

---

## 7. Tolerance Specification

**[BR-7.1]** FUZZY columns support two tolerance modes, configurable per column. There are no hardwired defaults on tolerance type — the person configuring it makes a conscious choice and justifies it.

### Absolute Tolerance

**[BR-7.2]** Match condition: `|lhs - rhs| <= tolerance`

Use when the acceptable variance is a fixed value regardless of magnitude (e.g., rounding to the nearest cent).

### Relative Tolerance

**[BR-7.3]** Match condition: `|lhs - rhs| / max(|lhs|, |rhs|) <= tolerance`

Division uses the larger absolute value. Use when acceptable variance scales with value magnitude (e.g., large dollar amounts where a fixed tolerance is too tight or too loose).

### Edge Cases

- **[BR-7.4]** **Both values are 0:** Match. Zero delta.
- **[BR-7.5]** **One value is 0, other is not:** Math works naturally. `|0 - 0.0001| / max(0, 0.0001) = 1.0` — 100% relative difference, fails any reasonable tolerance. No special case needed.

### Requirements

- **[BR-7.6]** `tolerance_type` is **required** on every FUZZY column. There is no default. This forces an explicit, justified choice.
- **[BR-7.7]** `tolerance` (the numeric value) is required on every FUZZY column. The chosen value must be evidentiary — it must cite specific instances in the data or code that demonstrate the expected variance magnitude (e.g., "Tolerance 0.01 absolute: `OriginalCalc.cs:112` uses `ROUND_HALF_UP` while rewrite uses Spark SQL `ROUND()` which applies banker's rounding; maximum observed delta across Oct 2024 data is 0.005"). Tolerances chosen without evidence ("0.01 seems reasonable") are not acceptable.
- **[BR-7.8]** There is no "percentage" type. Relative tolerance with `tolerance: 0.01` *is* 1%. A third label for the same math creates confusion for zero value-add.

*(Decision 14, Design Session 002)*

---

## 8. Null Handling

### Parquet

**[BR-8.1]** Non-issue. Parquet has a typed schema with native null support. Null is null — not empty string, not the literal text `"NULL"`. The format enforces this. Two nulls match. Null vs. empty string is a mismatch, correctly, because the schema says they are different things.

### CSV

The wild west of null representation:

- Empty field: `,,`
- Empty quoted string: `,"",`
- Literal text: `NULL`, `null`, `\N`, `NA`, `N/A`, `NaN`
- Whitespace: `, ,`

Every upstream system has its own opinion. If the LHS wrote `NULL` and the RHS writes an empty field, that is a **legitimate mismatch**. Downstream systems with brittle parsers treat these differently. Real consequences.

### The Rule

**[BR-8.2]** **Byte-level comparison. No null equivalence. No null normalization.** `NULL` is not equal to an empty field, is not equal to `""`, is not equal to `null`. If the bytes are different, it is a mismatch. This is consistent with the default-strict philosophy throughout the system.

**[BR-8.3]** The *rewrite process* is responsible for matching the original's null representation. If Proofmark flags a null mismatch, the fix is in the rewrite — cast your nulls to match the expected format. The comparison tool does not paper over differences.

### Null Handling in Hashing

**[BR-8.4]** No special treatment. Nulls (however represented) are bytes in the row. They hash like everything else.

*(Decision 17, Design Session 002)*

---

## 9. Encoding Handling

### MVP Approach

**[BR-9.1]** Both files are read using the same encoding. The default encoding is UTF-8. The encoding is configurable in the comparison target configuration (e.g., `encoding: utf-8`, `encoding: latin-1`).

- **[BR-9.2]** If either file is not valid in the configured encoding, Proofmark exits with an error (exit code 2).
- **[BR-9.3]** No encoding detection is performed. No encoding normalization is performed.
- **[BR-9.4]** Both LHS and RHS are always read with the same encoding setting.

**[BR-9.5]** The rewrite process is responsible for producing output in the expected encoding. If the original writes UTF-8, the rewrite must write UTF-8. Encoding mismatches are a rewrite problem, not a comparison tool problem.

### Production Consideration

Encoding detection and normalization for CSV files (which have no embedded encoding metadata) is non-trivial. This is vendor-build territory. The MVP requires the operator to know the encoding of their files and configure accordingly.

*(T-11, Decision 8, Design Session 002; Revision Log)*

---

## 10. Hash Algorithm

**[BR-10.1]** **MVP:** MD5. It is fast, universally available, and produces excellent distribution for row comparison and sorting. Collision risk is irrelevant — this is a comparison hash, not a security function.

**[BR-10.2]** **Optics management:** The algorithm name is not surfaced in report output. Reports show row hashes for mismatch identification. The algorithm that produced them is an implementation detail. If asked: "It is a comparison hash, not a security function."

**Production:** The hash algorithm should be configurable. The vendor can offer SHA256 if it makes compliance requirements easier. It is slower for zero benefit in this use case, but it will be irrelevant to the business outcome — hash is hash, swap the function, pipeline works the same.

*(Decision 16, Design Session 002)*

---

## 11. Report Output

### Format

**[BR-11.1]** JSON. One report per comparison target. JSON serves two audiences: the automated workflow (machine consumer needing structured data to parse pass/fail) and the human reviewer (needing a readable summary for governance). Machine-parseable and human-readable.

### Report Contents

**[BR-11.2]** **Metadata:**
- Timestamp
- Proofmark version
- Comparison target name
- Config file path

**[BR-11.3]** **Config echo:**
- Full configuration used for this comparison, embedded in the report so it is self-contained

**[BR-11.4]** **Column classification:**
- Which columns are EXCLUDED, STRICT, FUZZY
- Justifications echoed from configuration

**[BR-11.5]** **Summary:**
- Row counts (LHS, RHS)
- Match count (single-counted: the number of row pairs that matched. Not the double-counted internal value used for percentage calculation.)
- Mismatch count: `max(row_count_lhs, row_count_rhs) - match_count`. Single-counted, paralleling match_count.
- Match percentage (see formula below)
- Pass/fail stamp
- Threshold used
- Line break mismatch flag (CSV only, if applicable)

**[BR-11.6]** **Header/trailer comparison (CSV only):**
- Result of literal string comparison of header rows (LHS vs. RHS)
- Result of literal string comparison of trailer rows (LHS vs. RHS)

**[BR-11.7]** **Control record comparison:**
- Cross-file comparison only: LHS trailer content vs. RHS trailer content as literal strings.
- **[BR-11.8]** Proofmark does NOT validate internal consistency (e.g., whether a trailer's row count matches the actual data rows within that file). LHS is the source of truth. Proofmark's job is to prove RHS reproduces what was certified, not to validate the original. This is consistent with the attestation disclaimer.

**[BR-11.9]** **Mismatch detail:**
- Every mismatch, regardless of pass/fail
- Per hash group: hash value, LHS count, RHS count, status (MATCH or COUNT_MISMATCH with surplus detail)
- For unmatched rows: the unhashed concatenated row content (plaintext), enabling the human reviewer to identify which rows differ and why
- For FUZZY column mismatches: tolerance, tolerance type, and actual delta

**[BR-11.10]** **Mismatch row correlation:**
- For mismatched rows, Proofmark includes a deterministic correlation function that handles common cases — rows sharing most column values but differing in 1-2 columns.
- **[BR-11.11]** When correlation confidence is low, the report falls back to presenting unmatched LHS rows and unmatched RHS rows separately.
- **[BR-11.12]** Full fuzzy matching across all mismatch scenarios is vendor-build territory.

### Match Percentage Formula

**[BR-11.13]** The match percentage represents the proportion of rows that are equivalent across both sides:

- **[BR-11.14]** **Per hash group:** hash-level matched pairs = min(lhsCount, rhsCount). If FUZZY columns exist, each matched pair is validated against FUZZY tolerances. Pairs that fail FUZZY validation are reclassified as unmatched. Final matched for the group = (hash-matched pairs - FUZZY-failed pairs) x 2 (each matched row is counted on both the LHS and RHS side). FUZZY-failed rows from both sides become surplus/unmatched.
- **[BR-11.15]** **Surplus per group:** |lhsCount - rhsCount| from hash-level count mismatch, PLUS any FUZZY-failed pairs x 2 — these are all unmatched rows
- **[BR-11.16]** **Rows unique to one side:** Hash groups existing only in LHS or only in RHS contribute 0 matches. All rows in such groups count as surplus.
- **[BR-11.17]** **Total rows:** LHS row count + RHS row count (the denominator spans both sides)
- **[BR-11.18]** **Match percentage:** totalMatched / totalRows

**Example (hash mismatch):** LHS has 5,000 rows. RHS has 5,001 rows. One RHS row has no corresponding LHS row. totalMatched = 5,000 x 2 = 10,000. totalRows = 5,000 + 5,001 = 10,001. Match percentage = 10,000 / 10,001 = 99.99%.

**Example (FUZZY mismatch):** LHS has 100 rows. RHS has 100 rows. All 100 hash groups have 1 LHS row and 1 RHS row (perfect hash match). 3 of those pairs fail FUZZY tolerance validation. Final matched = (100 - 3) x 2 = 194. totalRows = 200. Match percentage = 194 / 200 = 97.0%. At a 99.5% threshold, this is FAIL. At a 95.0% threshold, this is PASS. The threshold governs all row-level mismatches uniformly — there is no distinction between a STRICT mismatch and a FUZZY mismatch for pass/fail purposes.

**[BR-11.19]** The report shows per-hash-group breakdown with hash value, LHS count, RHS count, and status.

*(T-2, T-8, Revision Log)*

### What Is Not in the Report

- **[BR-11.20]** **Matched rows.** Nobody needs 10 million "yep, same" entries. Row counts and match percentage cover it.
- **[BR-11.21]** **Platform-specific context.** Job names, orchestration IDs, scheduling metadata — not Proofmark's domain.

### Pass/Fail Logic

- **[BR-11.22]** Threshold is in the configuration (e.g., 99.5% match required). The threshold comparison must be deterministic and not subject to floating-point precision artifacts. The implementation must ensure that boundary cases (e.g., exactly 99.5% match rate with a 99.5% threshold) produce consistent, correct results.
- **[BR-11.23]** Default threshold: 100.0% (consistent with default-strict philosophy). Any surplus row = FAIL at default threshold.
- **[BR-11.24]** The report always shows ALL mismatches regardless of pass/fail.
- **[BR-11.25]** PASS requires ALL of the following:
  - Match percentage >= threshold (the single control for row-level equivalence — both hash-level mismatches and FUZZY tolerance violations reduce the match percentage and are governed by this threshold)
  - No schema mismatch (auto-fail)
  - No line break mismatch flag (CSV) (auto-fail)
  - No header mismatch (CSV) (auto-fail)
  - No trailer mismatch (CSV) (auto-fail)

  The four auto-fail conditions are structural problems that cannot be meaningfully captured by a percentage. Headers and trailers must be byte-for-byte equivalent — they are part of the equivalence certification, not advisory metadata.
- **[BR-11.26]** FAIL = anything else.

*(Decision 10, Design Session 002; T-8, T-10, T-12, Revision Log)*

---

## 12. CLI Interface

### Required Inputs

The CLI must accept the following inputs:

- **[BR-12.1]** **Configuration path:** Path to the comparison target configuration file.
- **[BR-12.2]** **LHS path:** Path to the LHS data. For CSV, this is a file path. For parquet, this is a directory path.
- **[BR-12.3]** **RHS path:** Path to the RHS data. For CSV, this is a file path. For parquet, this is a directory path.
- **[BR-12.4]** **Output path (optional):** Path where the JSON report should be written. When omitted, the JSON report is written to standard output. The report format is identical regardless of destination.

Reference invocation:
```
proofmark compare --config daily_balance.yaml --left /path/to/lhs --right /path/to/rhs
```

**[BR-12.5]** One config, one comparison, one report.

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | **[BR-12.6]** Comparison ran, PASS |
| `1` | **[BR-12.7]** Comparison ran, FAIL (including schema mismatch) |
| `2` | **[BR-12.8]** Error (bad config, file not found, encoding failure, parse failure) |

Note: discrete error codes within the error category (distinguishing "file not found" from "encoding failure" from "parse failure") are FSD territory, not BRD.

**[BR-12.9]** Exit codes allow automated workflows to script pass/fail decisions without parsing the report.

### What It Does Not Have (By Design)

- **[BR-12.10]** **No verbosity flags.** The MVP runs one way. Verbose/quiet/normal is a vendor NFR.
- **[BR-12.11]** **No batch mode.** Running multiple configs is orchestration, not Proofmark's concern.
- **[BR-12.12]** **No dry-run.** Nothing useful to validate without actually running the comparison.
- **[BR-12.13]** **No CLI flags to override config values.** The config file is authoritative for comparison settings. File paths come from CLI arguments.

*(Decision 12, Design Session 002; T-3, Revision Log)*

---

## 13. Evidence Package

**[BR-13.1]** Evidence package assembly is **out of scope** for Proofmark. Proofmark produces a comparison report. Assembly of that report into a governance evidence package is a QA process concern, not a tool concern.

*(Decision 13, Design Session 002)*

---

## 14. CSV Dialect: Known Landmine

"CSV" is not a standard. It is a gentleman's agreement everyone interprets differently. Quoting rules, escape characters, delimiter handling, null representation — every writer has opinions.

### MVP Approach

**[BR-14.1]** Use a standard parser. Read both files with the same parser configuration. If both were written by the same framework, they should parse the same way.

### Production Requirement

The comparison target configuration will eventually need to specify CSV dialect — delimiter, quote character, escape character, null representation. This is significant effort and **must be addressed by the vendor build**. There is a realistic chance this becomes a detailed specification item for the production team.

*(Decision 9, Design Session 002)*

---

## 15. SDLC Flow

This section documents the development flow for the MVP. In a standard enterprise setting, this would be governed by program-level SDLC documentation. It is included here because Proofmark's MVP is developed without a formal program team.

| Step | Artifact | Description |
|------|----------|-------------|
| 1 | **BRD** | This document. Formalizes business requirements from design sessions. |
| 2 | **Test Architecture + BDD Scenarios** | What we are testing. Acceptance criteria organized by feature. Given/When/Then against business requirements, not implementation. |
| 3 | **Adversarial Review** | Gaps in the test plan. What scenarios are not covered? Independent reviewers attack the test architecture. |
| 4 | **Test Data Management** | Design and generate fixtures covering BDD scenarios. Parquet multi-part files, CSVs with trailers, rounding variance, null representation mismatches, happy-path exact matches. Test data derives from BDD scenarios, independent of code structure. |
| 5 | **FSD** | Modules, interfaces, function signatures, data flow. The code architecture. |
| 6 | **Unit Tests** | Tests written against FSD interfaces, using test data from step 4. |
| 7 | **Code** | Make the tests pass. |

### Why This Ordering

- BDD scenarios are testable requirements without implementation assumptions. They bridge business requirements and code.
- Test data and FSD are independent — test data derives from BDD scenarios, FSD derives from BRD. They could be parallel, but sequential is acceptable for an MVP.
- Unit tests need both the FSD (to know what to call) and test data (to know what to feed). They come after both.

*(Decision 18, Design Session 002)*

---

## 16. Out of Scope (MVP)

The following items are explicitly out of scope for the MVP. They are documented here for completeness and as requirements for the production tool.

### Permanently Out of Scope

- **[BR-16.1]** **Custom application integration pipelines** — Application integration that does not follow standard ETL file output patterns is permanently out of scope. Program stakeholders should be informed that these workflows are out of scope due to the overwhelming complexity of custom integration logic.

---

## 17. Production Considerations

The following items are explicitly documented as vendor-build requirements. They are not solved by the MVP but must be addressed by the production tool.

### PII/PCI Value Stripping

Production mismatch reports cannot contain actual cell values. Row hash, column name, tier, and match/fail are clean. Actual values go to a secured location with restricted access. The report metadata, summary, classification, and stamp remain unclassified.

### CSV Dialect Specification

Per-target configuration of delimiter, quote character, escape character, and null representation. This is a significant effort. The MVP uses standard parsers with uniform configuration.

### Verbosity Flags

The MVP runs one way. The production tool needs verbose, quiet, and normal output modes.

### Hash Algorithm Configurability

The MVP uses MD5. The production tool must allow the algorithm to be configured (SHA256, etc.) for compliance purposes, even though it provides zero functional benefit for a comparison hash.

### Batch Execution

The MVP handles one target per invocation. The production tool may need a batch mode or an integration point for orchestration frameworks.

### Exotic Format Readers

XML, JSON, EBCDIC, and other MFT format readers. The pluggable reader architecture supports this; the readers themselves need to be built.

### Encoding Detection and Normalization

The MVP reads both files with a single configured encoding. The production tool should support encoding detection for CSV files and normalization across different encodings.

### Full Mismatch Correlation

The MVP includes a deterministic correlation function for common mismatch cases. The production tool should provide full fuzzy matching to correlate mismatched rows across complex scenarios.

---

## Appendix A: Decision Traceability

Every requirement in this BRD traces to a specific decision in the design sessions and/or the revision log.

| BRD Section | Source Decision | Source | BR ID Range |
|---|---|---|---|
| 1. Executive Summary | — | Attestation Disclaimer | BR-1.1 |
| 2. Scope (In Scope) | Decisions 1–14 | Design Sessions 001, 002 | BR-2.1 – BR-2.7 |
| 3.1 Comparison Target | Decision 1 | Design Session 002 | BR-3.1 – BR-3.2 |
| 3.2 No Relationships Between Targets | Decision 2 | Design Session 002 | BR-3.3 – BR-3.4 |
| 3.3 File vs. File Comparison | Decision 3 | Design Session 002 | BR-3.5 |
| 3.4 Two Readers | Decision 6, T-5 | Design Session 002, Revision Log | BR-3.6 – BR-3.14 |
| 3.5 Parquet Part Files | Decision 4 | Design Session 002 | BR-3.15 – BR-3.16 |
| 3.6 LHS / RHS Terminology | S-5 | Revision Log | BR-3.17 – BR-3.18 |
| 4. Pipeline: Line Break Pre-Check | T-12 | Revision Log | BR-4.1 – BR-4.6 |
| 4. Pipeline: Load | T-10, Decision 8 | Design Session 002, Revision Log | BR-4.7 – BR-4.8 |
| 4. Pipeline: Schema Validation | T-10 | Revision Log | BR-4.9 – BR-4.13 |
| 4. Pipeline: Exclude | Decision 7 | Design Session 002 | BR-4.14 |
| 4. Pipeline: Hash (STRICT only) | T-1 | Revision Log | BR-4.15 – BR-4.16 |
| 4. Pipeline: Sort | T-1 | Revision Log | BR-4.17 |
| 4. Pipeline: Diff (group counts) | T-7 | Revision Log | BR-4.18 – BR-4.22 |
| 4. Pipeline: Report | Decision 5 | Design Session 002 | BR-4.23 |
| 5. Column Classification (named tiers) | Decision 7, S-4 | Design Session 002, Revision Log | BR-5.1 – BR-5.10 |
| 6. Configuration | Decision 11, T-3 | Design Session 002, Revision Log | BR-6.1 – BR-6.8 |
| 7. Tolerance Specification | Decision 14 | Design Session 002 | BR-7.1 – BR-7.8 |
| 8. Null Handling | Decision 17 | Design Session 002 | BR-8.1 – BR-8.4 |
| 9. Encoding Handling | Decision 8, T-11 | Design Session 002, Revision Log | BR-9.1 – BR-9.5 |
| 10. Hash Algorithm | Decision 16 | Design Session 002 | BR-10.1 – BR-10.2 |
| 11. Report Output | Decision 10, T-2, T-8, T-9 | Design Session 002, Revision Log | BR-11.1 – BR-11.26 |
| 12. CLI Interface | Decision 12, T-3 | Design Session 002, Revision Log | BR-12.1 – BR-12.13 |
| 13. Evidence Package | Decision 13 | Design Session 002 | BR-13.1 |
| 14. CSV Dialect | Decision 9 | Design Session 002 | BR-14.1 |
| 15. SDLC Flow | Decision 18 | Design Session 002 | *(Process, not tool requirements — no BR IDs)* |
| 16. Out of Scope (Permanent) | — | Design Session 002 | BR-16.1 |

Foundational architecture (format-agnostic engine, pluggable readers, three-tier threshold model, SDLC approach) originates from Design Session 001 (2026-02-27). All 18 numbered decisions originate from Design Session 002 (2026-02-28). Structural and technical refinements (S-1 through S-5, T-1 through T-13) originate from the BRD Revision Log (2026-03-01).

**v3.1 Revisions (FSD v1 Audit, 2026-02-28):**

| Change | BR IDs Affected | Rationale |
|--------|----------------|-----------|
| FUZZY failures are first-class mismatches | BR-4.21, BR-11.14, BR-11.15, BR-11.25 | FUZZY tolerance violations now reduce match count/percentage. No separate FUZZY pass/fail gate. Threshold governs all row-level mismatches uniformly. |
| match_count is single-counted in report | BR-11.5 | Clarified that report match_count = matched pairs (not the internal double-counted value). Resolves inconsistency between BRD, test architecture, and FSD. |
| Threshold precision requirement | BR-11.22 | Threshold comparison must not be subject to floating-point precision artifacts. Implementation must handle boundary cases correctly. |
| Auto-fail conditions enumerated | BR-11.25 | PASS/FAIL conditions restructured. Four auto-fails (schema, line breaks, headers, trailers) listed explicitly. All row-level equivalence governed by threshold alone. |

---

## Appendix B: Glossary

| Term | Definition |
|---|---|
| **Comparison target** | A pair of data sources (LHS and RHS) plus a column configuration and reader config. The unit of work in Proofmark. |
| **LHS (Left-Hand Side)** | The original output. The source of truth. The output that was previously certified or accepted. |
| **RHS (Right-Hand Side)** | The output being validated. The rewrite's output that must prove equivalence to the LHS. |
| **STRICT** | Exact match columns. Byte-level equivalence required. The default classification for all columns. Hashed for sort ordering. |
| **FUZZY** | Tolerance columns. Match within a configured absolute or relative tolerance. Excluded from hash, compared within hash groups. |
| **EXCLUDED** | Columns dropped before hashing. Not compared. Requires documented justification. |
| **Part file** | One of multiple physical files comprising a single logical Parquet dataset. Produced by compute engine partitioning. |
| **Evidence package** | A governance deliverable assembled outside Proofmark. Includes Proofmark report(s), business context, sign-offs, and attestation disclaimer. |
| **Default-strict** | The design philosophy where omitting configuration yields the strictest possible comparison. Relaxation requires explicit config and justification. |
| **Portability test** | The design principle that Proofmark must be sellable to any enterprise running any orchestration framework. No platform-specific knowledge baked in. |
| **Hash group** | The set of rows sharing the same hash value after STRICT column hashing. Used for multiset comparison via group counts. |
| **Mismatch correlation** | The process of associating unmatched LHS rows with unmatched RHS rows to help identify which rows were likely intended to correspond. |

---

## Content Moved to ATC POC3 Alignment Document

The following content was present in BRD v1 and has been moved out of this document. It belongs in an internal alignment document that maps Proofmark to the specific program context. This list exists so that a reconciliation agent can verify nothing was silently dropped.

1. **Section 1 "What Proofmark Proves" block** — Three-point list about comparison architecture, information isolation model viability, and governance story. Internal strategic framing about what the MVP demonstrates to leadership.

2. **Section 1 "not the production tool" paragraph** — Commentary about Proofmark being a functional specification and POC, vendor build strategy, and organizational independence rationale. Replaced with generic product language.

3. **Section 2 In Scope — platform-specific commentary** — References to specific internal platforms (ADLS, ADF, TIBCO), volume percentages ("76% of production output"), and mapping of internal output patterns to comparison types.

4. **Section 2 Out of Scope — platform-specific rationale** — Detailed commentary about internal platform behaviors (Synapse mirroring ADLS, vanilla Salesforce ADF patterns), CIO presentation priorities, and internal migration history. Items retained as out-of-scope entries with generic rationale.

5. **Section 3.1 — platform-specific orchestration examples** — Detailed enumeration of specific internal orchestration patterns (OFW triggers, box jobs, date maker, ADB/ADF sub-tasks, federated ETL jobs tables). Replaced with generic enterprise ETL orchestration language.

6. **Section 3.1 — "Accenture test" naming** — Renamed to "Portability test." Concept retained, vendor names removed.

7. **Section 3.3 — "The real platform" references** — Specific references to internal file storage platforms (ADLS, TIBCO/ADF). Replaced with generic file output language.

8. **Section 3.5 — "Critical POC demo point" callout** — Internal demo strategy note about multi-part-file comparison. The requirement is retained; the internal framing is removed.

9. **Section 4 Step 4 — "During cloud migration" context** — Historical context about the team's cloud migration experience motivating hash-sort design. Replaced with generic technical rationale.

10. **Section 9 — "During cloud migration" real-world context** — Historical anecdote about encoding/line break mismatch experiences during migration. Replaced with generic technical requirements.

11. **Section 9 — encoding/line break "strict or normalize" options** — Replaced per T-11 (encoding is now a single configurable value, not strict/normalize toggle) and T-12 (line break mismatch is a pre-comparison fail flag, not a configurable strictness setting).

12. **Section 11 — Production Constraint block** — Detailed discussion of PII/PCI/SOX implications for mismatch reports containing cell values. Retained as a one-line item in Production Considerations and Out of Scope.

13. **Section 13 — Evidence Package (entire section)** — Full section on evidence package contents, why Proofmark's report works as evidence, and POC approach. Replaced with one-line out-of-scope reference.

14. **Section 14 — Test Data Strategy (entire section)** — Full section on MockEtlFramework test data approach, library behavior toggling, and demo scenario design. Moved entirely to alignment doc.

15. **Section 17 — Custom Salesforce "tell the CIO" language** — Specific recommendation to "tell the CIO it is out of scope." Softened to generic stakeholder communication language.

16. **Section 17 — Platform-specific out-of-scope commentary** — Detailed rationale referencing Synapse mirroring, ADLS Delta, and vanilla Salesforce ADF patterns. Items retained with generic rationale or removed where they duplicated in-scope entries.

17. **All references to "AI agent rewrites"** — Replaced with "technology team rewrites" or equivalent generic language throughout.

18. **All named internal platform references** — OFW, ADF, ADLS, TIBCO, Databricks, Autosys, Oozie removed from body text. Generic enterprise ETL language used throughout.

19. **Build-vs-buy rationale (T-13)** — Not included per revision log decision. Belongs in ATC POC3 Alignment doc.

20. **Glossary entries for platform-specific terms** — OFW, COTS (in its information-isolation context) removed from glossary. COTS framing is alignment doc content.
