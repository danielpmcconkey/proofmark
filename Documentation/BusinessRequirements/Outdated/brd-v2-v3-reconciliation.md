# BRD v2 to v3 Reconciliation Report

**Date:** 2026-02-28
**Agent:** Claude Opus 4.6 (Reconciliation Agent)
**Purpose:** Prove that BRD-v3.md captured everything from BRD-v2.md, with no content lost, mangled, rephrased, or reordered.

---

## 1. Content Preservation Check

**Method:** Stripped all `**[BR-X.Y]**` tags from v3, then ran a full diff against v2. Only two differences emerged:

| Difference | Location | Assessment |
|---|---|---|
| Version number `2.0` -> `3.0` | Line 3 | **Expected.** Version bump. |
| Appendix A traceability table restructured | Lines 641-669 | **Expected.** Table gained a `BR ID Range` column and new rows. Analyzed in detail below. |

### Section-by-Section Prose Comparison

| Section | Status | Notes |
|---|---|---|
| 1. Executive Summary | **PASS** | Identical prose. BR-1.1 inserted before existing text. |
| 2. Scope (all subsections) | **PASS** | Identical prose in In Scope, Out of Scope table, MVP vs. Production table. BR IDs inserted on In Scope bullet items only. |
| 3.1 Comparison Target | **PASS** | Identical prose. |
| 3.2 No Relationships Between Targets | **PASS** | Identical prose. |
| 3.3 File vs. File Comparison | **PASS** | Identical prose. |
| 3.4 Two Readers | **PASS** | Identical prose. |
| 3.5 Parquet Part Files | **PASS** | Identical prose. |
| 3.6 LHS / RHS Terminology | **PASS** | Identical prose. |
| 4. Comparison Pipeline (all steps) | **PASS** | Identical prose across Pre-Comparison, Steps 1-7. All rationale paragraphs preserved unchanged. |
| 5. Column Classification (all subsections) | **PASS** | Identical prose. |
| 6. Configuration (all subsections) | **PASS** | Identical prose. YAML code block, Design Notes block all preserved verbatim. |
| 7. Tolerance Specification | **PASS** | Identical prose including evidentiary language. |
| 8. Null Handling | **PASS** | Identical prose. |
| 9. Encoding Handling | **PASS** | Identical prose. |
| 10. Hash Algorithm | **PASS** | Identical prose including "irrelevant to the business outcome" phrasing. |
| 11. Report Output (all subsections) | **PASS** | Identical prose. Match Percentage Formula, example, Pass/Fail Logic all preserved. |
| 12. CLI Interface | **PASS** | Identical prose including stdout default language. |
| 13. Evidence Package | **PASS** | Identical prose. |
| 14. CSV Dialect | **PASS** | Identical prose. |
| 15. SDLC Flow | **PASS** | Identical prose. (No BR IDs added -- see Section 2 findings.) |
| 16. Out of Scope (MVP) | **PASS** | Identical prose. |
| 17. Production Considerations | **PASS** | Identical prose. No BR IDs added (correct -- these are vendor-build notes). |
| Appendix A: Decision Traceability | **MODIFIED** | Table restructured with BR ID Range column. See Section 5 for detailed analysis. |
| Appendix B: Glossary | **PASS** | Identical prose. No BR IDs (correct -- definitions, not requirements). |
| Content Moved section | **PASS** | All 20 items identical. |

**Content Preservation Verdict: PASS.** Zero words changed, removed, added, or reordered in the document body (excluding version number and Appendix A table structure).

---

## 2. BR ID Audit

### Total Count: 128 unique BR IDs

Every BR ID appears exactly once in the document. No duplicates.

### Complete BR ID Inventory

| BR ID | Summary |
|---|---|
| BR-1.1 | Output equivalence certifies equivalence to original, not absolute correctness |
| BR-2.1 | Delta Parquet comparison is in scope |
| BR-2.2 | CSV comparison (including trailing control records) is in scope |
| BR-2.3 | Three-tier column classification is in scope |
| BR-2.4 | Hash-sort-diff pipeline is in scope |
| BR-2.5 | JSON comparison reports (one per target) is in scope |
| BR-2.6 | Per-target configuration with default-strict and justification requirements |
| BR-2.7 | CLI interface with config path, LHS/RHS paths, optional output, exit codes |
| BR-3.1 | Comparison target definition (pair of data sources + column config + reader config) |
| BR-3.2 | Portability test: no platform-specific knowledge |
| BR-3.3 | No dependency modeling between comparison targets |
| BR-3.4 | Individual targets produce individual reports |
| BR-3.5 | File vs. file comparison; no database in the loop |
| BR-3.6 | Two reader types: parquet and CSV |
| BR-3.7 | Parquet reader input: directory path containing part files |
| BR-3.8 | Parquet reader reads all *.parquet files in directory |
| BR-3.9 | Parquet reader assembles into one logical table |
| BR-3.10 | CSV reader input: file path |
| BR-3.11 | CSV reader config: number of header/trailer rows |
| BR-3.12 | Data between header and trailer goes through hash-sort-diff pipeline |
| BR-3.13 | Header/trailer rows compared as exact literal strings in order |
| BR-3.14 | Both header/trailer and data comparison results in report |
| BR-3.15 | Parquet reader assembles all part files, comparison is order-independent |
| BR-3.16 | Multi-part vs. coalesced part files must compare correctly |
| BR-3.17 | LHS definition: original output, source of truth |
| BR-3.18 | RHS definition: output being validated |
| BR-4.1 | Pre-comparison line break check for CSV files |
| BR-4.2 | Line break mismatch sets file-level FAIL flag |
| BR-4.3 | Normalize line breaks internally for row-splitting only |
| BR-4.4 | Continue running full comparison after line break mismatch |
| BR-4.5 | Report includes both match rate and line break mismatch flag |
| BR-4.6 | Line break check does not apply to parquet |
| BR-4.7 | Load step: read both sources using configured reader |
| BR-4.8 | Both files read with same encoding (UTF-8 default); exit code 2 on encoding failure |
| BR-4.9 | Schema validation: any schema difference is automatic fail (exit code 1) |
| BR-4.10 | Column count mismatch is schema fail |
| BR-4.11 | Column name mismatch is schema fail |
| BR-4.12 | Column type mismatch (including precision) is schema fail |
| BR-4.13 | CSV schema validation: column count and header names when configured |
| BR-4.14 | Exclude step: drop all EXCLUDED columns before hashing |
| BR-4.15 | Hash step: concatenate all non-excluded columns, store unhashed value |
| BR-4.16 | Hash only STRICT columns for sort key; FUZZY excluded from hash |
| BR-4.17 | Sort both datasets by hash value; deterministic ordering |
| BR-4.18 | Diff step: group by hash value, compare group counts |
| BR-4.19 | Hash group in both sides: compare counts, surplus is unmatched |
| BR-4.20 | Hash group in one side only: all rows unmatched |
| BR-4.21 | Validate FUZZY columns within hash groups against tolerances |
| BR-4.22 | Multiset comparison: row counts per hash group matter |
| BR-4.23 | All mismatches reported regardless of pass/fail |
| BR-5.1 | Three-tier column classification; every column in exactly one tier |
| BR-5.2 | EXCLUDED: non-deterministic columns dropped before hashing |
| BR-5.3 | EXCLUDED columns require documented justification |
| BR-5.4 | STRICT: byte-level exact match, no tolerance |
| BR-5.5 | STRICT is the default for any unclassified column |
| BR-5.6 | FUZZY: configurable tolerance (absolute/relative) |
| BR-5.7 | FUZZY columns excluded from hash, compared within hash groups |
| BR-5.8 | FUZZY classification requires justification + explicit tolerance value and type |
| BR-5.9 | Default-strict: no config means every column is STRICT |
| BR-5.10 | Burden of proof on relaxing the standard, not tightening |
| BR-6.1 | Configuration must support inline comments |
| BR-6.2 | Configuration must be human-readable and human-editable |
| BR-6.3 | Configuration must be programmatically generatable |
| BR-6.4 | Configuration must be less verbose than JSON |
| BR-6.5 | YAML is reference implementation format |
| BR-6.6 | Configuration defines HOW to compare (no file paths) |
| BR-6.7 | CLI provides WHAT to compare (LHS/RHS paths) |
| BR-6.8 | Config/path separation critical for reusability |
| BR-7.1 | Two tolerance modes per FUZZY column; no hardwired defaults |
| BR-7.2 | Absolute tolerance: \|lhs - rhs\| <= tolerance |
| BR-7.3 | Relative tolerance: \|lhs - rhs\| / max(\|lhs\|, \|rhs\|) <= tolerance |
| BR-7.4 | Edge case: both values 0 = match |
| BR-7.5 | Edge case: one value 0, other not = math works naturally |
| BR-7.6 | tolerance_type is required on every FUZZY column |
| BR-7.7 | tolerance value required with evidentiary justification |
| BR-7.8 | No "percentage" type; relative tolerance IS percentage |
| BR-8.1 | Parquet nulls: native null support, no ambiguity |
| BR-8.2 | Byte-level comparison; no null equivalence or normalization |
| BR-8.3 | Rewrite process responsible for matching null representation |
| BR-8.4 | Nulls hash like everything else; no special treatment |
| BR-9.1 | Both files read with same encoding; UTF-8 default; configurable |
| BR-9.2 | Invalid encoding = exit with error (exit code 2) |
| BR-9.3 | No encoding detection or normalization |
| BR-9.4 | LHS and RHS always read with same encoding |
| BR-9.5 | Encoding mismatches are a rewrite problem |
| BR-10.1 | MVP hash: MD5 (comparison hash, not security) |
| BR-10.2 | Algorithm name not surfaced in report output |
| BR-11.1 | JSON format; one report per target; machine-parseable and human-readable |
| BR-11.2 | Report metadata: timestamp, version, target name, config path |
| BR-11.3 | Config echo: full configuration embedded in report |
| BR-11.4 | Column classification in report with justifications |
| BR-11.5 | Summary: row counts, match count/percentage, pass/fail stamp, threshold |
| BR-11.6 | Header/trailer comparison results (CSV only) |
| BR-11.7 | Control record comparison: LHS trailer vs. RHS trailer as literal strings |
| BR-11.8 | No internal consistency validation (trailer row count vs. actual data rows) |
| BR-11.9 | Mismatch detail: every mismatch with hash group breakdown |
| BR-11.10 | Mismatch row correlation: deterministic function for common cases |
| BR-11.11 | Fallback to separate unmatched LHS/RHS rows when confidence is low |
| BR-11.12 | Full fuzzy matching is vendor-build territory |
| BR-11.13 | Match percentage formula definition |
| BR-11.14 | Per hash group: matched = min(lhsCount, rhsCount) x 2 |
| BR-11.15 | Surplus per group: \|lhsCount - rhsCount\| |
| BR-11.16 | Rows unique to one side contribute 0 matches |
| BR-11.17 | Total rows: LHS count + RHS count |
| BR-11.18 | Match percentage: totalMatched / totalRows |
| BR-11.19 | Report shows per-hash-group breakdown |
| BR-11.20 | Matched rows NOT in report |
| BR-11.21 | Platform-specific context NOT in report |
| BR-11.22 | Threshold is in configuration |
| BR-11.23 | Default threshold: 100.0% |
| BR-11.24 | Report shows ALL mismatches regardless of pass/fail |
| BR-11.25 | PASS conditions: match >= threshold AND STRICT exact AND FUZZY within tolerance AND no line break mismatch AND no schema mismatch |
| BR-11.26 | FAIL: anything else |
| BR-12.1 | CLI: configuration path required |
| BR-12.2 | CLI: LHS path required |
| BR-12.3 | CLI: RHS path required |
| BR-12.4 | CLI: output path optional; stdout when omitted |
| BR-12.5 | One config, one comparison, one report |
| BR-12.6 | Exit code 0: comparison ran, PASS |
| BR-12.7 | Exit code 1: comparison ran, FAIL |
| BR-12.8 | Exit code 2: error (bad config, file not found, encoding failure, parse failure) |
| BR-12.9 | Exit codes enable automated workflow scripting |
| BR-12.10 | No verbosity flags (MVP) |
| BR-12.11 | No batch mode |
| BR-12.12 | No dry-run |
| BR-12.13 | No CLI flags to override config values |
| BR-13.1 | Evidence package assembly is out of scope |
| BR-14.1 | MVP: standard parser, same parser config for both files |
| BR-16.1 | Custom application integration pipelines permanently out of scope |

### Untagged Requirement Statements

**Section 15 (SDLC Flow):** This section contains no BR IDs. v2's Appendix A traced it to Decision 18 (Design Session 002). The section describes a 7-step development process with ordering rationale. Whether these are "requirements" is a judgment call -- they describe a process rather than a product behavior. However, this is the only section that was traced in v2's Appendix A and is now untraced in v3. **This is a gap.**

No other requirement statements were identified as missing BR IDs.

### Incorrectly Tagged Non-Requirement Statements

The following BR IDs tag statements that are arguably design rationale, philosophy, or scope deferrals rather than testable requirements. None are clear errors, but they are worth noting for governance hygiene:

| BR ID | Concern | Severity |
|---|---|---|
| BR-3.2 | Tags the Portability Test -- a design principle, not a functional requirement | Low (reasonable to track as a design constraint) |
| BR-5.7 | Tags the FUZZY hash exclusion rationale -- explains WHY, not WHAT | Low (the "what" is inherent in the explanation) |
| BR-5.10 | Tags a philosophy statement about burden of proof | Low (anchors the default-strict design philosophy) |
| BR-6.8 | Tags the reusability rationale for config/path separation | Low (rationale for BR-6.6/6.7) |
| BR-8.1 | Tags a descriptive statement about parquet null support | Low (implicit requirement: parquet nulls compared natively) |
| BR-11.12 | Tags "vendor-build territory" -- a scope deferral | Low (documents what is NOT required for MVP) |

**Assessment:** These are all defensible tagging choices. Design principles and negative scope boundaries are legitimate governance tracking targets. No items need removal, though a purist might argue BR-5.7 and BR-6.8 are pure rationale.

---

## 3. Numbering Integrity

### Sequential Numbering

| Section | Range | Sequential? | Notes |
|---|---|---|---|
| 1 | BR-1.1 | Yes (single) | |
| 2 | BR-2.1 - BR-2.7 | Yes | 1,2,3,4,5,6,7 |
| 3 | BR-3.1 - BR-3.18 | Yes | 1 through 18, no gaps |
| 4 | BR-4.1 - BR-4.23 | Yes | 1 through 23, no gaps |
| 5 | BR-5.1 - BR-5.10 | Yes | 1 through 10, no gaps |
| 6 | BR-6.1 - BR-6.8 | Yes | 1 through 8, no gaps |
| 7 | BR-7.1 - BR-7.8 | Yes | 1 through 8, no gaps |
| 8 | BR-8.1 - BR-8.4 | Yes | 1 through 4, no gaps |
| 9 | BR-9.1 - BR-9.5 | Yes | 1 through 5, no gaps |
| 10 | BR-10.1 - BR-10.2 | Yes | 1 through 2, no gaps |
| 11 | BR-11.1 - BR-11.26 | Yes | 1 through 26, no gaps |
| 12 | BR-12.1 - BR-12.13 | Yes | 1 through 13, no gaps |
| 13 | BR-13.1 | Yes (single) | |
| 14 | BR-14.1 | Yes (single) | |
| 15 | (none) | N/A | No BR IDs in this section |
| 16 | BR-16.1 | Yes (single) | |

### Section Number Matching

All BR ID section numbers match their actual BRD section numbers. BR-4.x appears in Section 4, BR-11.x appears in Section 11, etc. **No mismatches.**

**Numbering Integrity Verdict: PASS.** No gaps, no duplicates, no section number mismatches.

---

## 4. Dan's Post-v2 Edits Confirmed

| Edit | Location in v3 | Status |
|---|---|---|
| Evidentiary justification language with code/data citation requirement | Section 6, line 316 (Design Notes: "Justifications must be evidentiary -- they must cite specific instances in the data or code...") | **CONFIRMED** -- identical to v2 |
| Evidentiary tolerance value language | Section 7, line 348 (BR-7.7: "The chosen value must be evidentiary -- it must cite specific instances in the data or code that demonstrate the expected variance magnitude...") | **CONFIRMED** -- identical to v2 |
| "irrelevant to the business outcome" phrasing | Section 10, line 412 ("it will be irrelevant to the business outcome -- hash is hash, swap the function, pipeline works the same") | **CONFIRMED** -- identical to v2 |
| stdout default when output path omitted | Section 12, line 509 (BR-12.4: "When omitted, the JSON report is written to standard output. The report format is identical regardless of destination.") | **CONFIRMED** -- identical to v2 |

**Post-v2 Edits Verdict: PASS.** All four edits present and unchanged.

---

## 5. Appendix A Update Check

### Structure Change

v2 Appendix A had 3 columns: `BRD Section | Source Decision | Source`
v3 Appendix A has 4 columns: `BRD Section | Source Decision | Source | BR ID Range`

This is expected -- the column was added to provide BR ID traceability.

### New Rows in v3 (not in v2)

| Row | Justification |
|---|---|
| 1. Executive Summary | BR-1.1 exists in body. **Valid addition.** |
| 2. Scope (In Scope) | BR-2.1 - BR-2.7 exist in body. **Valid addition.** |
| 4. Pipeline: Load | BR-4.7 - BR-4.8 exist in body. **Valid addition.** |
| 4. Pipeline: Exclude | BR-4.14 exists in body. **Valid addition.** |
| 4. Pipeline: Sort | BR-4.17 exists in body. **Valid addition.** |
| 4. Pipeline: Report | BR-4.23 exists in body. **Valid addition.** |
| 13. Evidence Package | BR-13.1 exists in body. **Valid addition.** |
| 16. Out of Scope (Permanent) | BR-16.1 exists in body. **Valid addition.** |

### Rows in v2 Missing from v3

| Row | Issue |
|---|---|
| 15. SDLC Flow (Decision 18, Design Session 002) | **MISSING.** This row was in v2's traceability table and is absent from v3. No BR IDs were assigned to Section 15, so the row was presumably dropped because there was nothing to put in the BR ID Range column. **This is a gap.** |

### BR ID Range Accuracy

| Appendix A Row | Claimed Range | Actual IDs in Body | Match? |
|---|---|---|---|
| 1. Executive Summary | BR-1.1 | BR-1.1 | **Yes** |
| 2. Scope (In Scope) | BR-2.1 - BR-2.7 | BR-2.1 through BR-2.7 | **Yes** |
| 3.1 Comparison Target | BR-3.1 - BR-3.2 | BR-3.1, BR-3.2 | **Yes** |
| 3.2 No Relationships | BR-3.3 - BR-3.4 | BR-3.3, BR-3.4 | **Yes** |
| 3.3 File vs. File | BR-3.5 | BR-3.5 | **Yes** |
| 3.4 Two Readers | BR-3.6 - BR-3.14 | BR-3.6 through BR-3.14 | **Yes** |
| 3.5 Parquet Part Files | BR-3.15 - BR-3.16 | BR-3.15, BR-3.16 | **Yes** |
| 3.6 LHS / RHS | BR-3.17 - BR-3.18 | BR-3.17, BR-3.18 | **Yes** |
| 4. Line Break Pre-Check | BR-4.1 - BR-4.6 | BR-4.1 through BR-4.6 | **Yes** |
| 4. Load | BR-4.7 - BR-4.8 | BR-4.7, BR-4.8 | **Yes** |
| 4. Schema Validation | BR-4.9 - BR-4.13 | BR-4.9 through BR-4.13 | **Yes** |
| 4. Exclude | BR-4.14 | BR-4.14 | **Yes** |
| 4. Hash (STRICT only) | BR-4.15 - BR-4.16 | BR-4.15, BR-4.16 | **Yes** |
| 4. Sort | BR-4.17 | BR-4.17 | **Yes** |
| 4. Diff (group counts) | BR-4.18 - BR-4.22 | BR-4.18 through BR-4.22 | **Yes** |
| 4. Report | BR-4.23 | BR-4.23 | **Yes** |
| 5. Column Classification | BR-5.1 - BR-5.10 | BR-5.1 through BR-5.10 | **Yes** |
| 6. Configuration | BR-6.1 - BR-6.8 | BR-6.1 through BR-6.8 | **Yes** |
| 7. Tolerance Specification | BR-7.1 - BR-7.8 | BR-7.1 through BR-7.8 | **Yes** |
| 8. Null Handling | BR-8.1 - BR-8.4 | BR-8.1 through BR-8.4 | **Yes** |
| 9. Encoding Handling | BR-9.1 - BR-9.5 | BR-9.1 through BR-9.5 | **Yes** |
| 10. Hash Algorithm | BR-10.1 - BR-10.2 | BR-10.1, BR-10.2 | **Yes** |
| 11. Report Output | BR-11.1 - BR-11.26 | BR-11.1 through BR-11.26 | **Yes** |
| 12. CLI Interface | BR-12.1 - BR-12.13 | BR-12.1 through BR-12.13 | **Yes** |
| 13. Evidence Package | BR-13.1 | BR-13.1 | **Yes** |
| 14. CSV Dialect | BR-14.1 | BR-14.1 | **Yes** |
| 16. Out of Scope | BR-16.1 | BR-16.1 | **Yes** |

**All 27 BR ID ranges match exactly.** No range claims IDs that don't exist, and no range is narrower than the actual IDs in the section.

**Appendix A Verdict: PASS with one gap.** BR ID ranges are accurate. One row (Section 15 SDLC Flow) was dropped from the traceability table.

---

## 6. Summary

### Overall Verdict: CONDITIONAL PASS

The document is ready for use pending resolution of one issue.

### Scorecard

| Check | Result | Items |
|---|---|---|
| Content preservation (sections 1-17 + appendices + Content Moved) | **PASS** | 23 sections checked, 0 differences |
| Dan's post-v2 edits present | **PASS** | 4/4 confirmed |
| BR ID count and uniqueness | **PASS** | 128 IDs, all unique |
| Sequential numbering within sections | **PASS** | 15 section groups, no gaps or duplicates |
| Section numbers in BR IDs match actual sections | **PASS** | 128/128 correct |
| Rationale/design notes correctly untagged | **PASS** | All checked (7 rationale blocks, Design Notes block, YAML code block, example paragraph, FSD territory note) |
| Appendix A BR ID ranges accurate | **PASS** | 27/27 ranges match |
| Appendix A row completeness | **FAIL** | Section 15 row dropped |

### Issues Found

**1. Section 15 (SDLC Flow) dropped from Appendix A traceability table.**

v2 had a row: `| 15. SDLC Flow | Decision 18 | Design Session 002 |`

v3 has no corresponding row. Additionally, Section 15 received zero BR IDs.

This is the only traceability gap. The fix is either:
- (a) Add BR IDs to Section 15's requirement-like statements (the 7-step ordering and the "why this ordering" rationale) and add the row back to Appendix A, OR
- (b) Add the row back to Appendix A with an empty BR ID Range and a note that Section 15 describes a development process, not a product requirement, and was intentionally left untagged.

Option (b) is the safer governance choice -- it preserves the traceability chain from v2 while documenting the rationale for no BR IDs.

### Judgment Calls (Not Blocking)

Six BR IDs tag statements that are arguable as design rationale rather than testable requirements (BR-3.2, BR-5.7, BR-5.10, BR-6.8, BR-8.1, BR-11.12). All are defensible. None need action unless Dan wants a stricter "only testable requirements get IDs" policy.

### Total Items Checked

- 23 sections compared for prose preservation
- 128 BR IDs verified for uniqueness, sequential numbering, and section-number accuracy
- 27 Appendix A rows verified for BR ID range accuracy
- 4 post-v2 edits confirmed
- 7+ rationale/design note blocks verified as correctly untagged
- 1 gap identified (Section 15 traceability)

**Bottom line:** The prose is identical. The BR IDs are clean. Fix the Section 15 traceability gap and this is a governance-ready artifact.
