# NYU Design Project: CSAW presentation and work plan

Prepared November 5, 2026 for a presentation due November 6, 2026.

> Progress update, November 5 at approximately 6:40 PM Eastern: tools are now installed, the bitstream is recovered, and a baseline probe reproduces the supplied test pair. The PDF's encryption formula matches mode 1, while the host script calls mode 0 encryption. See `../HANDOFF.md` for verified results, current files, remaining tasks, and a revised timeline. Earlier progress snapshots and mismatch hypotheses below describe the planning stage.

## Scope and recommendation

This is a solo project. The student has prior hardware experience from Jane Street's ASIC competition and access to a Hackster board. Tomorrow's expectation is simulation. Treat the ASIC work as relevant background, with its own results and scope.

The recommended project is **AI-assisted recovery and controlled modification of an FPGA cryptographic accelerator**. The first goal is a trustworthy simulation of the supplied design. If that works in time, add one small AI-generated Trojan and demonstrate the difference between ordinary and triggered behavior.

For tomorrow, prioritize a reproducible baseline and a clear account of the evidence. A working Trojan is a stretch goal until the baseline passes. Keep the board available for a later hardware milestone.

The presentation brief asks for approximately 5-10 minutes. Target eight slides and about 7 minutes 40 seconds. Address every requested topic, and label completed work, supplied information, and proposed work accurately.

## What the repository contains

| Source | What it contributes |
| --- | --- |
| `presentation-instructions.txt` | Class presentation length and questions to address |
| `README.md` | Competition overview, dates, AI logging requirement, recommended tools, board documentation links |
| `qualifier/README.md` | Simulation challenge, AI-only hardware rule, deliverables, scoring, supplied solution diagrams |
| `qualifier/ice40_bitstream.bin` | FPGA configuration to recover and study |
| `qualifier/ice40_cryptographic_IP.md` | SPI ports, reset, clock, start, busy, and transfer protocol |
| `qualifier/spi_ice40_crypto_ip_test.py` | MicroPython host example, SPI setup, GPIO names, and a plaintext/ciphertext test pair |
| `qualifier/docs/les_block_diagrams.pdf` | Four pages covering the top level, encryption, decryption, and round controller; the PDF explicitly prints the embedded key |
| `qualifier/docs/les_block_diagrams-0.png` through `-3.png` | Existing diagram images; use the PDF when the small labels matter |
| `finals/README.md` | Later hardware demonstration and two further challenges whose details are not supplied here |
| `.gitignore`, `LICENSE` | Repository exclusions and reuse terms |

At review time, the checkout contains no recovered Verilog, simulation testbench, Trojan, AI transcript directory, or student results. The presentation instructions are an existing untracked file. The bitstream was identified and hashed, but has not been unpacked or simulated during this planning pass.

The machine is Apple Silicon. `iverilog` and `vvp` are available in the current shell. `iceunpack`, `icebox_vlog`, `yosys`, and `nextpnr-ice40` were not found on its current PATH. They may exist in an unactivated tool installation.

Input bitstream SHA-256:

```text
5fa5fda9768c36808780398d8e24d125d860aacc62b61af8b4c5124dd759ddbe
```

## Technical starting point

The documented system is an RP2040 communicating over SPI with a Lattice iCE40-UP5K FPGA. The data path handles 32-bit words. SCK clocks the internal logic as well as SPI, so computation needs clock pulses even while chip select is inactive. The documented maximum SCK frequency is 1 MHz. Reset is synchronous and active low.

The supplied diagrams describe a custom four-round cipher using byte rotations, AES substitution boxes, and a fixed 32-bit key. The cipher uses AES components but does not implement standard AES encryption.

The PDF gives `K = 0x8E043CB1` and these round functions:

```text
Encryption: x[0] = plaintext
            x[i+1] = AES_inverse_Sbox_per_byte(ROTR32(x[i], 8)) XOR K
            ciphertext = x[4]

Decryption: y[0] = ciphertext
            y[i+1] = ROTL32(AES_Sbox_per_byte(y[i] XOR K), 8)
            plaintext = y[4]
```

These are supplied reference descriptions. Recovering and testing the actual netlist remains necessary before claiming that the bitstream implements them.

### Discrepancies to investigate first

| Issue | Evidence | What to do |
| --- | --- | --- |
| Mode polarity | Interface documentation and MicroPython use `ENC_DEC=0` for encryption. The top-level diagram labels `1` as encryption. | Exercise both values against the recovered design and record the actual mapping. |
| Execution and readback timing | Documentation says processing takes four clocks. Script comments describe three additional clocks, but the loops issue seven. The diagram includes a registered busy-fall detector and SPI load logic. | Capture START, SCK, BUSY, load, and MISO. Distinguish cipher completion from when the result becomes available for readback. |
| Cipher description versus sample vector | The script expects `0x59C359C3` to encrypt to `0x9CD84392`. A direct software transcription of the PDF's four rounds and key produces `0x137B1F72`. | Treat this as a reference mismatch to resolve with the recovered netlist. Check mode, bit order, round count, key, and load timing. Do not change the expected result just to get a passing test. |
| Key loading | The qualifier introduction mentions sending keys. The interface documents no key-loading operation, and the PDF shows a fixed key. | Avoid claiming a runtime key-loading protocol unless the recovered design demonstrates one. |
| Pin mapping | The host script lists RP2040 GPIO numbers. The repository contains no FPGA pin constraint file. | Map FPGA I/O using the relevant board schematic or constraints and confirm behavior. RP2040 GPIO numbers are not FPGA package pin numbers. |

The arithmetic sanity check also produced `decrypt(0x9CD84392) = 0xDD04D7AC`. Its encryption round values were `0xBD110FA4`, `0x93C9DF4A`, `0xD2262E5E`, and `0x137B1F72`. The reference S-box matched the standard first sixteen AES entries, was bijective, and the encryption/decryption functions passed both round-trip directions on more than 1,000 inputs. This checks the transcription's internal consistency. It does not establish the behavior of the FPGA bitstream.

## Work plan before tomorrow

The presentation time is not yet specified. Allow roughly 9-11 focused hours for the full scope, with recovery taking the largest uncertain share. The clock-time schedule below targets a narrower scope in 8 hours 45 minutes including a break, with scope cutoffs to keep it bounded. Protect the last 90 minutes for the deck and rehearsal. If less time remains, reduce the Trojan work first.

| Block | Budget | Work | Evidence to retain |
| --- | --- | --- | --- |
| 1. Setup and provenance | 30-45 min | Activate or install the appropriate OSS CAD Suite, check tool versions, preserve the supplied binary, start complete AI logs, and create working directories. | Tool versions, input hash, first transcript, initial status list |
| 2. Bitstream recovery | 90-120 min | Unpack the binary to IceStorm ASCII, export structural Verilog, inspect active I/O and logic, establish a named top-level interface. | Commands, untouched structural Verilog, port map, notes on unresolved signals |
| 3. Baseline simulation | 2-3 hr | Ask AI to generate a self-checking testbench based on the host script. Check reset, SPI shift readback, both modes, exact clock sequence, and the supplied vector. Investigate the source discrepancies. | Simulator output, waveforms, actual mode mapping, result-loading timing |
| 4. One Trojan and validation | 90-120 min, only after the baseline works | Ask AI to add the small proposed Trojan and an exploit test. Compare modified and unmodified behavior with the same ordinary inputs and with the trigger. | Patch, full generation history, ordinary/triggered/near-miss results |
| 5. Analysis and reproducibility | 45-60 min | Summarize what passed, what remains unresolved, and what each waveform establishes. If available, compare synthesized resources under the same flow. | Short result table, reproduction command, measured resource counts or an explicit pending item |
| 6. Slides and rehearsal | At least 90 min | Build the eight slides from actual evidence, rehearse to 7-8 minutes, export a stable copy, and add the presentation and supporting material to the intended project repository. | Editable deck, PDF export, source references, final status |

### Schedule starting this evening

The current time was checked at approximately 4:56 PM Eastern on Thursday, November 5. These are estimates, with completion targeted for 1:45 AM Friday and a short final check before the presentation. The exact presentation time remains unknown.

| Step | Eastern time | Action and completion target |
| --- | --- | --- |
| 1 | Thu 5:00-5:30 PM | Activate recovery/simulation tools, create working folders, and start complete AI records. Finish with usable tool commands and preserved input provenance. |
| 2 | Thu 5:30-7:00 PM | Unpack the bitstream and export structural Verilog. Inspect active I/O and begin the signal map. Finish with the untouched recovered circuit and documented mapping evidence. |
| Break | Thu 7:00-7:30 PM | Meal and break. |
| 3 | Thu 7:30-9:30 PM | Generate and run the baseline testbench. Check reset, SPI readback, both modes, result availability, and the disputed sample vector. Finish with a trustworthy baseline or a precise, evidenced blocker. |
| 4 | Thu 9:30-10:45 PM | If the baseline works, generate one small Trojan and its trigger test. If the baseline remains unresolved, use this block to investigate it and document the Trojan proposal. |
| 5 | Thu 10:45-11:30 PM | Validate the working implementation. For a Trojan, cover ordinary inputs, the trigger, a near miss, reset, and return to ordinary operation. For a baseline-only result, consolidate reproducible tests and the diagnosis. |
| 6 | Thu 11:30 PM-Fri 12:00 AM | Freeze technical scope. Save result tables, readable waveforms, one actual AI exchange, and a short explanation of completed versus proposed work. |
| 7 | Fri 12:00-1:15 AM | Build the eight-slide deck from the saved evidence. Include sources, the actual AI workflow, taxonomy, solo responsibilities, and remaining work. Export editable and PDF versions. |
| 8 | Fri 1:15-1:45 AM | Rehearse to 7-8 minutes, cut excess detail, verify both exports, and add the final presentation to the intended project repository. |
| Final check | Fri, 30-45 minutes before the presentation | Open the final deck, verify submitted files, rerun the documented demonstration if practical, and review likely questions. |

**9:30 PM decision:** A trustworthy baseline is the condition for attempting the Trojan. Source discrepancies resolved through recovered-design evidence are a valid baseline result. An unexplained failing test is a reason to retain the Trojan as proposed work.

**Midnight cutoff:** Slide authoring starts with the evidence already available. The 1:45 AM target includes 105 minutes for slides and rehearsal. Treat 2:00 AM as a small packaging buffer, rather than additional implementation time.

### Decision points

- **After recovery:** If pin mapping or structural simulation is blocked, capture the exact blocker and the recovered artifacts. A behavioral model derived from the diagrams can help investigation, but label it separately from a bitstream-derived model.
- **After roughly four to six hours:** If there is no trustworthy baseline, keep working on baseline diagnosis and use the Trojan as a proposal in the presentation. Avoid modifying an unexplained failing baseline.
- **At least 90 minutes before stopping:** Freeze the technical scope and prepare the slides. Present the last reproducible state.

### First recovery commands

After the tools are activated, the initial route is:

```sh
mkdir -p build/recovered
iceunpack qualifier/ice40_bitstream.bin build/recovered/design.asc
icebox_vlog -n recovered_top build/recovered/design.asc > build/recovered/raw.v
icebox_explain build/recovered/design.asc > build/recovered/configuration.txt
```

Check the installed tools' help and retain their versions. These are a proposed starting sequence, not commands already run in this checkout. Port mapping, the correct package information, and any necessary primitive models still need attention. `icebox_vlog` exports an equivalent low-level circuit rather than the original named RTL hierarchy.

Use Yosys for inspection and, later, a consistent synthesis comparison. Use Icarus Verilog plus `vvp` for simulation and a waveform viewer such as GTKWave for inspection. nextpnr and programming the board belong to a later hardware milestone unless simulation finishes comfortably early.

Tool guidance was checked against the primary [IceStorm overview](https://prjicestorm.readthedocs.io/en/latest/overview.html), [icebox_vlog source](https://github.com/YosysHQ/icestorm/blob/main/icebox/icebox_vlog.py), and [OSS CAD Suite installation instructions](https://github.com/YosysHQ/oss-cad-suite-build#installation).

## Recommended Trojan scope

Start with a **rare input-sequence trigger and a one-result integrity payload** in the supplied educational accelerator. The trigger recognizes a deliberately chosen sequence of complete input transactions. The payload changes a selected bit of one result through the existing output path. Specify how the trigger resets, what happens on a wrong sequence, and how ordinary operation resumes before asking AI to implement it.

This choice gives a compact, observable simulation objective. Resource overhead and accidental activation remain things to measure. A key-disclosure payload through the existing SPI output can be a later extension after the simple case works.

| Taxonomy dimension | Proposed classification |
| --- | --- |
| Insertion stage and abstraction | Design-time modification of recovered RTL |
| Trigger | Digital, input-controlled, sequential trigger across transactions |
| Payload | Functional corruption of an output word |
| Security property affected | Integrity |
| Observation path | Existing SPI MISO output |
| Persistence | One-result effect followed by specified normal operation |
| Stealth evidence | Ordinary test behavior, near-miss behavior, and measured synthesis overhead |

All of this remains proposed until implemented and tested. A small design does not by itself prove stealth.

### Minimum evidence for a working Trojan claim

1. The unmodified recovered design passes the baseline checks or has a precisely documented, independently justified reference correction.
2. The modified design matches the baseline for a reproducible set of ordinary encryption and decryption transactions.
3. The intended sequence activates the payload, and the testbench asserts the observed output difference.
4. Near-miss sequences, reversed order, and reset behavior follow the specification.
5. The next ordinary transaction behaves as specified after the payload.

Record test counts and seeds. Report only the coverage actually run. Simulation demonstrates the tested cases, not universal equivalence.

## AI workflow and records

The challenge requires AI-generated hardware and exploit code, plus complete interaction logs. The student can specify requirements, inspect evidence, and evaluate designs. Ask AI to generate and revise the RTL and exploit testbench, including fixes, and retain the corresponding prompts and responses.

Use a single organized workflow before adding elaborate automation:

1. Supply the interface documentation, host test, recovered structural Verilog, and tool outputs as separate, named inputs. Give the model relevant text and diagram content rather than treating raw binary bytes as meaningful RTL.
2. Request an evidence-based port map and behavior explanation. Ask it to identify uncertain claims and source contradictions explicitly.
3. Generate the baseline testbench, run it, and return the exact errors and waveforms for diagnosis.
4. Once the baseline is stable, provide the trigger/payload specification and ask for a minimal RTL change plus self-checking exploit tests.
5. Feed actual test results back for revisions. Preserve each version and the evidence used to accept it.

For each interaction, retain the actual model identifier, date, interface used, full prompt, supplied context, full response, generated files, tool commands, and outcomes. Save this planning conversation too. Do not imply that this plan has automatically captured a complete submission-ready transcript.

For the guardrails question, report what actually occurred. If there was no refusal or bypass attempt, state that. If a model refused a request, retain the exchange and describe the outcome accurately. A clearly described contest setting is context, not evidence that a safeguard was bypassed.

The rubric gives AI usage 35 points, Trojan quality 25, automation 15, documentation 15, and simulation 10. Complete logs and a traceable generate-test-revise process are valuable even with a small implementation. Add automation only after a working manual sequence exists.

## Eight-slide presentation outline

These are content slots, not completed slide copy. Update the results and status immediately before building the deck.

| Slide | Title | Time | Main content and evidence |
| --- | --- | --- | --- |
| 1 | AI-assisted analysis of an FPGA cryptographic accelerator | 0:40 | State the challenge and current milestone. Add name and NYU Design Project. Briefly mention prior ASIC experience as background. |
| 2 | Accelerator architecture | 1:00 | Show the supplied top-level diagram. Explain the RP2040/SPI connection, 32-bit data, shared clock, and four-round custom cipher. Credit the supplied solution. |
| 3 | Bitstream recovery and open tools | 1:05 | Explain binary unpacking, structural Verilog export, signal mapping, and simulation. Show actual commands or a short recovered-code excerpt. Distinguish planned steps from completed ones. |
| 4 | Baseline verification and source discrepancies | 1:00 | Show the expected sample pair, actual observed behavior, mode/timing findings, and one readable waveform or result table. If unresolved, state the specific discrepancy and next test. |
| 5 | AI inputs and generation workflow | 1:00 | Show one real prompt/context excerpt, its generated output, and the test feedback used for revision. Include actual model/interface and logging practice. Answer the guardrails question with the actual experience. |
| 6 | Trojan design and taxonomy | 1:10 | Explain the selected trigger, payload, insertion point, reset behavior, and classification. Mark it proposed if it is not yet running. |
| 7 | Simulation results | 1:00 | Compare baseline, modified ordinary operation, triggered operation, and a near miss. Include measured counts and overhead only if available. If no Trojan runs, use this slide for completed baseline evidence and pending validation. |
| 8 | Solo responsibilities and next milestone | 0:45 | State the student's design/verification responsibilities and AI's code-generation role. List completed and remaining work, with hardware demonstration as a later milestone. |

Total planned speaking time: **7:40**. For a five-minute slot, combine slides 3-4 and 6-7 and shorten the opening. For ten minutes, retain eight slides and allow more explanation of the evidence. Keep lengthy code and additional waveforms in backup material only if useful.

### Coverage of the professor's questions

| Requested topic | Location |
| --- | --- |
| What has been done so far | Slides 1, 4, 7, and 8, using consistent status wording |
| How the bitstream was reverse engineered | Slide 3 |
| How information reached the LLM | Slide 5 |
| Which open tools were used | Slide 3, with tool versions in supporting material |
| What the bitstream implements | Slides 2 and 4, distinguishing supplied descriptions from recovered evidence |
| Trojan and taxonomy | Slide 6 |
| LLM guardrails | Slide 5, reporting actual interactions |
| Division of labor | Slide 8, explicitly describing a solo project |
| Presentation in GitHub | Add the final deck to the intended project repository before submission |

## Evidence and repository checklist

Suggested working locations are `rtl/`, `tb/`, `ai/`, `scripts/`, `build/`, `docs/`, and `presentation/`. These directories are a proposal, not files already created by this plan. The current ignore rules exclude some nested `src` paths, so verify that intended source files appear in Git status.

- [ ] Preserve the original bitstream and hash.
- [ ] Save recovered low-level Verilog separately from AI-refactored or modified RTL.
- [ ] Retain the port map and its evidence.
- [ ] Save full AI interactions and actual tool/model versions.
- [ ] Capture a readable baseline waveform and simulator result.
- [ ] Capture ordinary, triggered, and near-miss evidence if the Trojan works.
- [ ] Record measured resource counts, or explicitly mark them pending.
- [ ] Save the editable deck and a PDF export in `presentation/`.
- [ ] Include sources for diagrams and external facts in slide notes.
- [ ] Credit any reused Hackster schematic with the attribution specified in the repository: "Hammond Pearce, UNSW Sydney - CC BY-SA 4.0".
- [ ] Verify that the presentation is in the intended student repository and opens correctly.
- [ ] Rehearse once for timing and once for questions.

## Claims to keep precise

- The key is disclosed in the supplied PDF. Independent extraction from the bitstream is a separate result.
- The existing diagrams are supplied solution material. Reading them does not establish independent reverse engineering.
- A diagram-based behavioral model and bitstream-derived structural model have different provenance.
- A waveform should establish a specific behavior, such as result availability or trigger activation.
- Prior Jane Street ASIC work is relevant experience, with separate project results.
- Board access enables later testing. Tomorrow's results should say simulation unless hardware testing actually occurs.
- The class presentation on November 6 is distinct from the competition schedule in the repository. The supplied finals document leaves two challenges unspecified.

The immediate next task is **activate the recovery tools, export structural Verilog, and build an AI-generated baseline testbench that resolves the mode, clock timing, and sample-vector discrepancies**.
