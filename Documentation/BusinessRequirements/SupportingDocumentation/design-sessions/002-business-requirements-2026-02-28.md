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

### 10. Report Output Format: JSON File, One Per Comparison Target

**Two audiences:** QA agent (machine consumer — needs structured data to parse pass/fail) and human reviewer (needs readable summary for governance). JSON serves both: machine-parseable, human-readable enough for a POC.

**Report contents:**
- **Metadata:** timestamp, proofmark version, comparison target name, config file path
- **Config echo:** full config used, embedded so the report is self-contained
- **Column classification:** which columns are tier 1/2/3, with justifications echoed from config
- **Summary:** row counts (source A, source B), match count, mismatch count, match percentage, pass/fail stamp, threshold used
- **Mismatches:** every mismatch — row hash, column name, value A, value B, tier, (for tier 3: tolerance and actual delta)

**What's NOT in the report:**
- Matched rows. Nobody needs 10 million "yep, same" entries. Row counts and match percentage cover it.
- Platform-specific context (job names, OFW IDs, etc.) — not Proofmark's domain.

**Pass/fail logic:**
- Threshold is in the config (e.g., 99.5% match required)
- Report always shows ALL mismatches regardless of pass/fail
- Default threshold: 100% (strict default, consistent with tier 2 default)

**Production constraint (documented, not solved):** In production, mismatch detail with actual cell values is a PII/PCI/SOX problem. The report itself becomes a classified artifact. Production version strips values from mismatch detail — shows row hash, column name, tier, match/fail, but no actual data. Detail goes to a secured location with restricted access. The rest of the report (metadata, summary, classification, stamp) is clean. This is vendor-build territory — the POC includes full values because it makes the exercise faster and nobody's looking at real data.

### 11. Per-Target Configuration Schema: YAML

**Format: YAML.** Supports inline comments (natural place for justifications), less noisy than JSON, human-editable, and Python has native support. QA agents can generate these programmatically just as easily as JSON.

**Schema:**

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
      reason: Floating point rounding between Spark and ADF engines
```

**Design notes:**
- Parquet configs omit the `csv` section entirely. Parquet reader only needs directory paths (source_a, source_b).
- Default-strict philosophy: if you omit `encoding`, `line_breaks`, `threshold`, or `columns`, you get the strictest possible comparison. Relaxation requires explicit config + justification.
- The `reason` field on tier 1 and tier 3 columns flows into the report's column classification section and the evidence package. It's the audit trail.
- No `tier_2` list needed — everything unlisted is tier 2 by default. Listing would be redundant noise.

### 12. CLI Interface: Single Command, Stdout Default

**Invocation:**

```bash
proofmark compare --config path/to/target.yaml
```

One config, one comparison, one report. The config file is the single source of truth — no CLI flags to override config values.

**Output:** JSON report to stdout by default. `--output path/to/report.json` to write to file. Stdout is ideal for agent workflows (pipe it, parse it, move on). File output is for evidence packaging.

**Exit codes:**
- `0` = comparison ran, PASS
- `1` = comparison ran, FAIL
- `2` = error (bad config, file not found, parse failure)

Exit codes let the QA agent script pass/fail without parsing the report.

**What it doesn't have (by design):**
- No verbosity flags. POC runs one way. Verbose/quiet/normal is a vendor NFR.
- No batch mode. Running multiple configs is orchestration, not Proofmark's job.
- No dry-run. Nothing useful to validate without actually running the comparison.

**Production note:** Stdout-default is great for a POC and agent pipelines. A vendor product would likely default to file output with a structured output directory. That's their problem.

### 13. Evidence Package: Not Proofmark's Job

Proofmark produces a comparison report. That report is one *input* to a governance evidence package. Assembly of the evidence package is a QA process concern — human or agent — not a tool concern.

**An evidence package includes things Proofmark has no business knowing about:**
- Which OFW job(s) map to this comparison target
- Business context ("daily balance feed to downstream system X")
- Job owner / SME sign-off
- Proofmark comparison report(s) — linked, not embedded
- Exception approvals (why tier 1 exclusions were accepted)
- Attestation statement ("output equivalence certifies equivalence to original, NOT correctness")

**Why Proofmark's report works as evidence:** It's self-contained. Config echo, column classification with justifications, full mismatch detail, pass/fail stamp. You can drop it into an evidence package and it's interpretable without external context.

**For the POC:** Define what an evidence package looks like conceptually (markdown template or directory structure), but don't build assembly tooling. Proofmark outputs JSON. Packaging is manual for the demo.

### 14. Tolerance Specification: Absolute and Relative, Per Column

**Both types supported, configurable per tier 3 column.** No hardwired defaults on tolerance type — the person configuring it makes a conscious choice and justifies it. An independent tool that bakes in assumptions isn't independent.

**Config:**

```yaml
tier_3:
  - name: interest_accrued
    tolerance: 0.01
    tolerance_type: absolute
    reason: Floating point rounding between Spark and ADF engines

  - name: market_value
    tolerance: 0.001
    tolerance_type: relative
    reason: Rounding variance scales with value magnitude
```

**Rules:**
- `tolerance_type` is **required** on every tier 3 column. No default. Forces explicit, justified choice.
- **Absolute:** `|a - b| <= tolerance`
- **Relative:** `|a - b| / max(|a|, |b|) <= tolerance` — divides by the larger absolute value.
- Both values are 0 → match (zero delta).
- One value is 0, other isn't → math works naturally. `|0 - 0.0001| / max(0, 0.0001) = 1.0` — 100% relative difference, fails any reasonable tolerance. No special case needed.

**No "percentage" type.** Relative with `tolerance: 0.01` *is* 1%. Adding a third label for the same math creates confusion for zero value-add.

### 15. Test Data Strategy: Realistic Variance Between "Original" and "Rewrite"

**The problem:** If MockEtlFramework produces both "original" and "rewritten" outputs using the same libraries, floating point behavior, timestamp formatting, and rounding are identical on both sides. Tier 3 tolerance logic never gets exercised against real variance. The demo would be showing a feature that was never actually stress-tested.

**The decision:** MockEtlFramework must produce original and rewritten outputs using different libraries or settings for specific jobs. This creates the kind of variance that actually shows up during a real migration — where a 500-line PySpark job importing six random libraries gets replaced with clean Spark SQL, and every library has opinions about rounding, null coercion, date formatting, and encoding.

**POC approach — toggle library behavior per job:**
- Job A: `ROUND_HALF_UP` (original) vs. `ROUND_HALF_EVEN` / banker's rounding (rewrite)
- Job B: timestamp precision difference (seconds vs. microseconds)
- Job C: identical output on both sides (exact match happy path)

This gives three demo scenarios: tolerance pass (variance within threshold), tolerance fail (variance exceeds threshold), and exact match. All realistic, all from one framework toggling behavior.

**Why this matters for the CIO deck:** "We tested tolerance comparison against actual library-level variance, not synthetic data" is a much stronger statement than "we tweaked some numbers by hand." It mirrors the real migration challenge — replacing bespoke external modules with standardized Spark SQL and proving the outputs are equivalent within documented tolerances.

### 16. Hash Algorithm: MD5 for POC, Don't Advertise It

**MD5 is the right tool for this job.** It's fast, universally available, and produces excellent distribution for row comparison and sorting. Collision risk is irrelevant — this is a comparison hash, not a security function. Nobody's crafting adversarial ETL outputs.

**The optics problem:** "MD5 bad" is a reflex response from people who learned it in security training without context. It's exhausting and not worth the argument.

**POC approach:** Use MD5. Don't surface the algorithm name in report output. Reports show row hashes for mismatch identification — the algorithm that produced them is an implementation detail. If asked: "it's a comparison hash, not a security function."

**Production:** Make the algorithm configurable. Let the vendor offer SHA256 if it makes compliance happy. It's slower for zero benefit in this use case, but that's their trade-off. The architecture doesn't care — hash is hash, swap the function, pipeline works the same.

### 17. Null Handling: Byte-Level, No Normalization

**Parquet:** Non-issue. Parquet has a typed schema with native null support. Null is null, not empty string, not `"NULL"`. The format enforces it. Two nulls = match. Null vs. empty string = mismatch, correctly, because the schema says they're different things.

**CSV:** This is where it matters. The wild west of null representation:
- Empty field (`,,`)
- Empty quoted string (`,"",`)
- Literal `NULL`, `null`, `\N`, `NA`, `N/A`, `NaN`
- Whitespace (`, ,`)

Every upstream system has its own opinion. If the original wrote `NULL` and the rewrite writes an empty field, that's a **legitimate mismatch**. Downstream systems with brittle parsers treat these differently. Real consequences.

**The rule: byte-level comparison. No null normalization.** `NULL` ≠ `` ≠ `""` ≠ `null`. If the bytes are different, it's a mismatch. Consistent with default-strict philosophy.

The *rewrite process* is responsible for matching the original's null representation. That's an easy fix when Proofmark flags it — cast your nulls to match the expected format. The comparison tool doesn't paper over it.

**Null handling in hash:** No special treatment. Nulls (however represented) are bytes in the row. They hash like everything else. Simplest possible implementation.

### 18. SDLC Flow: BRD Through Code

**Agreed development flow:**

1. **BRD** — Formalize business requirements from design sessions 001 + 002 into a proper document.
2. **Test architecture + BDD scenarios** — What we're testing, acceptance criteria, organized by feature. Given/When/Then against business requirements, not implementation.
3. **Adversarial review** — Gaps in the test plan. What scenarios aren't covered?
4. **Test data management** — Design and generate fixtures that cover the BDD scenarios. Parquet multi-part files, CSVs with trailers, rounding variance (decision 15), null representation mismatches, happy-path exact matches. Test data comes from BDD scenarios, independent of code structure.
5. **FSD** — Modules, interfaces, function signatures, data flow. The code architecture.
6. **UTs** — pytest code written against FSD interfaces, using test data from step 4.
7. **Code** — Make the tests pass.

**Why this ordering:**
- BDD scenarios are testable requirements without implementation assumptions. They bridge business requirements and code.
- Test data and FSD are independent (test data derives from BDD scenarios, FSD derives from BRD) — could be parallel, but sequential is fine for a POC.
- UTs need both the FSD (to know what to call) and test data (to know what to feed it). They come after both.
- Test data fixtures double as demo assets for the CIO presentation.

## Still Open (To Discuss Before Building)

All original open items from this session have been resolved (decisions 10–18). Remaining work is execution per the SDLC flow above. Next artifact: BRD.
