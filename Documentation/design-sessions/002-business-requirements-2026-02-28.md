# Proofmark — Design Session 002 — Business Requirements — 2026-02-28

## Who Is Reading This
If you're a Claude instance, this is the second design session for Proofmark. Read session 001 first for foundational context. This session covers the business requirements conversation — what Proofmark does, how it compares, and the decisions behind the design.

## Key Decisions Made This Session

### 1. The Unit of Work Is a "Comparison Target," Not a "Job"

**The problem:** "Job" is a leaky abstraction in the real platform. An OFW trigger can be:
- A single job with one output
- A "box job" producing many outputs in sequence
- A job with "date maker" logic that queues up sequential runs for missed days
- A job with sub-tasks that hand off between ADB and ADF
- A job registered in a federated ETL jobs table across multiple curated zones

No clean 1:1 mapping between "OFW job" and "thing to compare."

**The decision:** Proofmark doesn't know what a job is. It compares **comparison targets**. A comparison target is:
- A pair of data sources (original output + rewritten output)
- A column configuration (tier 1/2/3 classification)
- A reader type and reader config

The mapping from "OFW job" to "comparison targets" is someone else's problem — the QA agent or human configuring Proofmark. One job might produce 5 comparison targets. A chain of jobs might result in one comparison target at the end. Proofmark doesn't care.

**The Accenture test:** If you couldn't sell this tool to another bank running a completely different orchestration framework, you built it wrong. Proofmark knows about files and tabular data. It does NOT know about OFW, ADF, Databricks, Autosys, Oozie, box jobs, date maker, curated zone federation, or any platform-specific concept.

### 2. Comparison Targets Have No Relationships Inside Proofmark

Proofmark does not model dependencies between comparison targets. It doesn't know that "target C is the final output of a chain that includes intermediary targets A and B." Grouping targets into validation runs, linking them to jobs, or mapping dependency chains is external context managed by the agent workflow or human process.

Proofmark compares individual targets and produces individual reports. Period.

### 3. File vs. File Comparison (No Database in the Loop)

The real platform produces files — parquet files in ADLS and CSV files through TIBCO/ADF. The production comparison tool won't be comparing database tables. The POC must reflect this.

- Original job produces a file (parquet or CSV)
- Rewritten job produces a file (parquet or CSV)
- Proofmark reads both files, compares, reports

PostgreSQL was a convenient stand-in for the MockEtlFramework POC. It's not part of the comparison architecture. MockEtlFramework will be updated to produce real file output (parquet and CSV) before Monday.

### 4. Parquet Part Files: Directory-Level Comparison

**Critical POC demo point:** The same output spread across 3 part files must compare correctly against the same output optimized into 1 part file.

In Spark, the number of part files is an implementation detail (number of partitions). The rewritten job may coalesce into fewer parts as an optimization. The data is identical; the physical layout is different.

The parquet reader:
1. Reads all part files in a directory
2. Assembles them into one logical table
3. Proceeds to comparison

Row ordering across parts is meaningless. The comparison must be order-independent.

### 5. Comparison Pipeline

The pipeline, in order:

1. **Load** — Read source (directory of part files for parquet, file for CSV). Assemble into one logical table.
2. **Exclude** — Drop tier 1 columns entirely. They don't exist from this point forward.
3. **Hash** — Hash each remaining row (all non-excluded columns).
4. **Sort** — Sort by hash value. Produces deterministic ordering regardless of physical file layout or original row order.
5. **Diff** — Walk both hash-sorted sets, compare row by row:
   - Tier 2 columns: exact match
   - Tier 3 columns: within configured tolerance
6. **Report** — All mismatches reported regardless of pass/fail. Threshold determines the stamp, not visibility.

**Why hash-sort instead of sort keys:** The real platform doesn't have reliable sort keys. During cloud migration, the team hashed the entire row and sorted by hash. No sort key config, no null sort edge cases, no composite key debates.

**Exclusion before hashing:** Tier 1 columns (UUIDs, timestamps, etc.) are excluded BEFORE hashing. If a UUID is the first column and it's different between original and rewrite, hashing it would produce completely different sort orders, making sequential comparison impossible. Exclude first, hash what's left.

**Duplicate rows:** This is multiset comparison, not set comparison. If the original has 2 identical rows (after tier 1 exclusion), the rewrite must also have exactly 2. Row counts matter.

### 6. Two Readers, Not Three

Session 001 identified three comparison types: parquet, simple CSV, CSV with trailing control record. Turns out simple CSV and CSV-with-trailer are the same reader with different config.

**Parquet reader:**
- Input: directory path containing part files
- Reads all `*.parquet` files in directory
- Assembles into one logical table

**CSV reader:**
- Input: file path
- Config: number of header rows to skip (for sort/hash, compared as literal strings), number of trailer rows to skip (for sort/hash, compared as literal strings)
- Everything between header and trailer is data — goes through hash-sort-diff pipeline
- Header and trailer rows are compared as exact literal string matches, in order

"Simple CSV" is just CSV reader with header=1 (or 0), trailer=0. Same reader, different config.

### 7. Default Everything to Tier 2 (Exact Match)

If no column configuration is provided for a comparison target, every column is tier 2 (exact match). Strictest possible default.

The QA agent's job is to carve out exceptions:
- "This column is a UUID, move it to tier 1 (excluded)" — requires justification
- "This column has floating point rounding, move it to tier 3 with tolerance ±0.01" — requires justification

The burden of proof is on relaxing the standard, not on tightening it. The evidence package shows: "we compared 47 columns exactly and excluded 3, here's why for each."

### 8. Line Break and Encoding: Configurable Strictness

**The real-world lesson:** At the start of cloud migration, encoding and line break mismatches were showstoppers. By the end, it was "fix your downstream ingestion process to be less brittle."

Proofmark needs to support both stances. Per comparison target config:

- **Line breaks:** `strict` (CRLF ≠ LF, must match) or `normalize` (treat all line break styles as equivalent)
- **Encoding:** `strict` (byte-level must match) or `normalize` (decode both to common encoding, compare characters)

Default: `strict`. Relax with documented justification. Early in the program, everything's strict. Later, configs relax as teams document why.

Evidence package shows the setting: "compared with strict encoding" or "normalized line endings per approved exception [reference]."

### 9. CSV Dialect: Known Landmine (Document, Don't Solve This Weekend)

"CSV" isn't a standard. It's a gentleman's agreement everyone interprets differently. Quoting rules, escape characters, delimiter handling, null representation — every writer has opinions.

The prior QBV tool whiffed on this. It used Python's standard CSV lib, which parsed correctly. But downstream systems had custom parsers that behaved differently. The ETL framework's PySpark CSV writer had its own quirks.

**POC approach:** Use a standard parser (Python csv module or pandas), read both files with the same parser config. If both were written by the same framework, they should parse the same way.

**Production landmine:** The comparison target config will eventually need to specify CSV dialect — delimiter, quote char, escape char, null representation. This is a significant effort for the vendor build.

**This should be documented in the BRD for the vendor build. There's a good chance this turns into a waterfall BRD for an offshore team.**

## Still Open (To Discuss Before Building)

These were NOT resolved in this session:

- **Report output format** — What does the comparison result look like? File on disk? Console? JSON/CSV/Markdown? What does a human or QA agent need to see?
- **Per-target configuration schema** — We know what fields exist (reader type, header/trailer rows, tier 1/2/3 columns, encoding strictness, line break strictness). What's the config file format? YAML? JSON?
- **CLI interface** — How does a QA agent invoke Proofmark? `proofmark compare --config job_x.yaml`?
- **Evidence package format** — What's the final governance deliverable? How does a comparison report feed into the attestation package?
- **Tolerance specification** — Tier 3 says "within tolerance." How is tolerance defined per column? Absolute? Relative? Percentage?
- **Hash algorithm choice** — MD5? SHA256? Performance vs. collision risk tradeoff.
- **Null handling** — How are nulls treated in hash, comparison, and reporting?
- **Test case design** — The first real SDLC artifact. TDD/BDD cases for Dan to review.
