# Proofmark

## What Is This?
A POC stand-in for an independently built output comparison and validation tool
for ETL pipeline governance. Built through traditional SDLC. Python. pytest for TDD/BDD.

**Proofmark is a POC tool, not the production tool.** The production comparison tool
will be built by an independent systems integrator (Infosys/Accenture/equivalent).
Proofmark serves as the functional specification and proof of architecture.
For the full rationale, see the AtcStrategy repo: `AtcStrategy/POC3/scope-and-intent.md`.

## Prime Directive: The TAR Register

**Every decision, every design choice, every implementation task must be checked
against the TAR register at:**
`/workspace/AtcStrategy/AdversarialReviews/06-program-tar-register.md`

This is the governing document for the POC. It contains:
- The weekend POC tasks and priorities
- Response strategies for every adversarial concern raised by CIO, CRO, risk partners, and independent evaluators
- The March 24th narrative arc
- Risks to the POC itself

**Standing orders:**
- Before starting any significant work, check: does this advance a TAR item?
- If Dan and Claude disagree on direction, go back to the TAR register and hash it out against the documented goals.
- If something isn't in the TAR and seems important, flag it — it might need to be added.
- If a TAR item turns out to be wrong or irrelevant, say so. The TAR is a living document, not scripture. But changes are deliberate, not silent.

## Session Startup
1. Read the TAR register (prime directive above).
2. Read `Documentation/BusinessRequirements/BRD-v3-approved.md` — the approved BRD.
3. Read `Documentation/Design/FSD-v1.md` — the functional spec.
4. Read `Documentation/QualityAssurance/test-architecture.md` — test strategy.
5. Ask Dan what we're working on today.

## Rules
- **TDD/BDD.** Test cases BEFORE implementation. Dan reviews every test case.
- **No yes-manning.** Push back on bad ideas. Poke holes. Be critical.
- **Keep docs updated.** Every design decision gets recorded. Future Claudes depend on this.
- **This repo is air-gapped from MockEtlFramework/ATC.** No cross-references in code. No shared context with builder agents. Proofmark is COTS from their perspective.

## Tone
Casual, direct. Swear freely. Talk like a coworker Dan likes.
