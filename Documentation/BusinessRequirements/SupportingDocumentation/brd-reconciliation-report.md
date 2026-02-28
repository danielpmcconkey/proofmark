# BRD v2 Reconciliation Report

**Date:** 2026-03-01
**Reconciliation Agent:** Claude Opus 4.6
**Source Documents:**
- `brd-review-consolidated.md` — Consolidated review (53 Dan comments, 11 agent findings, all decisions, content routing)
- `BRD-v2.md` — The revised BRD (Version 2.0)
- `brd-revision-log.md` — Decision tracking log
- `BRD.md` — Original annotated BRD v1.0 (reference)

---

## 1. Checklist: Structural Decisions (S-1 through S-5)

### S-1: Split BRD into two documents — PASS

**Evidence:** BRD-v2 body (Sections 1-17 + Appendices) contains no AI agent references, no internal platform names (OFW, ADF, ADLS, TIBCO, Autosys, Oozie, Databricks), no meta-strategy about the POC being a spec for a vendor build, no CIO presentation references. The "Content Moved to ATC POC3 Alignment Document" appendix (lines 687-730) explicitly enumerates 20 items that were relocated, providing a reconciliation trail. Specific removals confirmed:

- "What Proofmark Proves" block: removed from body, listed as moved item #1.
- Section 13 Evidence Package: reduced to a one-line out-of-scope statement (line 543: "Evidence package assembly is **out of scope** for Proofmark").
- Section 14 Test Data Strategy: entirely removed from body, listed as moved item #14.
- Platform-specific commentary: no OFW, ADF, ADLS, TIBCO, SFDC references in body text (confirmed by grep).
- Production Constraint in Section 11: removed, retained as one-line item in Production Considerations (Section 17, line 603-605).
- Section 16 SDLC: kept in BRD with explicit note that it is internal process documentation (line 567: "It is included here because Proofmark's MVP is developed without a formal program team").

### S-2: POC to MVP throughout — PASS

**Evidence:** Grep of BRD-v2 body (lines 1-685) for "POC" returns zero matches in body text. All references use "MVP." Section headers read "In Scope (MVP)" (line 24), "Out of Scope (MVP)" (line 34), "MVP vs. Production Distinction" (line 44), "Out of Scope (MVP)" (line 589). The POC term only appears in the "Content Moved" appendix where it describes what was in v1 — this is appropriate for tracking.

### S-3: "Accenture test" renamed to "Portability test" — PASS

**Evidence:** Line 75: "**The Portability Test:** If you could not sell this tool to another enterprise running a completely different orchestration framework, you built it wrong." No mention of "Accenture" in body text. Content Moved item #6 confirms the rename.

### S-4: Column tier labels: STRICT / FUZZY / EXCLUDED — PASS

**Evidence:** Section 5 (lines 218-248) uses STRICT, FUZZY, EXCLUDED throughout. The configuration schema (lines 277-310) uses `excluded:` and `fuzzy:` keys. Glossary (Appendix B) defines STRICT, FUZZY, EXCLUDED. No references to "tier 1", "tier 2", "tier 3", "tier_1", "tier_2", "tier_3" in body text (confirmed by grep).

### S-5: Left/Right terminology — PASS

**Evidence:** Section 3.6 (lines 127-137) dedicates a subsection to LHS/RHS terminology. Section 3.1 uses "LHS" and "RHS" (line 69). Config schema uses no `source_a`/`source_b` — file paths are CLI-provided per T-3. The CLI section (line 507-508) specifies "--left" and "--right" path arguments. Glossary defines LHS and RHS. No "Source A" or "Source B" or "source_a" or "source_b" references in body text.

---

## 2. Checklist: Technical Decisions (T-1 through T-13)

### T-1: Hash only STRICT columns for sorting — PASS

**Evidence:** Section 4, Step 4 (lines 184-189): "Hash only **STRICT columns** to produce a sort key per row. FUZZY columns are excluded from the hash but preserved for tolerance comparison in the Diff step." Section 5, FUZZY definition (lines 237-238): "FUZZY columns are excluded from the hash computation but preserved for tolerance comparison within hash groups during the Diff step." Decision traceability references T-1 at lines 189 and 651.

### T-2: Mismatch row correlation (hybrid approach) — PASS

**Evidence:** Section 11, "Mismatch row correlation" subsection (lines 462-465): "Proofmark includes a deterministic correlation function that handles common cases — rows sharing most column values but differing in 1-2 columns. When correlation confidence is low, the report falls back to presenting unmatched LHS rows and unmatched RHS rows separately. Full fuzzy matching across all mismatch scenarios is vendor-build territory." The "Mismatch detail" section (line 459) specifies "the unhashed concatenated row content (plaintext)." MVP vs. Production table (line 57) lists "Deterministic function for common cases" vs. "Full fuzzy matching."

### T-3: Config reusability — CLI provides file paths — PASS

**Evidence:** Section 6, "Configuration Defines HOW, Not WHAT" (lines 265-273): "The configuration file defines **how** to compare... It does NOT contain file paths. The CLI invocation provides **what** to compare: LHS path, RHS path. **This separation is critical for reusability.**" Strong language about config changes present (line 271): "If a config changes, go back to the start date and re-run all comparisons with the updated config." Config schema (lines 277-310) contains no file path fields. CLI section (lines 506-509) lists config path, LHS path, RHS path, and output path as required inputs.

### T-4: Line break mismatch = file-level failure — PASS (resolved as T-12)

**Evidence:** The consolidated review and revision log both note T-4 was parked and resolved as T-12. See T-12 below.

### T-5: Header/trailer rows — language fix — PASS

**Evidence:** Section 3.4 (lines 108-111): "number of header rows (separated from data, preserved in position, compared as literal strings in order), number of trailer rows (separated from data, preserved in position, compared as literal strings in order)." The word "skip" does not appear in the CSV reader description. Line 110: "Header and trailer rows are compared as exact literal string matches, in order, independently from the hash-sort-diff pipeline." Line 111: "Both header/trailer comparison results and data comparison results appear in the report."

### T-6: Parquet null handling — PASS

**Evidence:** Section 8, Parquet (lines 358-359): "Non-issue. Parquet has a typed schema with native null support. Null is null — not empty string, not the literal text `"NULL"`. The format enforces this." The concern is addressed implicitly — the BRD states the schema is enforced by the format. The BRD does not need to re-explain pyarrow internals; that is implementation context.

### T-7: Duplicate row handling — PASS

**Evidence:** Section 4, Step 6 Diff (lines 199-208): "Group rows by hash value and compare group counts between LHS and RHS." Specific algorithm: "Hash group exists in both LHS and RHS: Compare counts. If LHS count equals RHS count, all rows in the group are matched. If counts differ, the surplus rows (|lhsCount - rhsCount|) are unmatched. Hash group exists in only one side: All rows in the group are unmatched." Line 206: "If the LHS has 3 identical rows (after EXCLUDED column removal and STRICT column hashing), the RHS must also have exactly 3."

### T-8: Match percentage formula — PASS (with caveat)

**Evidence:** Section 11, "Match Percentage Formula" (lines 467-479): Full formula specified with per-hash-group matched = min(lhsCount, rhsCount) x 2, surplus = |lhsCount - rhsCount|, denominator = LHS count + RHS count, percentage = totalMatched / totalRows. Includes worked example (line 477). Report shows per-hash-group breakdown (line 479).

**Caveat:** The consolidated review (Part 5, line 859) marks T-8 as "PENDING DAN CONFIRMATION." The formula is implemented in BRD-v2, but Dan has not confirmed it. This is correctly flagged as an open item — BRD-v2 includes the formula as proposed, awaiting sign-off.

### T-9: Control record validation — PASS

**Evidence:** Section 11, "Control record comparison" (lines 452-454): "Cross-file comparison only: LHS trailer content vs. RHS trailer content as literal strings. Proofmark does NOT validate internal consistency (e.g., whether a trailer's row count matches the actual data rows within that file). LHS is the source of truth. Proofmark's job is to prove RHS reproduces what was certified, not to validate the original. This is consistent with the attestation disclaimer."

### T-10: Schema mismatch = automatic fail — PASS

**Evidence:** Section 4, Step 2 "Schema Validation" (lines 163-175): "Any schema difference is an **automatic fail** (exit code 1): Column count mismatch, Column name mismatch, Column type mismatch (including precision differences, e.g., varchar(200) vs. varchar(400) in parquet)." Rationale included (line 171). CSV header name validation addressed (line 173). Exit codes table (line 524) includes "including schema mismatch" for exit code 1. Pass/Fail logic (line 493) includes "no schema mismatch" as a pass condition.

### T-11: Encoding handling — PASS

**Evidence:** Section 9 "Encoding Handling" (lines 386-403): "Both files are read using the same encoding. The default encoding is UTF-8. The encoding is configurable." No `strict | normalize` option present. Line 393: "No encoding detection is performed. No encoding normalization is performed." Config schema (line 287) shows `encoding: utf-8`. Production Considerations (lines 627-629) lists "Encoding Detection and Normalization" as vendor-build territory.

### T-12: Line break mismatch handling — PASS

**Evidence:** Section 4, "Pre-Comparison: Line Break Check (CSV Only)" (lines 144-155): "If the line break styles differ: Set a **file-level FAIL flag** ('FAIL — line break mismatch'). Normalize both files to a common line break format internally for row-splitting purposes only. **Continue running the full comparison.**" Line 153: "This step does not apply to parquet (binary format; line breaks are not relevant)." Pass/Fail logic (line 493) includes "no line break mismatch flag (CSV)" as a pass condition. Summary section (line 446) includes "Line break mismatch flag (CSV only, if applicable)."

### T-13: Build-vs-buy rationale — PASS

**Evidence:** No build-vs-buy rationale appears in BRD-v2 body. Content Moved item #19 (line 727) confirms: "Build-vs-buy rationale (T-13) — Not included per revision log decision. Belongs in ATC POC3 Alignment doc."

---

## 3. Checklist: Dan's Comments (D-01 through D-53)

### D-01: "AI agent rewrites" -> "technology team rewrites" — PASS
Line 12: "when a technology team rewrites an ETL job." Content Moved item #17 confirms all AI agent references replaced.

### D-02: Make BRD look like a legit product, not a throw-away POC — PASS
The entire document reads as a vendor-handoff-ready product spec. No "throw-away," no "proving a point" language. Content Moved item #2 confirms the "not the production tool" paragraph was relocated.

### D-03: "Comparison architecture works" -> remove — PASS
"What Proofmark Proves" block absent from body. Content Moved item #1 confirms relocation.

### D-04: "What Proofmark Proves" block -> move to meta doc — PASS
Same as D-03.

### D-05: In-scope parquet — remove bespoke platform rationale — PASS
Line 26: "Delta Parquet part files. The comparison target is the parquet file output, not any downstream database or application instance." No ADLS, ADF, Oracle, SFDC references.

### D-06: CSV — remove 76% volume parenthetical — PASS
Line 27: "Simple CSV file outputs and CSV files with trailing control records." No volume percentage. Content Moved item #3 confirms "76% of production output" relocated.

### D-07: Out-of-scope database validation — COTS product tone — PASS
Line 38: "Implementable but significant setup work. Database-out jobs typically write file output first; compare the file." No CIO presentation reference, no internal platform details.

### D-08: Synapse — keep out-of-scope, move commentary — PASS
Synapse is listed in the Database validation out-of-scope row (line 38) but as a generic item. The detailed "mirror ADLS Delta 1:1, broken ~100 times" commentary is absent from body. Content Moved item #4 and #16 confirm relocation.

### D-09: Salesforce — same treatment as D-07/D-08 — PASS
No "Salesforce" or "SFDC" entries in out-of-scope table. Salesforce was originally listed as a separate out-of-scope item; in v2, vanilla Salesforce resolves to parquet comparison (implicitly covered by parquet being in scope). Custom Salesforce is addressed in Section 16, Permanently Out of Scope (line 595) with generic language. Content Moved item #15 and #16 confirm.

### D-10: Exotic MFT formats — keep pluggable reader note, move commentary — PASS
Line 39: "The architecture supports them via pluggable readers, but they are not implemented for the MVP." No volume percentage ("~4% of estate" removed). Production Considerations (line 623-625) lists "Exotic Format Readers" with pluggable architecture note.

### D-11: PII/PCI — use Dan's entitlements language — PASS
Line 42: "The MVP assumes that users who view Proofmark outputs have appropriate entitlements with respect to source data, that all data is appropriately classified, and that all privacy agreements are in place." This is nearly verbatim Dan's requested language.

### D-12: POC -> MVP in distinction table — PASS
Line 44: "MVP vs. Production Distinction." Table header (line 46): "MVP (Proofmark)."

### D-13: Comparison target — remove bespoke OFW job type enumeration — PASS
Lines 65-66: "In enterprise ETL platforms, orchestration triggers can be single jobs with one output, multi-step workflows producing many outputs in sequence, date-driven batch runs, jobs with sub-tasks spanning multiple compute engines, or jobs registered across federated task management systems." Generic enterprise language; no OFW, ADB, ADF, box job, date maker, curated zone references.

### D-14: Adopt left/right (LHS/RHS) terminology — PASS
Section 3.6 dedicated to LHS/RHS. Used throughout. See S-5.

### D-15: Replace OFW with generic terminology — PASS
Line 73: "orchestrated tasks." No OFW, Autosys, Airflow in body text. Content Moved item #5 confirms.

### D-16: Rename "Accenture test" — PASS
See S-3.

### D-17: "Great call out" (no action needed) — PASS (N/A)
Affirmation. Section 3.2 retained as-is.

### D-18: Remove "real platform" reference from Section 3.3 — PASS
Lines 89-93: "Proofmark compares files to files. There is no database in the comparison loop. LHS: a file output (parquet or CSV), RHS: a file output (parquet or CSV)." No "real platform," no ADLS, no TIBCO/ADF.

### D-19: "original" / "rewritten" -> "left" / "right" — PASS
Lines 91-92: "LHS: a file output" and "RHS: a file output."

### D-20: Header/trailer rows — not skipping, preserving — PASS
See T-5.

### D-21: "Critical POC demo point" -> move to meta doc — PASS
Lines 119-123 retain the functional requirement ("The same output spread across multiple part files must compare correctly against the same output coalesced into fewer part files") without the "Critical POC demo point" callout. Content Moved item #8 confirms.

### D-22: Config-before-load pipeline ordering — PASS (noted as open)
Lines 157-161: Step 1 (Load) describes reading using the configured reader, implying config is already read. BRD-v2 does not add a separate "Step 0: Read Config" step but the pipeline description assumes configuration is available. The consolidated review (Part 5, line 868) correctly identifies this as an open item on the BRD-vs-FSD boundary. The BRD-v2 treatment is appropriate for a BRD — the detailed architecture belongs in the FSD.

### D-23: Section ordering — column classification before pipeline — PARTIAL PASS
Section 4 (Pipeline, line 140) references EXCLUDED columns at Step 3 (line 179) before they are formally defined in Section 5 (line 218). However, Section 2 In Scope (line 28) adds a forward reference: "Per-target configuration of EXCLUDED, STRICT, and FUZZY columns (see Section 5)." Additionally, with named labels (STRICT/FUZZY/EXCLUDED per S-4), the forward reference is self-explanatory — the reader understands what "EXCLUDED" means without needing the formal definition first. The consolidated review's suggested approach of "forward reference" was implemented. Section reordering was not done.

**Note:** This is listed as an open item in the consolidated review (Part 5, line 872). The forward reference approach is a reasonable resolution, but Dan has not explicitly approved it.

### D-24: Hash step — BRD vs. implementation — PASS (N/A)
Dan acknowledged this is probably fine in the BRD. No change was needed. The hash step remains in the pipeline (Section 4, Step 4).

### D-25: Exclude header/footer rows from reshuffling — PASS
Section 4, Step 1 (line 159): "For CSV, this means reading the file, separating header/trailer rows from data rows per configuration." Steps 3-6 operate only on data rows. Header/trailer comparison appears separately in the report (lines 448-451).

### D-26: Mismatch row correlation — unhashed values in report — PASS
See T-2. Line 459: "For unmatched rows: the unhashed concatenated row content (plaintext), enabling the human reviewer to identify which rows differ and why."

### D-27: Column tier labels — STRICT/FUZZY/EXCLUDED — PASS
See S-4.

### D-28: Iterative column tier refinement — move to meta doc — PASS
No operational deployment context about iterative tier refinement in BRD-v2. Content Moved appendix item #... not explicitly enumerated as a separate item, but falls under the general "Dan's meta comments" category. The consolidated review (Part 4, line 842) confirms this moves to the alignment doc.

### D-29: Tolerance-vs-hash paradox — PASS
See T-1. FUZZY columns excluded from hash, compared within hash groups.

### D-30: Intentional test sabotage / timezone / floating point — move to meta doc — PASS
No test sabotage or timezone commentary in BRD-v2 body. Content routing table (consolidated review Part 4, line 845) confirms this moves to ATC POC3 Alignment doc.

### D-31: YAML format — BRD vs. implementation — PASS
Section 6 (lines 254-263): States configuration *requirements* (inline comments, human-readable, human-editable, programmatically generatable, less verbose than JSON). Line 263: "YAML is the reference implementation format. The requirement is structured, commented configuration — not a specific serialization format." This correctly positions YAML as reference implementation, not mandate.

### D-32: Tolerance justification capture — move to meta doc — PASS
No meta-commentary about justification review processes in BRD-v2. The BRD retains the requirement for justifications on FUZZY columns (lines 240-241) — this is the product requirement. The operational guidance about how justifications are reviewed moves to the alignment doc.

### D-33: Parquet null handling — how will we do this? — PASS
See T-6. Section 8 retains the parquet null handling statement. The implementation detail (pyarrow) is not in the BRD, which is correct — it belongs in the FSD.

### D-34: Null equivalence — stronger wording — PASS
Line 374: "**Byte-level comparison. No null equivalence. No null normalization.**" The phrase "No null equivalence" was added (not present in v1, which only had "No null normalization"). This strengthens the wording as Dan requested.

### D-35: Cloud migration line break/encoding context — move to meta doc — PASS
Section 9 contains no "During cloud migration" references, no historical anecdotes. Content Moved items #9, #10, #11 confirm relocation.

### D-36: Line break mismatch = file-level fail — PASS
See T-12.

### D-37: No "normalize" option for line breaks — PASS
Section 9 and the config schema contain no `line_breaks: strict | normalize` option. Line break mismatch is handled as a pre-comparison fail flag (Section 4, lines 144-155), not as a configurable strictness setting.

### D-38: POC -> MVP in hash algorithm section — PASS
Line 408: "**MVP:** MD5." No "POC" in this section.

### D-39: Mismatch display — unhashed values — PASS
See T-2 and D-26.

### D-40: Production Constraint block — move out of BRD — PASS
Section 11 contains no "Production Constraint (Documented, Not Solved)" subsection. PII/PCI is addressed as a one-line out-of-scope item (line 42) and in Production Considerations (lines 603-605). Content Moved item #12 confirms.

### D-41: CLI invocation — implementation vs. BRD — PASS
Section 12 (lines 500-537): Specifies required inputs (config path, LHS path, RHS path, output path) as a requirements list (lines 504-509). Includes a "Reference invocation" (line 512) rather than mandating exact syntax. This appropriately positions the CLI syntax as reference, not specification.

### D-42: CLI needs config path, LHS path, RHS path — PASS
Lines 506-508: "Configuration path," "LHS path" (with CSV = file path, parquet = directory path), "RHS path" (same semantics).

### D-43: Config reusability — same config, different file sets — PASS
See T-3. Section 6 (lines 265-273) dedicates a subsection to this with strong language.

### D-44: stdout is implementation — specify output path — PASS
Line 509: "Output path (optional): Path where the JSON report should be written." No "stdout by default" in the requirements section. The MVP vs. Production table (line 54) says "File output with configurable path" for MVP (changed from v1's "Stdout default, optional file").

### D-45: FSD error codes — parked for FSD — PASS (N/A)
Line 526: "Note: discrete error codes within the error category (distinguishing 'file not found' from 'encoding failure' from 'parse failure') are FSD territory, not BRD." Explicitly acknowledged and parked.

### D-46: Evidence Package section — move out of BRD — PASS
Section 13 (lines 541-545): Reduced to a two-line out-of-scope statement. Full evidence package section content moved. Content Moved item #13 confirms.

### D-47: Test Data Strategy section — move out of BRD — PASS
No Section 14 "Test Data Strategy" in BRD-v2. The section numbering jumps from Section 13 (Evidence Package) to Section 14 (CSV Dialect). Content Moved item #14 confirms entire section relocated.

### D-48: ETL FW custom module replacement commentary — move to meta doc — PASS
No MockEtlFramework references in BRD-v2 body. Content routing (consolidated review Part 4, line 845) confirms this moves to alignment doc.

### D-49: SDLC section — okay to keep, not typical for BRD — PASS
Section 15 "SDLC Flow" retained with explicit justification (line 567): "It is included here because Proofmark's MVP is developed without a formal program team." Internal-specific references cleaned up: "Dan reviews and approves every test case personally" removed. "Test data fixtures double as demo assets for the CIO presentation" removed. "pytest code written against FSD interfaces" simplified to "Tests written against FSD interfaces."

### D-50: "Out of Scope for POC" -> "Out of Scope (MVP)" — PASS
Line 589: "## 16. Out of Scope (MVP)."

### D-51: Custom SFDC — soften "tell the CIO" language — PASS
Line 595: "Program stakeholders should be informed that these workflows are out of scope due to the overwhelming complexity of custom integration logic." This closely matches Dan's requested language. No "tell the CIO" phrasing. Content Moved item #15 confirms.

### D-52: Production Considerations — POC -> MVP, check redundancy — PASS
Section 17 (lines 599-634): Uses "MVP" throughout. Some overlap exists with the MVP vs. Production Distinction table (Section 2) and Out of Scope (Section 16), but cross-referencing is acceptable for a BRD where production considerations are called out separately as vendor requirements. The section adds detail not present in other sections (encoding detection, full mismatch correlation, batch execution specifics).

### D-53: Design session formalization — explicit references — PARTIAL PASS
The decision traceability table (Appendix A, lines 641-663) references "Design Session 001" and "Design Session 002" throughout. Line 664 states dates: "Design Session 001 (2026-02-27)" and "Design Session 002 (2026-02-28)." However, there is no explicit file path to where these sessions are stored (e.g., `Documentation/design-sessions/001-initial-design-2026-02-27.md`). The consolidated review (Part 5, line 880) flags this as an open item: "The BRD should reference them explicitly. Not yet done."

**Gap:** File path references to design session documents are not included.

---

## 4. Checklist: Agent Findings (C-1, C-2, M-1 through M-5, m-1 through m-4)

### C-1: Pass/fail ambiguity with FUZZY columns — PASS
Resolved by T-1 (FUZZY excluded from hash) and the pass/fail logic (line 493): "PASS = match percentage >= threshold with all STRICT columns exact and all FUZZY columns within tolerance, and no line break mismatch flag (CSV), and no schema mismatch." The interaction between FUZZY column failures and match percentage is now clear: FUZZY tolerance violations within a matched hash group count as mismatches, contributing to the match percentage denominator.

### C-2: Duplicate row algorithm — PASS
Resolved by T-7. See T-7 above. Algorithm fully specified in Section 4, Step 6.

### M-1: Schema mismatch handling — PASS
Resolved by T-10. See T-10 above. Full Step 2 "Schema Validation" added to pipeline.

### M-2: Row count mismatch formula — PASS (with caveat)
Resolved by T-8. See T-8 above. Formula fully specified. Same caveat: pending Dan confirmation.

### M-3: "Normalize" encoding undefined — PASS
Resolved by T-11. See T-11 above. `strict | normalize` option removed entirely. Replaced with single configurable encoding.

### M-4: CSV header/trailer spec — PASS
Resolved by T-5. See T-5 above. Language fully changed from "skip" to "separate." The concern that T-5 was only "partially addressed" in the consolidated review (line 602) appears to have been fully resolved in BRD-v2 — the language is clear and complete in Section 3.4.

### M-5: No BDD examples in SDLC — PASS (moot)
The SDLC section stays in the BRD (per D-49), but the consolidated review correctly notes that BDD examples belong in the test architecture artifact, not the BRD. Section 15 does not include BDD examples, which is appropriate — the BRD references BDD scenarios as a step without trying to specify them.

### m-1: Section numbering — PASS
Sections in BRD-v2 are numbered 1-17 plus Appendices A and B plus the Content Moved appendix. Numbering is consistent and sequential. Note: the original Section 14 (Test Data Strategy) and Section 13 (Evidence Package full content) were removed, causing a renumber. New numbering: 1 (Exec Summary), 2 (Scope), 3 (Core Concepts), 4 (Pipeline), 5 (Column Classification), 6 (Configuration), 7 (Tolerance), 8 (Null Handling), 9 (Encoding), 10 (Hash Algorithm), 11 (Report Output), 12 (CLI), 13 (Evidence Package — stub), 14 (CSV Dialect), 15 (SDLC), 16 (Out of Scope), 17 (Production Considerations). Sequential and clean.

### m-2: Missing glossary terms — PARTIAL PASS
Platform-specific terms (OFW, ADLS, ADF, TIBCO) are no longer in the body text, so they no longer need glossary definitions. This correctly resolves the finding. COTS is removed from the glossary (confirmed — not present). New terms introduced by decisions are added: LHS, RHS, hash group, mismatch correlation, Portability test. Content Moved item #20 confirms.

**Minor gap:** The informal language "wild west" and "gentleman's agreement" remain in Sections 8 and 14 respectively (see m-3).

### m-3: Informal tone in places — PARTIAL PASS
Two instances of informal language remain in BRD-v2 body:
- Line 363: "The wild west of null representation" (Section 8)
- Line 551: "'CSV' is not a standard. It is a gentleman's agreement everyone interprets differently" (Section 14)

These are arguably effective writing and add color without being unprofessional. They are not egregiously informal for an internal working document. However, the consolidated review's resolution (line 634) said "Will clean up for vendor-facing version. Tone should be professional for a document intended to be handed to a systems integrator." If the document is intended to be vendor-handoff-ready (per S-1), these should be tightened.

**Verdict:** The finding was partially addressed. The most egregious informal language from v1 (e.g., specific anecdotes, "nobody is crafting adversarial ETL outputs") was cleaned up, but two colorful phrases remain.

### m-4: Day-over-day reports — PASS
Resolved by T-3. See T-3 above. Config reusability and CLI file paths fully address the day-over-day scenario.

---

## 5. Checklist: Content Moves

### Content Flagged for Removal — Verification

| # | Content | Present in BRD-v2 Body? | Status |
|---|---------|------------------------|--------|
| 1 | "What Proofmark Proves" block | No | PASS |
| 2 | "not the production tool" paragraph | No | PASS |
| 3 | Platform-specific in-scope commentary (ADLS, ADF, TIBCO, 76%) | No | PASS |
| 4 | Platform-specific out-of-scope rationale (Synapse mirroring, SFDC ADF, CIO) | No | PASS |
| 5 | OFW-specific orchestration examples | No | PASS |
| 6 | "Accenture test" naming | No (renamed to "Portability test") | PASS |
| 7 | "The real platform" references | No | PASS |
| 8 | "Critical POC demo point" callout | No | PASS |
| 9 | "During cloud migration" context (Section 4) | No | PASS |
| 10 | "During cloud migration" context (Section 9) | No | PASS |
| 11 | `encoding: strict | normalize` and `line_breaks: strict | normalize` options | No | PASS |
| 12 | Production Constraint block (Section 11) | No | PASS |
| 13 | Evidence Package full section | No (stub only) | PASS |
| 14 | Test Data Strategy full section | No | PASS |
| 15 | "Tell the CIO" language | No | PASS |
| 16 | Platform-specific out-of-scope commentary (Section 17) | No | PASS |
| 17 | "AI agent rewrites" references | No | PASS |
| 18 | Named internal platform references (OFW, ADF, ADLS, TIBCO, Databricks, Autosys, Oozie) | No | PASS |
| 19 | Build-vs-buy rationale | No | PASS |
| 20 | Glossary entries for OFW, COTS | No | PASS |

**Result: 20/20 PASS.** All content flagged for removal is absent from BRD-v2 body.

### Content Flagged to Stay — Verification

| Content | Present in BRD-v2? | Status |
|---------|-------------------|--------|
| Executive Summary (cleaned) | Yes (Section 1) | PASS |
| Attestation Disclaimer | Yes (Section 1, lines 16-18) | PASS |
| Scope (In-scope, out-of-scope, MVP vs Production table) | Yes (Section 2) | PASS |
| Core Concepts (3.1-3.6) | Yes (Section 3) | PASS |
| Comparison Pipeline (with new steps) | Yes (Section 4) | PASS |
| Column Classification (named tiers) | Yes (Section 5) | PASS |
| Configuration | Yes (Section 6) | PASS |
| Tolerance Specification | Yes (Section 7) | PASS |
| Null Handling | Yes (Section 8) | PASS |
| Encoding Handling (simplified) | Yes (Section 9) | PASS |
| Hash Algorithm | Yes (Section 10) | PASS |
| Report Output (expanded) | Yes (Section 11) | PASS |
| CLI Interface (requirements-focused) | Yes (Section 12) | PASS |
| Evidence Package (stub) | Yes (Section 13) | PASS |
| CSV Dialect | Yes (Section 14) | PASS |
| SDLC Flow (with internal process note) | Yes (Section 15) | PASS |
| Out of Scope (MVP) | Yes (Section 16) | PASS |
| Production Considerations (MVP language) | Yes (Section 17) | PASS |
| Appendix A: Decision Traceability | Yes | PASS |
| Appendix B: Glossary | Yes | PASS |
| Portability test concept | Yes (Section 3.1, line 75) | PASS |
| Default-strict philosophy | Yes (Section 5, lines 243-247) | PASS |
| Pluggable reader architecture note for exotic formats | Yes (Section 2 line 39, Section 17 line 623-625) | PASS |

**Result: 23/23 PASS.** All content flagged to stay is present.

---

## 6. Gaps Found

### Gap 1: Design session file path references (D-53) — MINOR
**Status:** Open item, not resolved.
**Detail:** Appendix A references "Design Session 001" and "Design Session 002" with dates but no file paths. The consolidated review explicitly flags this as unresolved (Part 5, line 880). The BRD should include a note like: "Design session transcripts are available at `Documentation/design-sessions/`."

### Gap 2: Informal tone remnants (m-3) — MINOR
**Status:** Partially addressed.
**Detail:** "The wild west of null representation" (Section 8, line 363) and "a gentleman's agreement everyone interprets differently" (Section 14, line 551) remain. If the document is intended for vendor handoff, these should be professionalized.

### Gap 3: T-8 match percentage formula — pending confirmation — NOT A GAP (documented open item)
**Status:** Correctly flagged in BRD-v2 and consolidated review as awaiting Dan's sign-off. The formula is implemented as proposed; it needs approval, not a revision.

### Gap 4: CSV Dialect section — residual v1 reference — MINOR
**Status:** Section 14 (CSV Dialect, line 557) uses the phrase "must be addressed by the **vendor build**" — this is generic enough, but the production requirement subsection header (line 558) says "Production Requirement" which is consistent with the BRD-v2 approach. No issue here on reflection.

### Gap 5: Synapse as separate out-of-scope item — OBSERVATION
**Status:** In v1, Synapse was a separate out-of-scope entry. In v2, it is folded into "Database validation (PostgreSQL, Oracle, SQL Server, Synapse)" as a single row. This is arguably cleaner and more vendor-appropriate (Synapse is just another database). The consolidation is consistent with S-1's goal of removing platform-specific rationale. No gap.

### Gap 6: Vanilla Salesforce out-of-scope entry — OBSERVATION
**Status:** In v1, Vanilla Salesforce was a separate out-of-scope entry ("resolves to parquet comparison"). In v2, this entry is removed. This is correct — if vanilla Salesforce resolves to parquet comparison and parquet is in scope, there is nothing to call out as out-of-scope. The Custom Salesforce (application integration) case is handled in Section 16, Permanently Out of Scope. No gap.

### Gap 7: "QA agent" reference in body text — MINOR
**Status:** Line 73 uses "the QA team or human operator." The term "QA agent" (which could imply an AI agent) was replaced with "QA team" — this is appropriate. However, v1 Section 11 had "the QA agent (machine consumer needing structured data to parse pass/fail)" — in v2 (line 422), this became "the automated workflow (machine consumer needing structured data to parse pass/fail)." This is a clean change, consistent with S-1. No gap.

### Gap 8: Section ordering (D-23) not formally resolved — OBSERVATION
**Status:** The consolidated review lists this as an open item. BRD-v2 uses a forward reference in Section 2 ("see Section 5") and self-explanatory named labels. This is a pragmatic resolution but Dan has not explicitly approved the approach.

---

## 7. Summary

### Pass/Fail Counts

| Category | Total | PASS | PARTIAL PASS | FAIL | N/A |
|----------|-------|------|--------------|------|-----|
| Structural Decisions (S-1 to S-5) | 5 | 5 | 0 | 0 | 0 |
| Technical Decisions (T-1 to T-13) | 13 | 13 | 0 | 0 | 0 |
| Dan's Comments (D-01 to D-53) | 53 | 49 | 2 | 0 | 2 |
| Agent Findings (C/M/m) | 11 | 8 | 2 | 0 | 1 |
| Content Moves (Removals) | 20 | 20 | 0 | 0 | 0 |
| Content Moves (Retentions) | 23 | 23 | 0 | 0 | 0 |
| **TOTAL** | **125** | **118** | **4** | **0** | **3** |

### Partial Passes (items requiring attention)

1. **D-23 (Section ordering):** Forward reference approach implemented but not formally approved by Dan. Open item.
2. **D-53 (Design session file paths):** References exist by name and date but no file paths. Open item per consolidated review.
3. **m-2 (Glossary):** Platform terms correctly removed, but residual informal language in Sections 8 and 14 blurs with m-3.
4. **m-3 (Informal tone):** Two instances remain ("wild west," "gentleman's agreement"). Should be cleaned up for vendor handoff.

### Documented Open Items (not gaps — correctly flagged)

1. **T-8 match percentage formula:** Pending Dan confirmation. Formula is in the BRD as proposed.
2. **D-22 config-before-load ordering:** BRD-vs-FSD boundary item. Appropriately deferred.
3. **D-45 FSD error codes:** Parked for FSD phase.
4. **D-23 section ordering:** Forward reference implemented, awaiting approval.
5. **D-53 design session file paths:** Not yet added.

### Confidence Assessment

**High confidence.** BRD-v2 accounts for every structural decision, every technical decision, and the vast majority of Dan's 53 inline comments. Content routing was executed cleanly — all 20 items flagged for removal are absent from the body, all 23 items flagged to stay are present, and a "Content Moved" appendix provides a complete audit trail. The four partial passes are minor editorial items, not structural or technical gaps.

### Recommendation

**APPROVE with minor revisions:**

1. Add file path references for design sessions in Appendix A (D-53). One sentence.
2. Clean up "wild west" and "gentleman's agreement" phrasing for vendor-facing tone (m-3). Two edits.
3. Optionally, confirm or note Dan's approval of the forward-reference approach for column classification ordering (D-23).

None of these items affect the technical content, decision implementation, or structural integrity of the document. The BRD-v2 is ready for Dan's review with these three flagged items.
