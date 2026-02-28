# BRD Review — Consolidated Record

**Date:** 2026-03-01
**Purpose:** Single source of truth for all review comments, agent findings, decisions, content routing, and open items from the BRD review cycle. A reconciliation agent will use this to verify the revised BRD accounts for every item.

---

## Part 1: Dan's Review Comments

Every `<!-- DAN: ... -->` comment extracted from the annotated BRD (v1.0, 2026-02-28), in document order.

---

### Comment D-01 — Section 1 (Executive Summary), Line 14

**BRD text:** "...when an AI agent rewrites an ETL job, does the rewritten job produce equivalent output to the original?"

**Dan's comment:** not "when an AI agent rewrites...". This is a COTS product from the perspective of the project. "when a technology team rewrites..."

**Resolution:** Addressed by S-1 (split BRD into vendor-facing product spec vs. internal alignment doc). All AI agent references removed from BRD. Generic enterprise language used throughout.

---

### Comment D-02 — Section 1 (Executive Summary), Line 18

**BRD text:** "Proofmark is **not** the production tool. It is a functional specification and architectural proof of concept. The production comparison tool will be built by an independent systems integrator..."

**Dan's comment:** similar comment to the one above. Let's make this BRD and build-out look like a legit product. Not a throw-away tool that some tech lead's using to prove a point. Ideally, my company could give this BRD to the vendor to build as-is.

**Resolution:** Addressed by S-1 and S-2. BRD rewritten as vendor-handoff-ready product spec. POC language replaced with MVP throughout (S-2). Meta-strategy about the POC being a spec for a vendor build moves to ATC POC3 Alignment doc.

---

### Comment D-03 — Section 1 (What Proofmark Proves), Line 24

**BRD text:** "1. **The comparison architecture works.** Format-agnostic engine, pluggable readers, three-tier threshold model, hash-sort-diff pipeline."

**Dan's comment:** I don't like the "comparison architecture works" bit. It's job is to prove like-for-like output within the constraints that are inherit to specific output formats.

**Resolution:** Addressed by S-1. The "What Proofmark Proves" block moves entirely to ATC POC3 Alignment doc. BRD executive summary rewritten to describe the product's purpose generically.

---

### Comment D-04 — Section 1 (What Proofmark Proves), Line 27

**BRD text:** The entire "What Proofmark Proves" block (points 1-3 about comparison architecture, information isolation model, governance story).

**Dan's comment:** I don't know why we're saying all this. This info belongs in some meta document that later Claude strategists read. I want the Claudes that build Proofmark to think they're legit building the tool that a large bank will use to compare outputs from armies of human devs.

**Resolution:** Addressed by S-1. Entire block moves to ATC POC3 Alignment doc.

---

### Comment D-05 — Section 2 (In Scope: Delta Parquet), Line 39

**BRD text:** "**Delta Parquet comparison** — ADLS Delta Parquet part files. This pattern also covers off-platform database outputs (Oracle, SQL Server) and vanilla Salesforce, because those targets are driven by ADF loading a parquet file. The comparison target is the parquet file, not the downstream database or SFDC instance."

**Dan's comment:** this extra flavor makes it sound like bespoke. this needs to read like it's gonna be an Infosys product. We can have a separate document on why Proofmark is a great fit for our project and how we should deploy it for our use cases.

**Resolution:** Addressed by S-1. Platform-specific rationale (ADF, SFDC, Oracle references) moves to ATC POC3 Alignment doc. BRD keeps the in-scope item as generic parquet comparison.

---

### Comment D-06 — Section 2 (In Scope: CSV), Line 40

**BRD text:** "**CSV comparison** — Simple DataFrame-to-CSV dumps (approximately 76% of production output by volume)..."

**Dan's comment:** move the parenthetical 76% bit to that "how it fits" document I describe just above.

**Resolution:** Addressed by S-1. The 76% volume figure is internal deployment context; moves to ATC POC3 Alignment doc.

---

### Comment D-07 — Section 2 (Out of Scope: Database validation), Line 49

**BRD text:** "**Database validation** — PostgreSQL, Oracle, SQL Server, Synapse. Trivial to implement but significant setup work. No value-add to the CIO presentation. DB-out jobs write parquet first anyway; the comparison target is the parquet file."

**Dan's comment:** change the tone to be more like planning an MVP for a COTS product; not what "Dan" wants in a POC.

**Resolution:** Addressed by S-1 and S-2. Out-of-scope items retain the item but strip internal rationale (CIO presentation reference, internal platform details). Commentary moves to ATC POC3 Alignment doc.

---

### Comment D-08 — Section 2 (Out of Scope: Synapse), Line 50

**BRD text:** "**Synapse validation** — Supposed to mirror ADLS Delta 1:1. That rule has been broken approximately 100 times. Ignored during cloud migration."

**Dan's comment:** good to call it out of scope. Move the comments to the "does it fit what we're doing" doc.

**Resolution:** Addressed by S-1. Keep as out-of-scope item in BRD; move commentary to ATC POC3 Alignment doc.

---

### Comment D-09 — Section 2 (Out of Scope: Salesforce), Line 51

**BRD text:** "**Salesforce** — Vanilla SFDC resolves to parquet comparison. Custom SFDC ADF pipelines are application integration, not ETL. Custom SFDC is permanently out of scope."

**Dan's comment:** same comment as the database validation.

**Resolution:** Addressed by S-1. Same treatment as D-07 and D-08.

---

### Comment D-10 — Section 2 (Out of Scope: Exotic MFT), Line 52

**BRD text:** "**Exotic MFT formats** — XML, JSON, EBCDIC, zipped/binary outputs. Approximately 4% of the total job estate. The architecture supports them via pluggable readers, but they are not implemented for the POC."

**Dan's comment:** move the commentary to the "does it fit" doc. Leave the "architecture supports them via pluggable readers" part but cite it as a note for future versions past the MVP.

**Resolution:** Addressed by S-1 and S-2. BRD retains the out-of-scope item with a note about pluggable reader architecture for future versions. Internal volume figures move to alignment doc.

---

### Comment D-11 — Section 2 (Out of Scope: PII/PCI), Line 55

**BRD text:** "**PII/PCI stripping from reports** — Production requirement. The POC runs on synthetic data (see Section 16)."

**Dan's comment:** change the "POC runs on" part to say something like "The MVP will assume that the users who view its outputs have the appropriate entitlements with respect to source data fed into Proofmark, that all data is appropriately classified, and that all privacy agreements are in place."

**Resolution:** Addressed by S-2 (POC to MVP) and Dan's specific language. The BRD should use Dan's exact phrasing about entitlements and data classification rather than referencing synthetic data.

---

### Comment D-12 — Section 2 (POC vs. Production Distinction table), Line 58

**BRD text:** The entire "POC vs. Production Distinction" table header.

**Dan's comment:** change POC to MVP. I know it doesn't fit the content perfectly, but I at least wanna pretend we're designing a COTS product here.

**Resolution:** Addressed by S-2. POC replaced with MVP throughout.

---

### Comment D-13 — Section 3.1 (Comparison Target), Line 78

**BRD text:** The paragraph explaining OFW trigger types: "In the real platform, an OFW trigger can be a single job with one output, a box job producing many outputs in sequence, a job with date-maker logic queuing sequential runs..."

**Dan's comment:** this sounds too bespoke. Move most of it to the why it's a good fit doc. It's good to define the unit of work as an output, but do it in a generic enterprise ETL platform way.

**Resolution:** Addressed by S-1. Platform-specific job type enumeration moves to ATC POC3 Alignment doc. BRD defines comparison target generically as the unit of work (a pair of outputs plus config).

---

### Comment D-14 — Section 3.1 (Comparison Target), Line 82

**BRD text:** "A pair of data sources (original output + rewritten output)"

**Dan's comment:** I want to adopt left / right terminology. Think of this like an enterprise reconciliation platform (Intellimatch). Those terms are used extensively in reconciliation. Left = original job's output. Right = what we're actually validating.

**Resolution:** Addressed by S-5. Left/Right (LHS/RHS) terminology adopted throughout. Flows through config schema (source_left / source_right), report output, and CLI arguments.

---

### Comment D-15 — Section 3.1 (Comparison Target), Line 87

**BRD text:** "The mapping from 'OFW job' to 'comparison targets' is the responsibility of whoever configures Proofmark..."

**Dan's comment:** change OFW to something like IT Task Management. What do we call things like Autosys and Airflow?

**Resolution:** Addressed by S-1. OFW replaced with generic terminology (e.g., "job scheduler" or "orchestration framework"). Platform-specific names removed from BRD.

---

### Comment D-16 — Section 3.1 (The Accenture Test), Line 90

**BRD text:** "**The Accenture test:** If you couldn't sell this tool to another bank running a completely different orchestration framework, you built it wrong."

**Dan's comment:** don't call it Accenture test. Come up with a phrase that evokes TCS, Cognizant, Accenture, Infosys without naming them or calling out "offshore."

**Resolution:** Addressed by S-3. Renamed to "Portability test."

---

### Comment D-17 — Section 3.2 (No Relationships Between Targets), Line 97

**BRD text:** The section describing that Proofmark does not model dependencies between comparison targets.

**Dan's comment:** that was a great call out.

**Resolution:** No action needed. Affirmation, not a change request.

---

### Comment D-18 — Section 3.3 (File vs. File Comparison), Line 106

**BRD text:** "The real platform produces files — parquet files in ADLS and CSV files through TIBCO/ADF."

**Dan's comment:** I don't want the "real platform" reference. this bit belongs in the is it a good fit doc. not the brd you hand to a dev team.

**Resolution:** Addressed by S-1. "The real platform" references and ADLS/TIBCO/ADF names move to ATC POC3 Alignment doc. BRD states the file-vs-file comparison requirement generically.

---

### Comment D-19 — Section 3.3 (File vs. File Comparison), Lines 108-109

**BRD text:**
- "Original job produces a file (parquet or CSV)"
- "Rewritten job produces a file (parquet or CSV)"

**Dan's comment:** "left" / "right"

**Resolution:** Addressed by S-5. LHS/RHS terminology.

---

### Comment D-20 — Section 3.4 (Two Readers: CSV reader config), Line 125

**BRD text:** "Configuration: number of header rows to skip (compared as literal strings, in order), number of trailer rows to skip (compared as literal strings, in order)"

**Dan's comment:** to be clear, we're not skipping those rows. We're preserving their order in the file to ensure they're actually where they belong. but we still hash and compare those rows.

**Resolution:** Addressed by T-5. Language changed from "skip" to "separate from data rows, preserving position, comparing as literal strings independently from the hash-sort-diff pipeline." Both header/trailer comparison and data comparison appear in the report.

---

### Comment D-21 — Section 3.5 (Parquet Part Files), Line 139

**BRD text:** "**Critical POC demo point:** The same output spread across 3 part files must compare correctly against the same output optimized into 1 part file."

**Dan's comment:** I think the Critical POC part is meta info that belongs elsewhere.

**Resolution:** Addressed by S-1. "Critical POC demo point" callout moves to ATC POC3 Alignment doc.

---

### Comment D-22 — Section 4, Step 1 (Load), Line 153

**BRD text:** The Load step description.

**Dan's comment:** The first step should be to understand the config to know how to load. yes, you call that out as first step of load, but reading the config will inform many processes. Not just load. I'm not saying this is wrong. My addition maybe should be an architecture / FSD. It warrants discussion, IMO.

**Resolution:** Dan acknowledges this may be FSD territory rather than BRD. Noted as a BRD-vs-implementation boundary item. The BRD should mention that configuration is read and validated before the pipeline executes, but detailed architecture goes in FSD.

---

### Comment D-23 — Section 4, Step 2 (Exclude), Line 157

**BRD text:** "Drop all tier 1 (excluded) columns. These columns do not exist from this point forward."

**Dan's comment:** have we defined our column tiers yet? If not, that should happen before referencing them.

**Resolution:** Document ordering issue. Column classification (Section 5) is defined after the pipeline (Section 4). In the revised BRD, either reorder sections so column classification comes before the pipeline, or add a forward reference. Also addressed by S-4 (tier labels become STRICT/FUZZY/EXCLUDED, making forward references self-explanatory).

---

### Comment D-24 — Section 4, Step 3 (Hash), Line 164

**BRD text:** "Hash each remaining row (all non-excluded columns) to produce a single hash value per row."

**Dan's comment:** just thinking out loud. But is this a business requirement or an implementation decision? I don't feel strongly enough. We all know that the row will be hashed in either case. And we do reference later versions having selectable hashing algorithms. So I'm probably wasting tokens here.

**Resolution:** Noted as a BRD-vs-implementation boundary item. Conclusion: probably fine in BRD since hashing is core to the comparison approach and future versions reference configurable algorithms. No change needed.

---

### Comment D-25 — Section 4, Step 4 (Sort), Line 172

**BRD text:** The Sort step.

**Dan's comment:** we're missing the part about excluding header and footer rows from the re-shuffling.

**Resolution:** Addressed by T-5. Header and trailer rows are separated before the hash-sort-diff pipeline operates on data rows. They are compared independently as literal strings in order.

---

### Comment D-26 — Section 4, Between Sort and Diff, Lines 173-179

**BRD text:** The transition between Sort and Diff steps.

**Dan's comment (full):** between sort and diff, I think we've missed a major requirement. The reader of the report will need to be able to know which rows didn't match. Imagine this scenario:
- left hand side (LHS) has a row in line 17 that is "123|Big|Bird|Yellow"
- right hand side (RHS) has a row in line 48 that is "123|Big|Burd|Yellow"
- I'm not gonna actually hash those, but the MD5 result of those two will be wildly different
- So the hashed comparison diff will simply see it as the LHS has a row that isn't present in the RHS and the RHS has a row that isn't present in the LHS

It's fine that we don't show them as "the same row but different". But the human reader of the report needs to be able to figure that out by seeing the actual original data un-hashed. So my thought is that we create the LHS as a dataframe of one column that is all columns concatenated into a string (including the delimiter), one column that is a hash of that first column. Do the same for the RHS. Sort both on the hashed column. Compare. Report the unhashed version in the diff.

**Resolution:** Addressed by T-2 (mismatch row correlation, hybrid approach). MVP stores concatenated unhashed row alongside the hash. Report shows unhashed values. Deterministic correlation function handles easy cases (rows sharing most column values, differing in 1-2 columns). Falls back to "unmatched LHS row / unmatched RHS row" when correlation confidence is too low. Full fuzzy matching deferred to vendor build.

---

### Comment D-27 — Section 5 (Column Classification, overall), Line 200

**BRD text:** The entire Column Classification section header area.

**Dan's comment (full, with edits):** overall comment. I think our tiering is backwards. 1 should be exact match. 2 should be "fuzzy". 3 should be ignore. I'll use your numbers in my comments here so I don't confuse. But you want your most important fields to be #1. It's a human thing. We're weird like that. EDIT. After reflecting on it, keep it as-is for this version. I don't wanna risk you missing a change in just one place and suddenly we're excluding things that need to be exact matches. EDIT 2. No, I take that back. I wanna get rid of the 1, 2, 3 designation outright. These should never be numbers. We can make them enums in the code, but they should be meaningful labels, not magic numbers. STRICT, FUZZY, EXCLUDED.

**Resolution:** Addressed by S-4. Tier labels changed from 1/2/3 to STRICT/FUZZY/EXCLUDED. Config YAML, report output, and all documentation use named labels. Code can use enums internally.

---

### Comment D-28 — Section 5 (Tier 1: Excluded), Line 207

**BRD text:** The Tier 1 Excluded definition and the justification requirement.

**Dan's comment:** for the meta "why does this tool fit our need" document. It is important to call out that first pass after rewrite may not notice that a column should be tier 1 or 3. Unless the analyst agent explicitly recognize up front that a column belongs in something other than tier 2, we'll be iterating and will eventually come to that conclusion. Config needs to be changeable with that in mind.

**Resolution:** Addressed by S-1. This is operational deployment context (how agents will iteratively refine configs). Moves to ATC POC3 Alignment doc. The BRD already supports config changeability inherently (configs are YAML files, editable between runs). T-3 reinforces this with config reusability and CLI-provided paths.

---

### Comment D-29 — Section 5 (Tier 3: Tolerance), Line 223

**BRD text:** The Tier 3 tolerance definition.

**Dan's comment:** if we're using a hash, how would we arrive at tolerance. do we cast / round those fields? That won't work. You can round 4.0051 and 4.0049 to 3 significant digits and get very different results, even though they're only 0.0002 apart. This needs discussion, BD.

**Resolution:** Addressed by T-1. FUZZY (tier 3) columns are excluded from the hash. Only STRICT (tier 2) columns are hashed for sort ordering. FUZZY columns are preserved for tolerance comparison in the diff step. Sort groups rows by exact-match content; within each hash group, diff validates FUZZY columns against tolerance. This resolves the tolerance-vs-hash paradox.

---

### Comment D-30 — Section 5 (Tier 3: Tolerance), Line 224

**BRD text:** Adjacent to the tier 3 definition.

**Dan's comment:** comment for the meta exercise, not this BRD. this might be a bridge too far. But I'm wondering about ways to intentionally trip this up. A good example we had from our on-prem to cloud migration was timezones. Our servers ran in UTC. On prem ran in UTC -5. We had oodles of fun with that one. Many ETL jobs truncated full date/time/timezone stamps down to date-only and when jobs run on opposite sides of midnight, that caused interesting results. And floating point math *is* weird. We need to intentionally introduce it. Same with the CSV library differences. I wanna test this process in the meta.

**Resolution:** Addressed by S-1. This is test strategy / meta-POC commentary. Moves to ATC POC3 Alignment doc (relevant to test data strategy, Section 14 of original BRD).

---

### Comment D-31 — Section 6 (Configuration: YAML format), Line 240

**BRD text:** "### Format: YAML"

**Dan's comment:** is this a business requirement or an implementation detail?

**Resolution:** Noted as BRD-vs-implementation boundary item. BRD should state configuration requirements (human-readable, supports inline comments/justifications, machine-parseable, standard format with broad tooling support). Specific format choice (YAML) is implementation. The BRD-vs-implementation boundary notes in the revision log flag this.

---

### Comment D-32 — Section 7 (Tolerance Specification), Line 300

**BRD text:** The tolerance specification section.

**Dan's comment:** as a meta for the overall POC3 project, we need to ensure we're capturing that justification and that it is clearly founded in evidence.

**Resolution:** Addressed by S-1. This is operational deployment guidance (how justifications are reviewed and accepted). Moves to ATC POC3 Alignment doc. The BRD already requires justifications on every FUZZY column config.

---

### Comment D-33 — Section 8 (Null Handling: Parquet), Line 335

**BRD text:** "Non-issue. Parquet has a typed schema with native null support... Two nulls match. Null vs. empty string is a mismatch..."

**Dan's comment:** meta to Claude. How will we actually do this? We're saying "don't worry about it" because parquet enforces its schema. In the real platform, we can make that assumption. In our POC, does that hold water? Parquet is really just a text file. And we're not building anything like delta lake or hive here.

**Resolution:** Addressed by T-6. Pyarrow enforces the parquet schema. Nulls come back as None, not empty strings. Schema is in file metadata. This holds for the POC without a metastore. (Note: Dan's characterization of parquet as "really just a text file" is incorrect -- parquet is a binary columnar format with embedded schema metadata. Pyarrow reads this metadata correctly.)

---

### Comment D-34 — Section 8 (Null Handling: CSV), Line 348

**BRD text:** The CSV null representation paragraph listing various null forms.

**Dan's comment:** this needs to be worded stronger. This isn't javascript where ("two" == 2) returns true. Make no attempt at null equivalence. Make that sound smarter Claude. I don't actually know the right way to phrase it, but this needs a point of emphasis, IMO. Edit. Okay, looks like you added the emphasis down below. But still think on this a bit. make sure we're putting in the right guard rails.

**Resolution:** The BRD already contains the strong rule ("Byte-level comparison. No null normalization.") Dan acknowledged this in his edit. Wording should be tightened further in revision for emphasis: no semantic null equivalence, byte-level comparison only.

---

### Comment D-35 — Section 9 (Line Break and Encoding: Real-World Context), Line 368

**BRD text:** "During cloud migration, encoding and line break mismatches were showstoppers at the start. By the end, the consensus was 'fix your downstream ingestion process to be less brittle.' Proofmark needs to support both stances."

**Dan's comment:** move that commentary to the "does it fit" file. Make this a generic statement about different line breaks and encoding being mother fuckers.

**Resolution:** Addressed by S-1. Migration-specific commentary moves to ATC POC3 Alignment doc. BRD states the requirement generically (line break and encoding differences are common in cross-platform ETL and must be handled explicitly).

---

### Comment D-36 — Section 9 (Line Break Configuration), Line 375

**BRD text:** "**Line breaks:** `strict` (CRLF and LF must match exactly) or `normalize` (treat all line break styles as equivalent)"

**Dan's comment (full):** I mention this above, but how do you compare the line break if you're using that line break to delimit your rows from one another? You'll strip out your breaks by definition before you ever get to the comparin'. There needs to be something in here that evaluates for line break consistency before ever trying to compare the rows. We can continue the hash and compare so that the reviewer knows all the failures they need to deal with. But a line break mismatch should flunk the entire file. no ifs, ands, or buts. I don't think this applies to parquet, but double check that, please.

**Resolution:** Addressed by T-12 (line break mismatch handling). Pre-comparison step checks LHS and RHS line break style. If different: automatic fail at file level, but continue running the full comparison. Report shows match rate plus "FAIL -- line break mismatch" flag. Rationale: team gets the full picture in one pass. They see the line break problem AND any other data mismatches. For comparison to proceed, normalize both internally for row splitting purposes only; the fail flag is already set. Applies to CSV only; parquet is binary, line breaks not relevant.

---

### Comment D-37 — Section 9 (Line Break and Encoding Defaults), Line 384

**BRD text:** "Both default to `strict`. Relaxation requires documented justification."

**Dan's comment:** I don't want to approve normalised line endings as an exception. There should never be a reason we can't write the proper line endings. If our Mock ETL FW can't support "standard" line ending formats, let's fix it to do just that. and for MVP, we can assume standard windows vs *nix. nothing exotic needed here.

**Resolution:** Partially addressed by T-12. Line break mismatch is now an automatic fail regardless of any config option. The `line_breaks: normalize` option is effectively removed as a permissible pass condition. Dan's position is clear: line break mismatches are always failures, no exceptions. The encoding handling is addressed by T-11 (remove strict/normalize option, replace with a single configured encoding, default UTF-8).

---

### Comment D-38 — Section 10 (Hash Algorithm), Line 392

**BRD text:** "**POC:** MD5."

**Dan's comment:** MVP, not POC.

**Resolution:** Addressed by S-2 (POC to MVP throughout).

---

### Comment D-39 — Section 11 (Report Output: Mismatches), Line 432

**BRD text:** "Every mismatch, regardless of pass/fail: row hash, column name, value A, value B, tier"

**Dan's comment (full):** see my note above about how to display value A and value B. Will we even be able to "knit" it together like this? As far as the comparison, the hashes will be wildly different. I'm way good if you think it'll be easy to then look at each of the rows that didn't appear on the other side and try to fuzzy logic your way to "we think these were supposed to be the same row". As a meta on the POC, we're gonna have to build that intelligence into something. Is that in Proofmark or is that in your QA agents? I'd love it to get into proofmark as a deterministic algorithm but need advice on the practicality.

**Resolution:** Addressed by T-2 (mismatch row correlation, hybrid approach). Same resolution as D-26. Deterministic correlation in Proofmark for easy cases, fallback to unmatched listing. Full fuzzy matching is vendor-build territory. Rationale: deterministic logic pays for itself once; QA agent correlation costs tokens 70,000 times.

---

### Comment D-40 — Section 11 (Production Constraint), Line 456

**BRD text:** The entire "Production Constraint (Documented, Not Solved)" subsection about PII/PCI in mismatch detail.

**Dan's comment:** that whole constraint is not needed here. We have it in the out of scope. See my comments on that. Your commentary is useful to the POC3 project but don't belong here. Move them to the "is this a good fit" md.

**Resolution:** Addressed by S-1. Production constraint block moves to ATC POC3 Alignment doc. BRD references PII/PCI handling as out of scope for MVP (per D-11 language about entitlements).

---

### Comment D-41 — Section 12 (CLI Interface: Invocation), Line 468

**BRD text:** The `proofmark compare --config path/to/target.yaml` code block.

**Dan's comment:** this is definitely implementation. BRD should call out that CLI is acceptable and that the executor of that CLI operation needs to be able to provide X, Y, and Z inputs.

**Resolution:** Noted as BRD-vs-implementation boundary item. BRD should specify: CLI interface is the delivery mechanism; required inputs are config path, LHS path, RHS path, and output path. Actual syntax is implementation / FSD.

---

### Comment D-42 — Section 12 (CLI Interface: Invocation), Line 470

**BRD text:** The CLI invocation section.

**Dan's comment:** don't we need it to take in config path, LHS output path, RHS output path. We should also specify that, for CSV output, this needs to be a path to a single file while, for parquet, it needs to be a directory. I think, I haven't actually bothered to truly understand parquet under the hood.

**Resolution:** Addressed by T-3 (config reusability, CLI provides file paths). Config defines HOW to compare. CLI invocation defines WHAT to compare (LHS path, RHS path). Example: `proofmark compare --config daily_balance.yaml --left /path/lhs --right /path/rhs`. BRD should specify input path semantics (CSV = single file, parquet = directory).

---

### Comment D-43 — Section 12 (CLI: Config reusability), Line 474

**BRD text:** "One config, one comparison, one report. The config file is the single source of truth."

**Dan's comment (full):** I disagree and it may highlight a lack of refinement in our discussions. Config should be re-usable. A job creates an output (or many or none, but let's not get mired down in that). That output is an output target that should be matched day over day. We compare LHS tuesday to RHS tuesday. Then LHS wednesday to LHS wednesday. Same config, different file sets. Because, if the config changes day over day, that tells us nothing. We need the EXACT same rigour applied to tuesday as to wednesday, IMO.

**Resolution:** Addressed by T-3. Config separated from file paths. Config defines the comparison standard (reader type, column tiers, tolerances, strictness settings). File paths come from CLI arguments. Strong language added: if a config is changed, you go back to the start date. Config must be valid for all as_of dates in the comparison run.

---

### Comment D-44 — Section 12 (CLI: Output), Line 482

**BRD text:** "JSON report to stdout by default. `--output path/to/report.json` to write to file."

**Dan's comment:** stdout is implementation. the BRD should say that we need to be able to specify an output path when we execute the CLI.

**Resolution:** Noted as BRD-vs-implementation boundary item. BRD should state the requirement: user must be able to specify an output destination. Stdout default vs. file default is implementation.

---

### Comment D-45 — Section 12 (CLI: Exit Codes), Line 492

**BRD text:** The exit codes table (0=PASS, 1=FAIL, 2=Error).

**Dan's comment:** note to future us. the FSD should define discrete error codes. (not exit codes. error codes that would be referenced by the users triaging problems.)

**Resolution:** Parked for FSD. Not a BRD change. Noted as future requirement.

---

### Comment D-46 — Section 13 (Evidence Package), Line 509

**BRD text:** The entire Evidence Package section.

**Dan's comment:** this entire Evidence Package section needs to be moved out of the BRD. it's great commentary on the POC3 project, but not something I'd hand to Tata and say "build this". I believe you've already marked it as out of scope. If not, make sure you do and that's all the BRD needs.

**Resolution:** Addressed by S-1. Entire Evidence Package section moves to ATC POC3 Alignment doc. BRD retains a reference in out-of-scope: evidence package assembly is not a Proofmark concern (Proofmark's scope ends at the comparison report).

---

### Comment D-47 — Section 14 (Test Data Strategy), Line 537

**BRD text:** The entire Test Data Strategy section header.

**Dan's comment:** section 14 also belongs outside the BRD. Good stuff, just not for this document.

**Resolution:** Addressed by S-1. Entire Test Data Strategy section moves to ATC POC3 Alignment doc.

---

### Comment D-48 — Section 14 (Test Data Strategy: The Problem), Line 543

**BRD text:** The paragraph about MockEtlFramework producing both sides with the same libraries.

**Dan's comment (full):** a comment on this specific call out. For our prototype in the actual bank, we'll still be using the same ETL FW to write outputs. The distinction is that some teams employ different tooling in their external modules via python imports. Our re-writes are going to try to eliminate custom module usage (where practical) and replace that flow with standard modules. That's how this problem will manifest for us in the real world execution of this re-write through Claude. I think that's one place where it'll be advisable for us to stop and ask ourselves if maybe we shouldn't edit the ETL FW to make it more versatile for handling these types of differences.

**Resolution:** Addressed by S-1. This is operational deployment context for the POC3 project. Moves to ATC POC3 Alignment doc (test data strategy section).

---

### Comment D-49 — Section 16 (SDLC Flow), Line 585

**BRD text:** The SDLC Flow section header.

**Dan's comment:** this also wouldn't be in a real-world BRD. In a real world dev shop, you'd have program governance documents that all teams adhere to that spell this out. Okay to leave here, though, because we don't have a program team.

**Resolution:** Acknowledged. Per S-1, keep in BRD but note it is internal process documentation (since no program team exists). Dan explicitly approved keeping it.

---

### Comment D-50 — Section 17 (Out of Scope header), Line 612

**BRD text:** "### Out of Scope for POC"

**Dan's comment:** MVP.

**Resolution:** Addressed by S-2 (POC to MVP throughout).

---

### Comment D-51 — Section 17 (Permanently Out of Scope: Custom SFDC), Line 627

**BRD text:** "**Custom Salesforce ADF pipeline** — Application integration, not ETL. Not Proofmark's problem. Recommendation: tell the CIO it is out of scope entirely."

**Dan's comment:** move the custom sf commentary out of the BRD. Good to call out when we're planning on moving out past the prototype. Also soften the "tell the CIO" language. Make it more like "ensure program stakeholders are aware that those workflows are out of scope due to the overwhelming complexity of the custom integration logic."

**Resolution:** Addressed by S-1. Custom SFDC commentary moves to ATC POC3 Alignment doc. BRD retains a clean permanently-out-of-scope entry without internal strategy language. CIO reference replaced with Dan's stakeholder-aware phrasing.

---

### Comment D-52 — Section 18 (Production Considerations), Line 633

**BRD text:** The entire Production Considerations section.

**Dan's comment:** for the entirety of section 18, change POC to MVP. Otherwise good but probably redundant to statements already made.

**Resolution:** Addressed by S-2. POC to MVP. Dan flagged potential redundancy with earlier out-of-scope and MVPvs-production distinction sections. Revision should consolidate or cross-reference to avoid repetition.

---

### Comment D-53 — Appendix A (Decision Traceability), Line 694

**BRD text:** The decision traceability table referencing Design Sessions 001 and 002.

**Dan's comment:** are these design sessions written out somewhere? if not, they should be formalized so readers of this doc can reference them.

**Resolution:** Design sessions exist as files in `Documentation/design-sessions/`. BRD should include explicit file path references or note that design session transcripts are available as companion documents.

---

## Part 2: Fresh-Eyes Agent Review Findings

These findings came from an independent reviewer agent who evaluated the BRD without context on the back-and-forth design discussions. All findings and their dispositions are documented in the revision log.

---

### C-1: Pass/fail ambiguity — CRITICAL

**Finding:** The BRD's pass/fail logic is ambiguous when FUZZY (tier 3) columns are involved. If all rows match on STRICT columns but some FUZZY columns exceed tolerance, is that a PASS or FAIL? The BRD says "match percentage >= threshold with all tier 2 columns exact and all tier 3 columns within tolerance" but does not define how FUZZY column failures interact with match percentage.

**Resolution:** Addressed by T-1 (hash only STRICT columns for sorting) and T-8 (match percentage formula). FUZZY columns are excluded from the hash. Sort groups rows by exact-match content. Within each hash group, diff validates FUZZY columns against tolerance. Match percentage formula uses total rows across both sides as denominator. Any FUZZY tolerance violation within a matched hash group counts as a mismatch for that row.

---

### C-2: Duplicate row algorithm — CRITICAL

**Finding:** The BRD says "multiset comparison" and "row counts matter" but does not specify the algorithm. Sequential walk of hash-sorted data would break if duplicate handling is not defined. How are surplus rows reported?

**Resolution:** Addressed by T-7. Group by hash, compare group counts. Per hash group: matched = min(lhsCount, rhsCount). Surplus = |lhsCount - rhsCount|. Reports which rows are unmatched. BRD must specify grouping algorithm, not just say "multiset."

---

### M-1: Schema mismatch handling — MAJOR

**Finding:** The BRD does not specify what happens when LHS and RHS have different schemas (different column counts, different column names, different column types).

**Resolution:** Addressed by T-10. Any schema difference between LHS and RHS is an automatic fail (exit code 1). Column count mismatch, column name mismatch, column type mismatch (even varchar(200) vs varchar(400) in parquet) -- all fail. Rationale: schema mismatch indicates the rewrite changed the output structure, which is a logic problem.

---

### M-2: Row count mismatch formula — MAJOR

**Finding:** The BRD does not define how match percentage is calculated when LHS and RHS have different row counts.

**Resolution:** Addressed by T-8 (revised formula). Denominator: total rows across both sides (LHS count + RHS count). Numerator: sum of matched rows across both sides. Per hash group, matched = min(lhsCount, rhsCount) x 2 (counted on both sides). Surplus rows (|lhsCount - rhsCount| per group) are unmatched. Rows with a hash unique to one side have 0 matches and count as surplus. Match percent = totalMatched / totalRows. Default threshold 100% means any surplus row = FAIL. Status: REVISED, PENDING DAN CONFIRMATION.

---

### M-3: "Normalize" encoding undefined — MAJOR

**Finding:** The BRD offers `encoding: strict | normalize` but does not define what "normalize" means. Normalize to what? UTF-8? Latin-1? What is the source encoding detection mechanism?

**Resolution:** Addressed by T-11. Remove the `encoding: strict | normalize` config option from the MVP. Replace with `encoding: utf-8` (configurable to other encodings if needed). Both files read with the same encoding setting. If a file is not valid in the configured encoding, exit code 2 (error). Encoding detection/normalization is vendor-build territory.

---

### M-4: CSV header/trailer spec — MAJOR

**Finding:** The BRD says headers and trailers are "skipped" but compared as literal strings. The word "skip" is confusing. Are they removed from the data pipeline and compared separately, or skipped entirely?

**Resolution:** Partially addressed by T-5. Language changed from "skip" to "separate from data rows." Headers and trailers are preserved, their position is maintained, and they are compared as literal strings independently from the hash-sort-diff pipeline. Both header/trailer comparison and data comparison appear in the report. Finding marked as partially addressed because the BRD revision needs to fully integrate this language.

---

### M-5: No BDD examples in SDLC — MAJOR

**Finding:** The SDLC section references BDD scenarios as step 2 but provides no examples of what those scenarios look like.

**Resolution:** Moot if the SDLC section moves to ATC POC3 Alignment doc (per S-1). If SDLC stays in BRD (Dan approved keeping it), BDD examples belong in the test architecture artifact, not the BRD itself.

---

### m-1: Section numbering — MINOR

**Finding:** Section numbers in the BRD are inconsistent or missing in some areas.

**Resolution:** Will fix in revision. Straightforward editorial cleanup.

---

### m-2: Missing glossary terms — MINOR

**Finding:** The glossary references terms like ADLS, ADF, TIBCO, OFW without defining them, but also claims Proofmark does not know about these things.

**Resolution:** Will fix. Either add definitions for platform terms used in context, or (more likely given S-1) remove platform-specific terms from the BRD entirely and move them to the ATC POC3 Alignment doc. The glossary should only contain terms relevant to the vendor-facing product spec.

---

### m-3: Informal tone in places — MINOR

**Finding:** Some BRD language is informal or opinionated in ways that would not appear in a vendor-facing specification (e.g., "The wild west of null representation," "gentleman's agreement everyone interprets differently").

**Resolution:** Will clean up for vendor-facing version. Tone should be professional for a document intended to be handed to a systems integrator.

---

### m-4: Day-over-day reports — MINOR

**Finding:** The BRD does not address how the same comparison target is run across multiple days (e.g., comparing Tuesday's output then Wednesday's output with the same config).

**Resolution:** Addressed by T-3 (config reusability + CLI paths). Config defines HOW to compare; CLI provides WHAT to compare (file paths). Same config, different file paths per day. Strong language: if a config is changed, you go back to the start date.

---

## Part 3: Decisions Made

All decisions from the revision log, with full rationale.

---

### Structural Decisions

#### S-1: Split BRD into two documents — DECIDED

- **BRD (cleaned):** Product spec. Generic enterprise language. No AI references, no internal platform names, no meta-strategy. What a vendor (Infosys/TCS/etc.) would receive to build the tool.
- **ATC POC3 Alignment:** Internal document. How the team deploys Proofmark for their specific use cases, AI agent context, CIO narrative, information isolation strategy.
- **Sections moving out of BRD to Alignment doc:**
  - Section 1 "What Proofmark Proves" block
  - Section 13 Evidence Package (entire section; BRD just references out-of-scope)
  - Section 14 Test Data Strategy (entire section)
  - Platform-specific commentary throughout (OFW, ADF, ADLS, TIBCO, SFDC references)
  - Production Constraint in Section 11
- Section 16 SDLC: keep in BRD but note it is internal process (since no program team).

#### S-2: POC to MVP throughout — DECIDED

All references to "POC" in the BRD are replaced with "MVP." This aligns with the positioning of Proofmark as a legitimate product specification, not a throwaway proof of concept.

#### S-3: "Accenture test" renamed to "Portability test" — DECIDED

The phrase "Accenture test" names a specific vendor and has connotations Dan wants to avoid. "Portability test" evokes the same principle (the tool must be sellable to any organization) without naming firms or implying offshore.

#### S-4: Column tier labels: STRICT / FUZZY / EXCLUDED (not 1/2/3) — DECIDED

- Numeric tier labels (1, 2, 3) are replaced with meaningful names: STRICT (exact match, the default), FUZZY (tolerance match), EXCLUDED (dropped before comparison).
- Config YAML, report output, and all documentation use named labels.
- Code can use enums internally.
- Rationale: Dan's concern that numbered tiers create confusion about priority (humans expect #1 to be most important). Named labels are self-documenting.

#### S-5: Left/Right terminology (not Source A/B) — DECIDED

- LHS = original output (the known-good reference). RHS = output being validated (the rewrite).
- Flows through config schema (`source_left` / `source_right`), report output, and CLI arguments.
- Standard reconciliation platform language (cf. Intellimatch).
- Rationale: aligns with industry-standard reconciliation terminology. "Source A / Source B" is ambiguous about which side is the reference.

---

### Technical Decisions

#### T-1: Hash only STRICT columns for sorting — DECIDED

- EXCLUDED columns: dropped before hashing (existing behavior, no change).
- STRICT columns: hashed for sort ordering.
- FUZZY columns: excluded from hash but preserved for tolerance comparison in the diff step.
- Sort groups rows by exact-match content. Within each hash group, diff validates FUZZY columns against tolerance.
- **Rationale:** Resolves the tolerance-vs-hash paradox Dan flagged (D-29). If FUZZY columns are included in the hash, any tolerance-level difference produces completely different hashes, making row correlation impossible. By hashing only STRICT columns, rows that differ only in FUZZY columns will land in the same hash group and can be compared with tolerance logic.

#### T-2: Mismatch row correlation — DECIDED (hybrid approach)

- MVP: Store concatenated unhashed row alongside the hash. Report shows unhashed values for every row.
- Build a deterministic correlation function that handles the easy cases (e.g., rows sharing most column values, differing in 1-2 columns).
- Falls back to "unmatched LHS row / unmatched RHS row" when correlation confidence is too low.
- Full fuzzy matching is vendor-build territory.
- **Rationale:** Deterministic logic pays for itself once. QA agent correlation costs tokens 70,000 times (one per comparison target across the estate). Even a basic correlation function saves massive downstream effort.

#### T-3: Config reusability — CLI provides file paths — DECIDED

- Config defines HOW to compare: reader type, column tiers, tolerances, strictness settings.
- CLI invocation defines WHAT to compare: LHS path, RHS path.
- Example: `proofmark compare --config daily_balance.yaml --left /path/lhs --right /path/rhs`
- Strong language: if a config is changed mid-run, you go back to the start date. Config must be valid for all as_of dates in the comparison run.
- **Rationale:** Dan's point (D-43) that configs must be reusable day-over-day. Same comparison standard applied to Tuesday and Wednesday. Config changes invalidate prior comparisons.

#### T-4: Line break mismatch = file-level failure — OPEN (parked, then resolved as T-12)

- Original parking lot item. Resolved as T-12 (see below).
- Dan raised: how do you define a "row" when line breaks vary between LHS and RHS?
- Probably does not apply to parquet (binary format). CSV only.
- Was parked for dedicated discussion; that discussion produced T-12.

#### T-5: Header/trailer rows — language fix — DECIDED

- Not "skipping." Separating from data rows, preserving position, comparing as literal strings independently from the hash-sort-diff pipeline.
- Both header/trailer comparison and data comparison appear in the report.
- **Rationale:** Dan's correction (D-20). The word "skip" implies the rows are ignored. They are not ignored -- they are separated and compared differently (literal string match in order, not hash-sort-diff).

#### T-6: Parquet null handling — RESOLVED

- Pyarrow enforces the parquet schema. Nulls come back as `None`, not empty strings.
- Schema is in file metadata. This holds for the MVP without a metastore.
- **Rationale:** Addresses Dan's concern (D-33) about whether parquet null handling holds without Delta Lake or Hive. It does -- pyarrow reads schema metadata from the file itself.

#### T-7: Duplicate row handling — DECIDED

- Group by hash, compare group counts. Not sequential walk.
- Per hash group: matched = min(lhsCount, rhsCount). Surplus = |lhsCount - rhsCount|.
- Example: AAA group has LHS=2, RHS=1. Matched=1, surplus left=1. Report shows which rows are unmatched.
- BRD must specify grouping algorithm, not just say "multiset."
- **Rationale:** Agent finding C-2. The BRD said "multiset comparison" without defining the mechanism. Grouping by hash with count comparison is the concrete algorithm.

#### T-8: Match percentage formula — REVISED, PENDING DAN CONFIRMATION

- Denominator: total rows across both sides (LHS count + RHS count).
- Numerator: sum of matched rows across both sides. Per hash group, matched = min(lhsCount, rhsCount) x 2 (counted on both sides).
- Surplus rows (|lhsCount - rhsCount| per group) are unmatched.
- Rows with a hash unique to one side have 0 matches and count as surplus.
- Match percent = totalMatched / totalRows.
- Report shows per-hash-group breakdown: hash, lhsCount, rhsCount, status (MATCH or COUNT_MISMATCH with surplus detail), plus plaintext for non-matches.
- Default threshold 100% means any surplus row = FAIL.
- **Rationale:** Dan's intent: duplication problems are honest logic problems, failed with prejudice. But match percentage should reflect reality at scale (99.95% for 1 missing row out of 10,001, not 0.01%). The formula produces intuitive percentages.
- **Status note:** Pending Dan's confirmation on the specific formula.

#### T-9: Control record validation — DECIDED

- Proofmark does cross-file comparison ONLY. LHS trailer vs. RHS trailer as literal strings.
- Proofmark does NOT validate internal consistency (e.g., does the trailer's row count match the actual data rows in that file).
- LHS is always source of truth. Humans already certified LHS. Proofmark's job is to prove RHS reproduces what was certified, not to validate the original.
- Consistent with attestation disclaimer: equivalence, not correctness.
- TAR T-04 description is incorrect / misleading. Should be updated to reflect that control record comparison is cross-file, not self-validation.
- **Rationale:** The attestation disclaimer says Proofmark certifies equivalence to the original, not correctness. Self-validation of control records would be validating correctness. Cross-file comparison validates equivalence.

#### T-10: Schema mismatch = automatic fail — DECIDED

- Any schema difference between LHS and RHS is an automatic fail (exit code 1).
- Column count mismatch, column name mismatch, column type mismatch (even varchar(200) vs. varchar(400) in parquet) -- all fail.
- **Rationale:** Agent finding M-1. Even if nothing would be truncated, schema mismatch indicates the rewrite changed the output structure. That is a logic problem, not a data problem.

#### T-11: Encoding handling — DECIDED

- Encoding detection on CSV is hard (just bytes, no metadata). Parquet embeds encoding.
- MVP approach: read both files with the same encoding (UTF-8 default, configurable in config).
- If a file is not valid in the configured encoding, exit code 2 (error).
- Do not attempt encoding detection or normalization in the MVP.
- Remove the `encoding: strict | normalize` config option from the MVP. Replace with `encoding: utf-8` (configurable to other encodings if needed). Both files read with the same encoding setting.
- Encoding detection/normalization is vendor-build territory.
- **Rationale:** Agent finding M-3. "Normalize" was undefined. Rather than define it, remove it. The MVP reads both files with the same encoding. If either file is invalid, it errors out.

#### T-12: Line break mismatch handling — DECIDED (resolves parking lot T-4)

- Pre-comparison step: check LHS and RHS line break style.
- If different: automatic fail at file level, but continue running the full comparison.
- Report shows match rate plus "FAIL -- line break mismatch" flag.
- For comparison to proceed: normalize both to a common format internally (for row splitting purposes only). The fail flag is already set regardless.
- Applies to CSV only. Parquet is binary format, line breaks not relevant.
- **Rationale:** Dan's concern (D-36) about how to detect line break mismatches when line breaks are used to delimit rows. The solution is to detect the mismatch first (pre-comparison step), set the fail flag, then normalize internally so the comparison can still run. Team gets the full picture in one pass: line break problem plus any data mismatches.

#### T-13: Build-vs-buy rationale — DECIDED

- Not a BRD item. Goes in ATC POC3 Alignment doc.
- Final pitch will recommend "buy from vendor or commission vendor to build."
- **Rationale:** Build-vs-buy is program strategy, not product specification.

---

## Part 4: Content Routing

What stays in the BRD, what moves to the ATC POC3 Alignment doc, and what gets dropped.

---

### Stays in BRD (cleaned, vendor-facing)

| Section | Notes |
|---------|-------|
| 1. Executive Summary | Rewritten. Remove "What Proofmark Proves" block, AI agent references, and meta-strategy. Generic enterprise product language. |
| 2. Scope | In-scope items stay but stripped of platform-specific rationale (76% volume, ADF/ADLS/SFDC/TIBCO references). Out-of-scope items stay with generic rationale. MVP vs. Production table stays with POC renamed to MVP. PII/PCI out-of-scope uses Dan's entitlements language (D-11). |
| 3. Core Concepts | 3.1 (Comparison Target) stays, rewritten generically. OFW paragraph moves out. LHS/RHS terminology adopted. Portability test replaces Accenture test. 3.2 (No Relationships) stays as-is. 3.3 (File vs. File) stays, "real platform" reference removed. 3.4 (Two Readers) stays, header/trailer language fixed per T-5. 3.5 (Parquet Part Files) stays, "Critical POC demo point" moves out. |
| 4. Comparison Pipeline | Stays. Updated for T-1 (hash only STRICT), T-5 (header/trailer separation), T-7 (grouping algorithm for duplicates). Column tiers referenced by name (STRICT/FUZZY/EXCLUDED) per S-4. Forward reference or reorder needed per D-23. |
| 5. Column Classification | Stays. Tier labels changed to STRICT/FUZZY/EXCLUDED per S-4. Default-strict philosophy stays. |
| 6. Configuration | Stays. Config requirements stated; YAML choice may be noted as reference implementation. Schema updated for LHS/RHS (S-5), named tiers (S-4), `source_left`/`source_right`, encoding change (T-11). File paths removed from config (T-3). |
| 7. Tolerance Specification | Stays as-is. |
| 8. Null Handling | Stays. Strengthen null-equivalence language per D-34. |
| 9. Line Break and Encoding | Stays but rewritten. Migration commentary moves out (D-35). Encoding handling simplified per T-11. Line break mismatch = automatic fail per T-12. Normalize option removed as a permissible pass condition per D-37. |
| 10. Hash Algorithm | Stays. POC changed to MVP (S-2). |
| 11. Report Output | Stays minus Production Constraint block (moves out per D-40). Mismatch detail updated per T-2 (unhashed row values, correlation). Match percentage formula per T-8. Per-hash-group breakdown added. |
| 12. CLI Interface | Stays but rewritten. Implementation details (exact syntax, stdout default) removed per D-41/D-44. BRD specifies required inputs (config path, LHS path, RHS path, output path) per T-3 and D-42. Exit codes stay. |
| 15. CSV Dialect | Stays as-is (already generic). |
| 16. SDLC Flow | Stays with note that it is internal process documentation (no program team). Dan approved keeping it (D-49). |
| 17. Out of Scope | Stays. POC to MVP (S-2). Platform commentary stripped. Custom SFDC language softened per D-51. |
| 18. Production Considerations | Stays. POC to MVP (S-2). Check for redundancy with earlier sections per D-52. |
| Appendix A | Stays. Add file references for design sessions per D-53. |
| Appendix B (Glossary) | Stays. Remove platform-specific terms (OFW, ADLS, ADF, TIBCO) or define them only if still referenced. Add any new terms introduced by decisions. |

### Moves to ATC POC3 Alignment Doc

| Content | Source Section | Reference |
|---------|---------------|-----------|
| "What Proofmark Proves" block | Section 1 | S-1, D-03, D-04 |
| Information isolation model description | Section 1 | D-04 |
| Platform-specific rationale for in-scope items (ADLS, ADF, SFDC, TIBCO) | Section 2 | D-05, D-06 |
| Internal commentary on out-of-scope items (CIO presentation, cloud migration references) | Section 2 | D-07, D-08, D-09, D-10 |
| 76% CSV volume figure | Section 2 | D-06 |
| OFW-specific job type enumeration | Section 3.1 | D-13 |
| "The real platform" references | Section 3.3 | D-18 |
| "Critical POC demo point" (parquet part files) | Section 3.5 | D-21 |
| Cloud migration encoding/line break context | Section 9 | D-35 |
| Production Constraint block (PII/PCI in report detail) | Section 11 | D-40 |
| Evidence Package (entire section) | Section 13 | D-46, S-1 |
| Test Data Strategy (entire section) | Section 14 | D-47, S-1 |
| Dan's meta comments about iterative column tier refinement | Section 5 | D-28 |
| Dan's meta comments about intentional test sabotage (timezone, floating point, CSV library differences) | Section 5 | D-30 |
| Dan's meta comments about tolerance justification capture | Section 7 | D-32 |
| Dan's meta comments about ETL FW custom module replacement | Section 14 | D-48 |
| Custom SFDC narrative and stakeholder communication | Section 17 | D-51 |
| Build-vs-buy rationale | N/A | T-13 |

### Dropped Entirely

No content is dropped outright. All content either stays in the BRD (cleaned) or moves to the ATC POC3 Alignment doc. Dan's inline meta-comments are captured in this consolidated record and inform the alignment doc but are not reproduced verbatim in either output document.

---

## Part 5: Unresolved / Parking Lot

### Unresolved Items

#### T-8: Match percentage formula — PENDING DAN CONFIRMATION

The formula has been proposed and revised, but Dan has not yet confirmed the specific calculation. The proposed formula:
- Denominator = LHS count + RHS count
- Numerator = sum of (min(lhsCount, rhsCount) x 2) per hash group
- Match percent = totalMatched / totalRows

Awaiting Dan's sign-off on this specific formulation.

#### D-22: Config-before-load pipeline ordering

Dan flagged that config reading should be the first pipeline step, informing all subsequent steps (not just load). He acknowledged this may be FSD territory. Needs a decision: does the BRD mention a config validation step, or is this purely FSD?

#### D-23: Section ordering (column classification before pipeline)

The BRD references column tiers in Section 4 (pipeline) before defining them in Section 5 (column classification). The revised BRD should either reorder these sections or add a forward reference. Not yet decided which approach.

#### D-45: FSD error codes

Dan noted that the FSD should define discrete error codes for user triage (not just CLI exit codes). Parked for FSD phase. Not a BRD change.

#### D-53: Design session formalization

Dan asked whether design sessions are written out and available for reference. They exist in `Documentation/design-sessions/`. The BRD should reference them explicitly. Not yet done.

### Parking Lot

#### Saboteur agent

A chaos monkey for ETL code -- intentionally introducing errors to test Proofmark's detection capabilities. This is POC3 meta-strategy, not a Proofmark BRD item. Noted in revision log parking lot.

#### TAR T-04 description update

T-9 identified that the TAR register entry T-04 (control record validation) is incorrect or misleading. It should be updated to reflect that control record comparison is cross-file (LHS trailer vs. RHS trailer), not self-validation (does the trailer match the data in the same file). This is a TAR register change, not a BRD change.

---

*End of consolidated record.*
