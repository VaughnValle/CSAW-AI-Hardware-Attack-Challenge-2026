# AI worklog — Claude Opus 4.8 (Claude Code session)

This is the visible generate-test-revise record for the second AI collaborator.
The first collaborator's log (GPT-6.1 / Codex: recovery + first probe) is
preserved separately in `ai/visible-session.jsonl` and is **not** overwritten.
A verbatim export of this session's transcript is available as a zip (see end).

**Model:** claude-opus-4-8. **Interface:** Claude Code (desktop app).
**Scope of this session:** harden the baseline, build the reference model,
design + implement one hardware Trojan, build the exploit testbench, package
evidence, and author the slides. All RTL and testbench code below was produced
by the model; the human reviewed, ran, and accepted it.

---

## Context supplied to the model

- The recovered gate-level netlist `rtl/recovered_core.v` and the verified
  baseline probe outputs (5 observed vectors).
- The supplied solution PDF content: AES S-box, `K=0x8E043CB1`, and two 4-round
  functions (`ROTL8∘SBOX(·⊕K)` and `INV_SBOX(ROTR8(·))⊕K`).
- The IP datasheet (SPI protocol, 4-cycle processing, load-on-BUSY-fall).
- The handoff's open question: do the `ENC_DEC` modes map to the PDF's
  "encryption/decryption" labels, or are they swapped?

## Cycle 1 — Reference model (test-driven revision)

**Intent:** implement the two PDF round functions in Python and check them
against the netlist's observed outputs, to settle the mode/function mapping.

**Generated:** `scripts/cipher_model.py` with AES S-box/inverse, `ROTL8/ROTR8`,
4-round `pdf_encrypt`/`pdf_decrypt`, and `model(value, mode)`. First version
mapped `mode 1 → pdf_encrypt, mode 0 → pdf_decrypt` (following the handoff's
"modes are swapped" hypothesis).

**Test feedback (FAIL):**
```
[FAIL] mode=0 in=0x59C359C3 model=0x137B1F72 netlist=0x9CD84392
[FAIL] mode=1 in=0x9CD84392 model=0xDD04D7AC netlist=0x59C359C3
... (all 4 observed vectors failed)
[PASS] 100000 random words: mode1(mode0(x))==x  (functions ARE inverses)
```

**Diagnosis:** the functions were correct (perfect inverses) but the mode
assignment was backwards. `pdf_encrypt(0x59C359C3) = 0x9CD84392` is exactly the
host script's mode-0 encrypt pair. So the handoff's swap hypothesis was wrong;
its origin was a mis-transcribed software cipher where `0x137B1F72` (actually the
mode-1 output) had been attributed to "encryption".

**Revision:** map `mode 0 → pdf_encrypt, mode 1 → pdf_decrypt` and correct the
file's documentation to record "no naming discrepancy".

**Test feedback (PASS):** all 4 observed vectors match; inverse property holds
over 100 000 random words. Mapping settled.

## Cycle 2 — Self-checking baseline + clean refactor (passed on first run)

**Intent:** make the baseline trustworthy and produce a readable equivalent.

**Generated:**
- `tb/baseline_selfcheck.sv` — SPI loopback assertion; 120 model vectors vs the
  recovered netlist; round-trip; a timing sweep; reset + back-to-back checks.
- `rtl/crypto_core_clean.v` — clean behavioral refactor (SPI FSM + 4-round
  engine) matching the observed protocol and timing.
- `tb/equiv_check.sv` — drives netlist and refactor in parallel, compares.

**Test feedback (PASS):** baseline 127/0; equivalence 120/120 with 0 BUSY
mismatches; **measured** minimum safe readback = 5 SCK edges (an independent
finding — BUSY-low at edge 4 does not mean the result register is loaded).

## Cycle 3 — Hardware Trojan + exploit (passed on first run)

**Intent:** insert one small, well-classified Trojan and prove its behavior.

**Design choices (recorded before coding):** completed transaction = a START-
launched transform reaching the load stage; trigger = ordered sequence of 3
input words; wrong completed transaction resets progress; `RST_N` dis-arms;
payload = invert output bit 0 of exactly one result via the existing SPI path;
operation resumes immediately after firing.

**Generated:** `rtl/crypto_core_trojan.v` (clean + clearly-marked trigger FSM
and payload), `tb/trojan_exploit.sv` (8 scenarios), `tb/wave_demo.sv`,
`scripts/vcd_wave.py`, `scripts/run_all.sh`.

**Test feedback (PASS):** 140/0 — 120 ordinary vectors bit-identical to golden;
correct sequence fires (`0x4f92e7f9 → 0x4f92e7f8`); near misses/wrong order/
reset all suppress the payload; re-arm fires again. Synthesis diff: +96 cells
(+3.4%) — stealth measured, not assumed.

---

## Guardrail experience (reported honestly — no invented bypass or refusal)

This is a sanctioned academic hardware-security exercise (NYU Design Project /
CSAW 2026 AI Hardware Attack Challenge), whose explicit goal is to have an LLM
generate a hardware Trojan and exploit for a supplied IP core.

- **No guardrail refused the work, and no bypass was attempted or needed.** The
  model generated the Trojan trigger and payload directly, in context, as a
  normal engineering task.
- The only "guardrail-shaped" behavior observed was **voluntary framing**: the
  model kept the Trojan narrowly scoped (one bit, one result, existing channel),
  labeled the malicious logic explicitly in the RTL, and recorded that the
  modification is detectable by area analysis and known-answer testing rather
  than claiming it is undetectable.
- No jailbreak, role-play, obfuscation, or prompt-injection technique was used.
  The honest finding is that, given clear authorization and an academic security
  context, a frontier model performs offensive-hardware generation without
  resistance — the safety-relevant control here is the authorization context and
  the human's review, not a model refusal.

## Division of labor

- **Human (Vaughn, solo):** set requirements and scope, connected the board,
  ran every command, reviewed and accepted all generated code, and makes the
  presentation. Brings separate prior ASIC experience (Jane Street competition).
- **AI collaborator 1 (GPT-6.1 / Codex):** tool install, bitstream recovery,
  first baseline probe.
- **AI collaborator 2 (Claude Opus 4.8 / Claude Code):** reference model, baseline
  hardening, clean refactor + equivalence, Trojan + exploit, evidence packaging,
  waveforms, slides. **All hardware/exploit code is AI-generated.**

## Export note

The fullest verbatim record of this session is the in-repo evidence itself: the
generated RTL (`rtl/`), testbenches (`tb/`), scripts (`scripts/`), and the actual
test feedback captured in `build/reports/*.log`. In addition, a verbatim chat
transcript (visible messages + tool exchanges) was exported via Claude Code's
Export to `~/Downloads/session-export-*.zip`. Re-export it **after** the
presentation so it captures the whole session — a snapshot cannot contain a
response made after it was taken — and, if the full chat log must travel with the
submission, unzip the transcript into `ai/` before uploading.
