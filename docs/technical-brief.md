# Technical brief — CSAW 2026 AI Hardware Attack Challenge (qualifier)

**Author:** Vaughn (NYU Design Project, solo)
**Date:** 2026-11-05 (presented 2026-11-06)
**AI collaborators:** GPT-6.1 (Codex desktop; recovery + baseline probe) → Claude Opus 4.8 (Claude Code; baseline hardening, Trojan, exploit, evidence, slides)

All hardware/RTL and exploit code in this submission is **AI-generated**. The
human defined requirements, verified results, and made scope decisions. The
complete AI interaction logs are in `ai/` (see §8).

---

## 1. What was done

1. Recovered an inspectable circuit from the supplied iCE40 bitstream.
2. Verified the original accelerator's behavior in simulation against the
   recovered gate-level netlist.
3. Reconstructed the cipher and **resolved** the mode/function naming question.
4. Produced a clean behavioral refactor proven equivalent to the netlist.
5. Inserted one small AI-generated hardware Trojan and an exploit testbench.
6. Demonstrated ordinary behavior, trigger activation, near misses, reset
   dis-arming, one-result scope, and recovery, with waveforms and a resource
   comparison, all from one reproducible script.
7. Demonstrated the whole attack on the **physical Hackster board**: backed up
   the FPGA flash, flashed the original and then our Trojan bitstream, reproduced
   the exploit on real silicon, and restored the clean image (see §7b).

## 2. Supplied vs. independent (important for scoring honesty)

| Item | Source |
| --- | --- |
| `ice40_bitstream.bin` | **Supplied** challenge artifact |
| Port/SPI protocol, 4-cycle processing hint | **Supplied** (`ice40_cryptographic_IP.md`) |
| AES S-box, round key `K=0x8E043CB1`, the two round-function equations | **Supplied** (solution PDF `les_block_diagrams.pdf`) |
| Gate-level netlist `recovered_core.v` | **Independent** (icebox_vlog recovery) |
| Mode↔function mapping and the "no discrepancy" conclusion | **Independent** (reference model vs netlist) |
| Minimum safe readback latency = 5 SCK edges | **Independent** (timing sweep) |
| Clean refactor, Trojan, all testbenches, waveforms, synth diff | **Independent / AI-generated** |

The key was **supplied in the PDF**. We do **not** claim independent key
recovery from the logic.

## 3. How the bitstream was reverse engineered

- `iceunpack ice40_bitstream.bin design.asc` (identified device `5k`).
- `icebox_vlog -l -d sg48 -n recovered_core design.asc` → structural Verilog
  (~3.2k lines after normalization; 9 scalar ports, four `SB_RAM40_4K`).
- `scripts/recover.py` is deterministic and content-addressed: it records the
  input SHA-256, the exact commands, and performs the **only** edit — converting
  icebox's ANSI scalar-port header to non-ANSI declarations so Icarus accepts
  the later `reg` declarations. An assertion guarantees the **circuit body is
  byte-for-byte unchanged**. Input SHA-256:
  `5fa5fda9768c36808780398d8e24d125d860aacc62b61af8b4c5124dd759ddbe`.
- Memory models: compile with `cells_sim.v` and `-DNO_ICE40_DEFAULT_ASSIGNMENTS`
  to supply the `SB_RAM40_4K` / primitive behavior.

**Open tools:** OSS CAD Suite 2026-11-05 (Project IceStorm `iceunpack`/
`icebox_vlog`, Yosys `synth_ice40`, Icarus Verilog `iverilog`/`vvp`), Python 3.
No proprietary vendor tools were used for recovery or simulation.

## 4. What the bitstream implements

A lightweight **32-bit, 4-round block cipher** with a raw SPI peripheral
interface and discrete sideband control (no AXI/Wishbone). Unified clock
domain: `SCK` clocks both the SPI shift register and the crypto engine.

- Encrypt round (mode 0): `y ← ROTL8( SBOX_perbyte( y XOR K ) )`
- Decrypt round (mode 1): `x ← INV_SBOX_perbyte( ROTR8( x ) ) XOR K`
- Four rounds; the two functions are exact inverses (verified over 100 000
  random words). Uses AES S-box bytes but is **not** standard AES.

### Resolved naming question

An earlier hypothesis held that the silicon's `ENC_DEC` modes were **swapped**
relative to the PDF's "encryption/decryption" labels. Our reference model shows
there is **no discrepancy**: `pdf_encrypt(0x59C359C3) = 0x9CD84392`, exactly the
host script's mode-0 ("encrypt") plaintext→ciphertext pair. The earlier swap
hypothesis traced to a mis-transcribed software cipher — the value `0x137B1F72`
attributed to "encryption" is actually the mode-1 (decrypt) output of the
plaintext. Mode 0 = PDF encryption, mode 1 = PDF decryption, by their plain names.

### Timing

`BUSY` is high through SCK edges 1–3 and low from edge 4, but the processed word
is **parallel-loaded one edge later**: the minimum safe readback latency is
**5 SCK edges** after `START`, not 4. The host script's 8 edges is safely
conservative. (`BUSY`-low alone does not guarantee the result register updated.)

## 5. Baseline verification (self-checking)

| Check | Result |
| --- | --- |
| SPI loopback readback | exact |
| 60 inputs × 2 modes vs reference model | 120/120 pass |
| Netlist vs clean refactor equivalence | 120/120, 0 BUSY mismatches |
| Round-trip on netlist (enc∘dec, dec∘enc) | pass |
| Reset clears in-flight result | pass |
| Back-to-back transactions | pass |
| **Total baseline checks** | **127 pass / 0 fail** |

Reference vectors are produced by `scripts/cipher_model.py`, which is itself
validated against the netlist's observed outputs and the mutual-inverse
property, so nothing in the bench is hand-copied from netlist outputs.

## 6. Trojan

**Design-time RTL-insertion hardware Trojan.** Diff `rtl/crypto_core_clean.v`
against `rtl/crypto_core_trojan.v` for the entire modification.

| Taxonomy axis | Classification |
| --- | --- |
| Insertion phase | Design-time, RTL source |
| Trigger | Digital, input-controlled, **sequential** — rare ordered sequence of 3 complete transactions (`0x13375EED → 0xC0DEFACE → 0xA5A5A5A5`) |
| Rarity / reset of progress | Any wrong completed transaction resets progress (a word = SEQ0 restarts it) |
| Payload | Functional corruption, **integrity** impact — invert output bit 0 |
| Delivery channel | **Existing** SPI output path; **no added ports** |
| Effect scope | **One result**; progress resets, ordinary operation resumes |
| Reset behavior | Synchronous `RST_N` clears trigger progress (dis-arms) |

Added state: a 32-bit input-capture register and a 2-bit progress counter.

## 7. Trojan validation and measured limitations

| Scenario | Result |
| --- | --- |
| (A) 120 ordinary vectors | **dormant**, bit-identical to golden |
| (B) correct sequence | **fires**: golden `0x4f92e7f9` → trojan `0x4f92e7f8` (bit 0) |
| (C) one-result scope + recovery | next transactions normal |
| (D) wrong final word | no fire |
| (E) wrong middle word | no fire |
| (F) wrong order | no fire |
| (G) reset mid-sequence | dis-armed, no fire |
| (H) re-arm | fires again |
| **Total Trojan checks** | **140 pass / 0 fail** |

**Stealth is measured, not assumed.** `synth_ice40` resource comparison:

| Metric | Clean | Trojan | Δ |
| --- | --- | --- | --- |
| Total cells | 2813 | 2909 | +96 (+3.4%) |
| SB_LUT4 | 2709 | 2771 | +62 (+2.28%) |
| Flip-flops (DFF+DFFE+DFFESR) | 104 | 138 | +34 |

The Trojan is dormant to functional testing on ordinary traffic and invisible on
BUSY/timing/LED side channels, but it is **not** area-invisible: a gate/area
diff reveals the added trigger state. A known-answer test on the exact trigger
word would also expose it. Simulation coverage here is extensive but **not** a
universal-equivalence proof.

## 7b. On-board hardware demonstration (real Hackster board)

The attack was validated end-to-end on the physical board, not only in
simulation. Devices: AppMicro `/dev/cu.usbmodem21301` (RP2040, MicroPython
1.27.0), FPGA programmer `/dev/cu.usbmodem21401` (vendor `hackster-programmer`,
commit `e664a43`).

| Step | Observation |
| --- | --- |
| AppMicro hello | MicroPython 1.27.0 on RP2040 — confirmed |
| Supplied test on as-found FPGA | **SPI error** — FPGA was unprogrammed |
| 256 KiB flash read-back (backup) | **100% 0xFF** — flash was blank (sha `3b874d3b…`) |
| Flash original `ice40_bitstream.bin` | "Verification successful", no data mismatch |
| Supplied test on original | SPI pass; encrypt `9cd84392`; decrypt `59c359c3` — matches sim |
| Build + flash Trojan bitstream | yosys→nextpnr(up5k/sg48)→icepack; Fmax 21.86 MHz (SCK ≤1 MHz); clean write |
| Supplied test on Trojan image | still passes (dormant on ordinary traffic) |
| On-board exploit (`scripts/hw_trojan_exploit.py`) | un-armed SEQ2 → `4f92e7f9`; armed SEQ0→SEQ1→SEQ2 → **`4f92e7f8`**; recovers after |
| Restore original image | "Verification successful"; supplied test passes again |

The board was left running the clean original image (not the Trojan). The
Trojan bitstream is reproducible via `scripts/build_bitstream.sh`; logs are in
`build/reports/hw-*.log`. Note (per vendor caveat) the programmer can print a
success line even after a `Data mismatch`, so each write was scanned for
mismatch/error lines — none were present.

## 8. Reproduce everything

```sh
source /Users/bon/Tools/oss-cad-suite/environment
bash scripts/run_all.sh
```

Runs recovery → Python model self-test → baseline self-check → netlist/clean
equivalence → Trojan exploit → synthesis diff → waveforms, and exits non-zero on
any self-check failure. Evidence lands in `build/reports/` and
`presentation/figures/`.

For the real-board demo (board connected), build the bitstreams and follow the
printed flash/exploit commands:

```sh
source /Users/bon/Tools/oss-cad-suite/environment
bash scripts/build_bitstream.sh    # builds build/hw/crypto_core_{clean,trojan}.bin
```

## 9. AI provenance

- `ai/visible-session.jsonl`, `ai/metadata.json` — preserved GPT-6.1/Codex log
  (recovery + first probe). **Do not overwrite.**
- `ai/claude-opus-worklog.md` — Claude Opus 4.8 generate-test-revise log
  (baseline hardening, Trojan, exploit), including the one substantive revision
  (mode-mapping correction) driven by test feedback, and the guardrail experience.
