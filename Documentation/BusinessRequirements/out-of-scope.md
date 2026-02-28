# Proofmark — Out of Scope

## Out of Scope for Weekend (2026-02-27 to 2026-03-02)

### Database Validation (PostgreSQL, Oracle, SQL Server, Synapse)
- Dan's assessment: trivial to implement but a lot of setup work in the sandbox
- No value-add to the CIO presentation at this stage
- Synapse specifically was punted during cloud migration (validated ADLS Delta, tested Synapse sync separately via traditional QA)
- **Revisit:** When moving to production pilot. DB comparison is a natural extension of the parquet reader since DB-out jobs write parquet first anyway.

### Salesforce (Vanilla or Custom)
- Vanilla SFDC uses same ADF parquet pattern — resolves to parquet comparison in theory
- Custom SFDC pipeline is application integration, not ETL. Recommend telling CIO it's out of scope entirely.
- **Revisit:** Vanilla SFDC when parquet comparison is proven in production. Custom SFDC — never, unless forced.

### Synapse Validation
- Supposed to mirror ADLS Delta 1:1. Rule broken ~100 times.
- Ignored during cloud migration. Future problem.
- **Revisit:** After ADLS Delta comparison is battle-tested.

### Exotic MFT Formats
- XML, JSON, EBCDIC, zipped/binary outputs
- ~4% of total job estate
- Architecture supports them via pluggable readers, but not implementing this weekend
- **Revisit:** After CSV and parquet readers are solid. EBCDIC may require specialist knowledge (or a very patient Claude).

### FUZZY Classification on Non-Numeric Columns
- Currently FUZZY only makes sense for numeric types (absolute/relative tolerance is arithmetic).
- Future consideration: trim-before-compare on string columns would be useful for trailing whitespace from different CSV writers.
- **Revisit:** Post-MVP. If added, would need a new tolerance_type (e.g., "trim" or "normalize_whitespace") and config validation to reject absolute/relative on string types.

## Permanently Out of Scope
- Custom Salesforce ADF pipeline — not ETL, not our problem
