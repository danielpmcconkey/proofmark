# BRD Revision Log — Session 2026-03-01

This log captures every decision from Dan's annotated BRD review and the subsequent
back-and-forth discussion. A reviewer agent will use this to verify the revised BRD
accounts for every item.

## Status Key
- **DECIDED** — Resolution agreed. Implement in revised BRD.
- **OPEN** — Still under discussion.
- **PARKED** — Acknowledged, deferred to later.

---

## Structural Decisions

### S-1: Split BRD into two documents — DECIDED
- **BRD (cleaned):** Product spec. Generic enterprise language. No AI references, no
  internal platform names, no meta-strategy. What a vendor (Infosys/TCS/etc.) would receive.
- **ATC POC3 Alignment:** Internal doc. How we deploy Proofmark for our use cases,
  AI agent context, CIO narrative, information isolation strategy.
- Sections moving out of BRD → Alignment doc: Section 1 "What Proofmark Proves",
  Section 13 Evidence Package (just reference out-of-scope), Section 14 Test Data Strategy,
  platform-specific commentary throughout, Production Constraint in Section 11.
- Section 16 SDLC: keep in BRD but note it's internal process (since no program team).

### S-2: POC → MVP throughout — DECIDED

### S-3: "Accenture test" → "Portability test" — DECIDED

### S-4: Column tier labels: STRICT / FUZZY / EXCLUDED (not 1/2/3) — DECIDED
- Config YAML, report output, and all documentation use named labels.
- Code can use enums internally.

### S-5: Left/Right terminology (not Source A/B) — DECIDED
- LHS = original output. RHS = output being validated.
- Flows through config schema (source_left / source_right), report, CLI args.
- Standard reconciliation platform language (cf. Intellimatch).

---

## Technical Decisions

### T-1: Hash only STRICT (tier 2) columns for sorting — DECIDED
- EXCLUDED columns: dropped before hashing (existing behavior).
- STRICT columns: hashed for sort ordering.
- FUZZY columns: excluded from hash but preserved for tolerance comparison in diff step.
- Sort groups rows by exact-match content. Within each hash group, diff validates
  FUZZY columns against tolerance.
- This resolves the tolerance-vs-hash paradox Dan flagged.

### T-2: Mismatch row correlation — DECIDED (hybrid approach)
- MVP: Store concatenated unhashed row alongside the hash. Report shows unhashed values.
- Build a deterministic correlation function that handles the easy cases
  (e.g., rows sharing most column values, differing in 1-2 columns).
- Falls back to "unmatched LHS row / unmatched RHS row" when correlation
  confidence is too low.
- Rationale: deterministic logic pays for itself once. QA agent correlation
  costs tokens 70,000 times.
- Full fuzzy matching is vendor-build territory.

### T-3: Config reusability — CLI provides file paths — DECIDED
- Config defines HOW to compare (reader type, column tiers, tolerances, strictness).
- CLI invocation defines WHAT to compare (LHS path, RHS path).
- Example: `proofmark compare --config daily_balance.yaml --left /path/lhs --right /path/rhs`
- Strong language: if a config is changed, you go back to the start date. Config must be
  valid for all as_of dates in the comparison run.

### T-4: Line break mismatch = file-level failure — OPEN (parked)
- Line break mismatch should fail the entire file before comparison starts.
- This is a pre-comparison validation step, not a comparison step.
- Need to discuss: how do you define a "row" when line breaks vary?
- Probably doesn't apply to parquet (binary format). CSV only.
- Parked for dedicated discussion.

### T-5: Header/trailer rows — language fix — DECIDED
- Not "skipping." Separating from data rows, preserving position, comparing as
  literal strings independently from the hash-sort-diff pipeline.
- Both header/trailer comparison and data comparison appear in the report.

### T-6: Parquet null handling — RESOLVED
- Pyarrow enforces the parquet schema. Nulls come back as None, not empty strings.
- Schema is in file metadata. This holds for the POC without a metastore.

### T-7: Duplicate row handling (agent C-2) — DECIDED
- Group by hash, compare group counts. Not sequential walk.
- AAA group: LHS=2, RHS=1 → 1 surplus left. Reports which rows are unmatched.
- BRD must specify grouping algorithm, not just say "multiset."

### T-8: Match percentage formula — REVISED, PENDING DAN CONFIRMATION
- Denominator: total rows across both sides (LHS count + RHS count).
- Numerator: sum of matched rows across both sides. Per hash group,
  matched = min(lhsCount, rhsCount) × 2 (counted on both sides).
- Surplus rows (|lhsCount - rhsCount| per group) are unmatched.
- Rows with a hash unique to one side have 0 matches and count as surplus.
- Match percent = totalMatched / totalRows.
- Report shows per-hash-group breakdown: hash, lhsCount, rhsCount, status
  (MATCH or COUNT_MISMATCH with surplus detail), plus plaintext for non-matches.
- Default threshold 100% means any surplus row = FAIL.
- Dan's intent: duplication problems are honest logic problems, failed with prejudice.
  But match percentage should reflect reality at scale (99.95% for 1 missing row
  out of 10,001, not 0.01%).

### T-9: Control record validation (TAR T-04) — DECIDED
- Proofmark does cross-file comparison ONLY. LHS trailer vs RHS trailer as
  literal strings.
- Proofmark does NOT validate internal consistency (e.g., does the trailer's
  row count match the actual data rows in that file).
- LHS is always source of truth. Humans already certified LHS. Our job is to
  prove RHS reproduces what was certified, not to validate the original.
- Consistent with attestation disclaimer: equivalence, not correctness.
- TAR T-04 description is incorrect / misleading. Should be updated to reflect
  that control record comparison is cross-file, not self-validation.

---

## Content Moves (BRD → ATC POC3 Alignment)

- Section 1 "What Proofmark Proves" block
- Section 2 platform-specific rationale in Out of Scope items (keep the items, move commentary)
- Section 3.1 OFW-specific paragraph about job types
- Section 3.3 "The real platform" references
- Section 3.5 "Critical POC demo point" callout
- Section 9 "During cloud migration" context
- Section 11 Production Constraint block
- Section 13 Evidence Package (entire section → just reference out-of-scope)
- Section 14 Test Data Strategy (entire section)
- Section 17 internal commentary on Salesforce, Synapse, etc.
- Dan's meta comments about the overall POC3 exercise (captured inline)

---

## BRD vs Implementation Boundary (Dan's flags)

- YAML format (Section 6): BRD should state config requirements, not mandate format. YAML is implementation.
- Hash step (Section 4): probably fine as BRD since we reference configurable algorithms.
- CLI syntax (Section 12): BRD should say CLI is acceptable and specify required inputs.
  Actual syntax is implementation.
- stdout default (Section 12): implementation. BRD says "specify output path."
- SDLC flow (Section 16): acknowledged as unusual for BRD, kept because no program team.

---

## Agent Review Findings — Disposition

| Finding | Severity | Disposition |
|---------|----------|-------------|
| C-1: Pass/fail ambiguity | Critical | Addressed by T-1 (hash only STRICT) and T-8 (match formula) |
| C-2: Duplicate row algorithm | Critical | DECIDED — see T-7 |
| M-1: Schema mismatch handling | Major | DECIDED — see T-10 |
| M-2: Row count mismatch formula | Major | DECIDED — see T-8 (revised) |
| M-3: "Normalize" encoding undefined | Major | DECIDED — see T-11 |
| M-4: CSV header/trailer spec | Major | Partially addressed by T-5 |
| M-5: No BDD examples in SDLC | Major | Moot if SDLC section moves to alignment doc |
| m-1: Section numbering | Minor | Will fix in revision |
| m-2: Missing glossary terms | Minor | Will fix (add ADLS, ADF, TIBCO, etc.) or remove platform terms |
| m-3: Informal tone in places | Minor | Will clean up for vendor-facing version |
| m-4: Day-over-day reports (T-06) | Minor | Addressed by T-3 (config reusability + CLI paths) |

---

### T-10: Schema mismatch = automatic fail — DECIDED
- Any schema difference between LHS and RHS is an automatic fail (exit code 1).
- Column count mismatch, column name mismatch, column type mismatch (even
  varchar(200) vs varchar(400) in parquet) — all fail.
- Rationale: even if nothing would be truncated, schema mismatch indicates the
  rewrite changed the output structure. That's a logic problem.

### T-11: Encoding handling — DECIDED
- Encoding detection on CSV is hard (just bytes, no metadata). Parquet embeds it.
- MVP approach: read both files with the same encoding (UTF-8 default, configurable
  in YAML). If a file isn't valid in the configured encoding, exit code 2 (error).
- Don't attempt encoding detection or normalization in the MVP.
- Remove the `encoding: strict | normalize` config option from the MVP. Replace with
  `encoding: utf-8` (configurable to other encodings if needed). Both files read
  with the same encoding setting.
- Encoding detection/normalization is vendor-build territory.

### T-12: Line break mismatch handling — DECIDED (was parking lot T-4)
- Pre-comparison step: check LHS and RHS line break style.
- If different: **automatic fail at file level**, but continue running the full
  comparison. Report shows match rate plus "FAIL — line break mismatch" flag.
- Rationale: team gets the full picture in one pass. They see the line break
  problem AND any other data mismatches. Don't make them fix line breaks,
  re-run, then discover 47 other problems.
- For comparison to proceed: normalize both to a common format internally
  (for row splitting purposes only). The fail flag is already set regardless.
- Applies to CSV only. Parquet is binary format, line breaks not relevant.

### T-13: Build-vs-buy rationale — DECIDED
- Not a BRD item. Goes in ATC POC3 Alignment doc.
- Final pitch will recommend "buy from vendor or commission vendor to build."

## Parking Lot

1. Saboteur agent — chaos monkey for ETL code (POC3 meta, not Proofmark BRD)
