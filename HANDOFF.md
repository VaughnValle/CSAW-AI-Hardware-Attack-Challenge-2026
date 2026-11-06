# CSAW / NYU Design Project: AI agent handoff

**Snapshot:** Thursday, November 5, 2026, approximately 6:40 PM America/New_York (Eastern Standard Time).

**Deadline:** Class presentation is due **Friday, November 6, 2026**. The exact presentation time has not been provided.

**Working directory:** `/Users/bon/Documents/CSAW-AI-Hardware-Attack-Challenge-2026`

## 1. Mission and user context

Help the student complete a credible NYU Design Project presentation about the CSAW 2026 AI Hardware Attack Challenge, backed by actual simulation evidence. The student works **alone**, has prior hardware experience from **Jane Street's ASIC competition**, and has a physical **Hackster board**. Prior ASIC work is relevant experience with separate results.

Tomorrow's expectation is **simulation**. A hardware demonstration is optional and should not consume the time needed for simulation and slides. The student initially needed a high-level explanation and plan, then authorized implementation with "Got it, let's do it." They have now asked to transfer the work to another AI agent.

The intended technical project is:

1. Recover an inspectable circuit from the supplied FPGA bitstream.
2. Understand and verify the original accelerator's behavior in simulation.
3. Use AI to generate one small hardware Trojan and its exploit testbench.
4. Show ordinary behavior, trigger activation, and the payload with reproducible evidence.
5. Prepare an editable 5-10 minute slide deck and a PDF export, and place the presentation in the intended student GitHub repository.

The student benefits from short, plain-language progress updates explaining what a step achieves. Continue the already authorized work without repeatedly asking for approval. Preserve their files and distinguish proposed work from completed work.

## 2. Read this status before older plans

**This handoff supersedes the progress descriptions in `docs/presentation-plan.md` and `docs/local-bench-setup.md`.** Those documents contain useful planning and setup guidance, but were originally written before installation and recovery.

### Completed and verified

- Reviewed all challenge documentation, the host MicroPython script, and all four solution diagram pages.
- Installed native Apple Silicon **OSS CAD Suite 2026-11-05** at `/Users/bon/Tools/oss-cad-suite`.
- Created the project Python environment `.venv` with **pyserial 3.5** and **mpremote 1.29.0**.
- Cloned the vendor programmer repository to `/Users/bon/Tools/hackster-programmer`.
- Ran `tb/environment_smoke.sv` successfully using the pre-existing Icarus installation.
- Unpacked the supplied binary and recovered a structural Verilog circuit.
- Mapped all **nine recovered ports** to the documented Hackster interface.
- Implemented a reproducible recovery script that fixes a declaration syntax issue while preserving the circuit body.
- Added the required FPGA primitive models to the simulation command and successfully ran `tb/baseline_probe.sv` against the recovered circuit.
- Observed correct SPI shift-register readback and the provided plaintext/ciphertext pair in both intended modes.
- Observed two USB serial devices after the student connected both cables.

### Still pending

- A stronger, self-checking baseline testbench. The current probe asserts SPI readback but **prints** the cryptographic outputs for inspection; it does not yet assert all cipher results.
- Broad functional regression, independent reference-model checks, and precise result-loading latency characterization.
- A Trojan design implementation, exploit testbench, and tests showing ordinary behavior remains intact.
- Synthesis resource comparison and optional timing checks.
- Actual MicroPython REPL/hello verification on the connected board. USB enumeration has succeeded; a command has not yet been sent to AppMicro.
- Any FPGA programming or firmware changes. **No device was flashed during this work.**
- The slide deck, slide renders/visual checks, PDF export, rehearsal notes, and GitHub submission.
- A final, refreshed export of the complete visible AI history after implementation finishes.

## 3. Challenge and presentation requirements

Read `presentation-instructions.txt` for the class brief. It requests approximately **5-10 minutes** addressing:

- What has been done so far.
- How the bitstream was reverse engineered.
- How recovered information was supplied to the LLM.
- Which open tools were used.
- What the bitstream implements.
- The Trojan design and its taxonomy.
- Actual experience with LLM security guardrails.
- Division of labor.
- Uploading the presentation to GitHub.

Read `qualifier/README.md` for the challenge rules. The hardware Trojan and exploit must be AI-generated, and hardware code must not be written by the human student. Keep comprehensive prompts and responses, including the context supplied, generation revisions, and test feedback. Missing AI logs can invalidate a challenge submission.

The qualifying deliverables are modified RTL, an exploit testbench, AI transcripts, and a technical brief. The rubric assigns 35 points to AI usage, 25 to Trojan quality, 15 to automation, 15 to documentation, and 10 to simulation. Preserve a traceable generate-test-revise process before attempting elaborate automation.

The class deadline is separate from the competition schedule. `finals/README.md` describes a later physical demonstration and two challenges whose details are not yet in this checkout. Those are outside tomorrow's minimum scope.

## 4. Repository and artifact map

| Path | Purpose / status |
| --- | --- |
| `README.md` | Original competition overview and external references |
| `presentation-instructions.txt` | Student-provided class brief; originally untracked, preserve it |
| `qualifier/README.md` | Challenge rules, deliverables, scoring, solution images |
| `qualifier/ice40_bitstream.bin` | Original supplied image; unchanged |
| `qualifier/ice40_cryptographic_IP.md` | Original SPI/control documentation |
| `qualifier/spi_ice40_crypto_ip_test.py` | Original MicroPython host script; runs on AppMicro, not desktop CPython |
| `qualifier/docs/les_block_diagrams.pdf` | Four solution pages with explicit key and round functions |
| `qualifier/docs/les_block_diagrams-0.png` through `-3.png` | Supplied diagram images |
| `constraints/hackster.pcf` | AI-created named pin map adapted from vendor SPI constraints |
| `scripts/recover.py` | Reproducible binary-to-Verilog recovery and syntax normalization |
| `rtl/recovered_core.v` | Bitstream-derived structural circuit, about 207 KiB, normalized port declarations |
| `rtl/accelerator_baseline.v` | AI-created wrapper giving the recovered ports readable names |
| `tb/environment_smoke.sv` | Small simulator environment check; passed |
| `tb/baseline_probe.sv` | Actual recovered-circuit SPI/mode/timing probe; ran successfully |
| `scripts/export_ai_log.py` | Exports visible conversation and tool exchanges from this local chat session |
| `ai/visible-session.jsonl`, `ai/metadata.json` | Exported chat evidence; refresh before final submission |
| `docs/presentation-plan.md` | Earlier detailed work plan, eight-slide outline, and presentation coverage checklist |
| `docs/local-bench-setup.md` | Setup commands, vendor references, pin map, and optional hardware procedures |
| `build/recovered/design.asc` | Unpacked configuration, identified as device `5k` |
| `build/recovered/raw.v` | Untouched verbose export, about 45,711 lines |
| `build/recovered/compact_raw.v` | Untouched compact export before syntax normalization |
| `build/recovered/configuration.txt` | Tile/configuration explanation |
| `build/recovered/manifest.json` | Recovery commands, ports, input/output hashes, normalization description |
| `build/reports/baseline-probe.log` | Actual baseline observations reproduced below |
| `build/sim/baseline_probe.vcd` | Waveform of the recovered-circuit probe, about 1.2 MiB |
| `build/reports/*version*`, `tool-paths.txt` | Installed tool provenance |
| `presentation/` | Intended deck location; no deck exists yet |

`build/` and `.venv/` are ignored by Git. Important report/waveform evidence must be intentionally copied or packaged if it needs to travel with the submission. The existing ignore rules also exclude some nested `src` directories, so verify new source files are tracked as intended.

At handoff, `.gitignore` is modified and the new `constraints/`, `docs/`, `rtl/`, `scripts/`, and `tb/` content is untracked. No work was committed or pushed. No new branch or worktree was created. Preserve the existing checkout. **Remote configuration update:** the student identified their fork as `https://github.com/VaughnValle/CSAW-AI-Hardware-Attack-Challenge-2026.git`. Both fetch and push URLs for `origin` now point to that fork. The original competition repository, `https://github.com/JBlocklove/CSAW-AI-Hardware-Attack-Challenge-2026.git`, is retained as `upstream`. Changing these local settings did not publish any files; prepare and review deliverables before uploading them.

Original bitstream SHA-256:

```text
5fa5fda9768c36808780398d8e24d125d860aacc62b61af8b4c5124dd759ddbe
```

## 5. Resume commands

Run in a shell with this project as its current directory. Each new shell must activate the tool bundle again.

```sh
cd /Users/bon/Documents/CSAW-AI-Hardware-Attack-Challenge-2026
source /Users/bon/Tools/oss-cad-suite/environment
mkdir -p build/recovered build/sim build/reports
python3 scripts/recover.py

iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS \
  -s baseline_probe -o build/sim/baseline_probe.vvp \
  /Users/bon/Tools/oss-cad-suite/share/yosys/ice40/cells_sim.v \
  rtl/recovered_core.v rtl/accelerator_baseline.v tb/baseline_probe.sv

vvp build/sim/baseline_probe.vvp
```

The probe has already run with these primitive-model arguments. When recording output through `tee`, enable `set -o pipefail` so simulator failures remain visible in the command's exit status.

### Two recovery issues already solved

1. **Port declaration syntax:** Icebox exports an ANSI `output pin_31` header and later declares `reg pin_31 = 0`, which Icarus rejects. `scripts/recover.py` converts the scalar port header to non-ANSI declarations, allowing the separate register declaration. Its assertion verifies that the circuit body remains unchanged. Retain the raw export and the manifest.
2. **Missing memory primitives:** The circuit instantiates four `SB_RAM40_4K` blocks. Include the bundle's `share/yosys/ice40/cells_sim.v` and define `NO_ICE40_DEFAULT_ASSIGNMENTS` when compiling. The earlier compile failure was an omitted simulation dependency, not evidence of a broken bitstream.

Installed version examples:

```text
Yosys 0.70+336, git 8f3cc3d0c
nextpnr-ice40 0.11.1-88-g937c770c
OSS CAD Suite release 2026-11-05, native darwin-arm64
```

## 6. Actual baseline findings: use these rather than earlier hypotheses

The recovered module has these ports and the named wrapper connects them as follows:

| Signal | FPGA sg48 pin | AppMicro GPIO from challenge script |
| --- | --- | --- |
| SCK | 36 | GP6 |
| RST_N | 34 | GP7 |
| MOSI | 32 | GP8 |
| MISO | 31 | GP9 |
| NORM_CS_N | 28 | GP10 |
| START | 27 | GP12 |
| ENC_DEC | 25 | GP13 |
| BUSY | 23 | GP14 |
| ICE_LED | 38 | FPGA output |

The exported circuit directly connects the BUSY and ICE_LED outputs. The probe drives SPI mode-0-style transfers, MSB first, and samples the registered MISO after each rising edge.

### Observed outputs

| Experiment | Observed result |
| --- | --- |
| SPI shift readback of `0x59C359C3` | `0x59C359C3`, asserted by the probe |
| Mode 0, input `0x59C359C3` | `0x9CD84392` |
| Mode 1, input `0x9CD84392` | `0x59C359C3` |
| Mode 1, input `0x59C359C3` | `0x137B1F72` |
| Mode 0, input `0x9CD84392` | `0xDD04D7AC` |

The first two cryptographic observations reproduce the host script's intended encryption/decryption pair. **Do not continue treating its sample vector as failing.**

For both mode values, BUSY rose when START was asserted before its first clock edge, stayed high after edges 1-3, and fell after edge 4. The probe waits until edge 8 before readback, matching the conservative host-script sequence. **The minimum safe result-readback latency is still unmeasured.** Characterize it separately rather than assuming BUSY-low means every loading register has already updated.

### Why earlier calculations appeared inconsistent

The supplied PDF explicitly labels encryption as repeated:

```text
x_next = AES_inverse_Sbox_per_byte(ROTR32(x, 8)) XOR K
K = 0x8E043CB1
four rounds
```

A software transcription gave `0x137B1F72` for input `0x59C359C3`. The recovered circuit produces that value in **mode 1**, whereas the host script calls **mode 0** encryption. The PDF's opposite round function is:

```text
y_next = ROTL32(AES_Sbox_per_byte(y XOR K), 8)
four rounds
```

The current observations are consistent with the PDF's encryption function corresponding to mode 1 and its decryption function corresponding to mode 0. Explain the naming disagreement, and verify the proposed reference functions across more inputs before claiming a complete cipher reconstruction. The two functions are intended inverses, so nomenclature alone should not obscure the actual mode-to-function mapping.

The key is **supplied in the solution PDF**. It has not been independently extracted from the recovered logic. Do not claim bonus key recovery or independent discovery without further evidence. The cipher uses AES S-box components but is a custom 32-bit, four-round construction, rather than standard AES encryption.

## 7. Physical board status and commands

The student connected both cables during this chat. Last observed devices:

| Device | Description / identity | Intended role |
| --- | --- | --- |
| `/dev/cu.usbmodem21301` | `Board in FS mode`, VID:PID `2E8A:0005`, serial `e4654841cf26542b` | AppMicro candidate; confirm with a MicroPython hello |
| `/dev/cu.usbmodem21401` | `Hackster`, VID:PID `2E8A:000A`, serial `E4654841CF410E2` | FPGA programmer |

These paths can change. Enumerate before use:

```sh
.venv/bin/python -m serial.tools.list_ports -v
.venv/bin/mpremote connect /dev/cu.usbmodem21301 resume exec \
  "import sys; print(sys.implementation); print('Hackster AppMicro ready')"
```

The hello command has **not yet been run**. A serial enumeration is not a complete board functional test. No FPGA image or RP2040 firmware has been changed.

Use explicit `.venv/bin/python` and `.venv/bin/mpremote` for board tooling, since activating the OSS suite changes the default Python. Only one serial tool should own an application port at a time.

If hardware testing is useful later, `docs/local-bench-setup.md` has the exact original-image loading command and the vendor's 256 KiB flash-readback command. That readback is not a full backup of both RP2040s or all possible FPGA flash contents. Inspect programmer output carefully: the upstream utility can print a success line even after reporting `Data mismatch`. The supplied MicroPython script also prints some failures without necessarily returning a failing desktop process status.

## 8. Remaining work in priority order

### P0: Strengthen the baseline

**Goal:** Establish trustworthy ordinary behavior before modifying the design.

- Rerun the probe to establish the incoming agent's environment.
- Make the observed host-script pair self-checking in both modes.
- Implement an independent reference model for the proposed round functions, clearly attributing the PDF key.
- Compare deterministic edge cases and reproducibly seeded random inputs against the recovered netlist.
- Check reset, ordinary back-to-back transactions, mode selection, and exact result-loading timing.
- Preserve a concise baseline result table and a readable waveform showing START, SCK, BUSY, chip select, and serial data.

**Completion criterion:** Repeatable passing checks with a documented mode/function mapping and no unexplained reference discrepancy.

### P1: Implement one small AI-generated Trojan

**Goal:** Demonstrate a controlled malicious modification with clear simulation evidence.

The recommended first scope is a rare **sequence of complete input transactions** triggering a **one-result integrity payload**, such as flipping a selected ciphertext bit through the existing output path. This is a proposal only; no trigger values or implementation have been committed.

Before coding, define what constitutes a completed transaction, how incorrect sequences reset trigger progress, whether reset clears activation, which response changes, and how ordinary operation resumes. Retain the bitstream-derived baseline for comparison. A refactored implementation is allowed by the challenge, but it must be tested against that baseline and its provenance explained.

Suggested taxonomy: design-time RTL insertion, digital input-controlled sequential trigger, functional corruption payload, integrity impact, existing SPI output channel, one-result effect. Measure stealth claims rather than assuming a small modification is undetectable. Key disclosure can be a later extension if the simple case works comfortably early.

### P2: Validate the Trojan and package evidence

**Goal:** Show both the intended effect and preservation of ordinary behavior.

- Original and modified designs receive identical ordinary transactions and match.
- The specified trigger activates the exact intended payload.
- Near misses, wrong sequence order, and reset behavior follow the specification.
- An ordinary transaction after the payload behaves as specified.
- Record actual test counts, seeds, and results. Simulation coverage is not universal equivalence.
- If time permits, compare synthesized resources using the same flow and report measured differences.
- Provide one reproducible command or script for baseline and exploit validation.

### P3: Build the presentation and technical brief

**Goal:** Deliver an accurate, understandable 5-10 minute progress presentation.

Use eight slides targeting about 7 minutes 40 seconds:

| Slide | Topic | Target time |
| --- | --- | --- |
| 1 | Project goal and current progress | 0:40 |
| 2 | Accelerator architecture and ordinary transaction | 1:00 |
| 3 | Bitstream recovery and open tools | 1:05 |
| 4 | Baseline verification and resolved naming discrepancy | 1:00 |
| 5 | Actual AI inputs, generation/revision workflow, and guardrail experience | 1:00 |
| 6 | Trojan trigger, payload, insertion point, and taxonomy | 1:10 |
| 7 | Simulation evidence and measured limitations | 1:00 |
| 8 | Solo responsibilities and next milestone | 0:45 |

Credit supplied diagrams and distinguish supplied information from independently recovered evidence. Explain the student's requirements, decisions, and verification responsibilities alongside AI's code-generation role. Report actual guardrail interactions; do not invent a bypass or a refusal.

Save the editable deck and PDF under `presentation/`. Keep code snippets short and waveforms readable. Follow the available presentation-authoring skill and inspect slide renders before delivery. No visual theme or template has been chosen. The student's GitHub destination is now identified: `origin` points to the VaughnValle fork. The competition repository is retained as `upstream`.

### P4: Optional physical demonstration

**Goal:** Reproduce the simulated behavior on Hackster.

Confirm AppMicro first, then prepare the appropriate pin-constrained bitstream and host sequence. Keep this phase optional until simulation evidence and slides are secure. Tomorrow's stated requirement is simulation.

## 9. Revised timeline from this handoff

Use Eastern time and check the actual current time on resuming. These are estimates, not completed milestones. Installation and first recovery are already done, so do not repeat the original 5 PM setup schedule.

| Proposed time | Task / outcome |
| --- | --- |
| Thu 6:45-7:00 PM | Reproduce current probe, read source/logs, optionally confirm AppMicro hello |
| Thu 7:00-8:00 PM | Strengthen baseline assertions, reference comparison, and timing characterization |
| Thu 8:00-8:30 PM | Meal/break and scope decision |
| Thu 8:30-9:30 PM | One small Trojan plus exploit test, only if baseline is trustworthy |
| Thu 9:30-10:15 PM | Ordinary/triggered/near-miss regression and waveform capture |
| Thu 10:15-10:45 PM | Resource comparison if practical, technical brief, results and AI-log packaging |
| Thu 10:45 PM-Fri midnight | Build and inspect the eight-slide deck, export PDF |
| Fri midnight-12:30 AM | Rehearse, trim slides, verify outputs and submission destination |
| Fri 12:30-1:15 AM | Contingency buffer for validation and packaging |
| Before presentation | Reserve 30-45 minutes for opening the final files and reviewing questions |

**Scope gates:** If baseline remains unresolved, retain the Trojan as a clearly labeled proposal and present the actual recovery/diagnostic evidence. Protect at least 90 minutes for slides and rehearsal. Begin slide authoring by 10:45 PM under this revised schedule. Exact presentation time remains unknown, so preserve a finished overnight copy.

## 10. AI provenance and continuation logs

The local chat session for this work is:

```text
/Users/bon/.codex/sessions/2026/11/05/rollout-2026-11-05T16-44-33-01a1adab-b1e2-75c1-9931-37099b0b6f2c.jsonl
```

Its inspected turn metadata identifies `gpt-6.1-sol` and the Codex desktop interface. Use the actual exported metadata if later turns show additional models.

Refresh the visible history export with:

```sh
/usr/bin/python3 scripts/export_ai_log.py \
  /Users/bon/.codex/sessions/2026/11/05/rollout-2026-11-05T16-44-33-01a1adab-b1e2-75c1-9931-37099b0b6f2c.jsonl
```

The exporter retains visible user/assistant messages and tool exchanges, including generated code and command results. It excludes private reasoning and system/developer instructions. It creates `ai/visible-session.jsonl` and `ai/metadata.json` and must be refreshed after later work to capture it. A snapshot taken before a final response cannot contain that future response.

If continuing in a different agent or chat, preserve this session's export and save the new agent's full visible interactions separately. The existing exporter overwrites its fixed filenames, so do not use it on a different session without changing the output destination or preserving the prior export.

## 11. Sources and attribution

- Challenge rules and artifacts: repository `README.md`, `qualifier/README.md`, interface document, host script, and supplied diagrams.
- [OSS CAD Suite installation](https://github.com/YosysHQ/oss-cad-suite-build#installation) and [installed release](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-11-05).
- [IceStorm overview](https://prjicestorm.readthedocs.io/en/latest/overview.html) and [icebox_vlog source](https://github.com/YosysHQ/icestorm/blob/main/icebox/icebox_vlog.py).
- [Hackster programmer](https://github.com/kiwih/hackster-programmer), [SPI pin constraints](https://github.com/kiwih/hackster-programmer/blob/main/examples/spi_aes/spi_aes.pcf), and [package/build settings](https://github.com/kiwih/hackster-programmer/blob/main/examples/hackster.mk).
- [Hackster setup lab](https://cgi.cse.unsw.edu.au/~cs6420/labs/lab00introduction/) and [mpremote documentation](https://docs.micropython.org/en/latest/reference/mpremote.html).
- [Surfer waveform viewer](https://surfer-project.org/) if GTKWave is unavailable on this Mac.

If reusing the Hackster schematic or hardware documentation, use the repository's attribution: **Hammond Pearce, UNSW Sydney - CC BY-SA 4.0**. Preserve other applicable source notices and licenses.

## Immediate next action

**Read the current baseline log, rerun the probe with the included memory primitive models, then turn the observed cipher pair into explicit assertions and broaden baseline coverage. Do not reinstall tools or restart the project from the old planning state.**
