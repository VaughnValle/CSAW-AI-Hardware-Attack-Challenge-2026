# Local bench and simulation setup

> Progress update, November 5 at approximately 6:40 PM Eastern: installation, first recovery, and a baseline simulation probe are complete, and both board USB devices enumerate. See `../HANDOFF.md` for the current state and the successful simulation command including the required FPGA memory models. The initial-check descriptions below are historical snapshots.

Prepared for this Apple Silicon Mac on November 5, 2026. Allow about 45-75 minutes, depending on the 525 MB tool download and USB enumeration. Optional firmware recovery can add time.

The board is useful for a later comparison against simulation. The initial bench needs the Hackster, the Mac, and two USB data cables. Simulation runs entirely on the Mac.

## Checked on this Mac

- Architecture: `arm64`.
- Icarus Verilog and `vvp` are installed through Homebrew.
- Recovery tools and waveform viewers were not found on the active PATH.
- No Hackster USB serial device was visible at the time of the check.
- `/usr/bin/python3` is available and can be used to create a dedicated host environment.
- No tools were installed or board firmware changed while writing this guide.
- The included environment smoke test was run with the existing Icarus installation. This is separate from verification of the challenge design.

## 1. Arrange the physical bench and identify USB ports (10 minutes)

Place the board on a nonconductive surface. Use data-capable USB cables. The vendor identifies two USB-C connectors:

| Board connector | Purpose | What connects through it |
| --- | --- | --- |
| USB1, FPGA Programmer | Programmer RP2040 | FPGA configuration and the vendor programmer protocol |
| USB2, Application Microcontroller | AppMicro RP2040 | MicroPython and the challenge host application |

The [vendor setup lab](https://cgi.cse.unsw.edu.au/~cs6420/labs/lab00introduction/#step-2-hackster-pc-connection) documents both connections and says either port powers the board. Identify the silk-screen labels on your board rather than relying on left/right orientation.

With the board disconnected, run:

```sh
ls /dev/cu.*
```

Connect **USB1 only** and rerun the command. Record the new `/dev/cu.usbmodem...` device as the programmer port. Connect USB2 and record the additional device as the application port. Port names can change after replugging or resetting.

Set the two variables to the actual values you observed. The following strings are placeholders, not detected devices:

```sh
CSAW_PROG_PORT='/dev/cu.usbmodemREPLACE_PROGRAMMER'
CSAW_APP_PORT='/dev/cu.usbmodemREPLACE_APPLICATION'
```

The RP2040-to-FPGA connections are onboard. The initial setup uses the USB connectors without adding signal wires. Later measurements can use the labeled signal test points with a compatible instrument.

## 2. Prepare the project directories (5 minutes)

Open Terminal and run:

```sh
cd /Users/bon/Documents/CSAW-AI-Hardware-Attack-Challenge-2026
mkdir -p rtl tb ai scripts constraints build/recovered build/sim build/reports presentation
shasum -a 256 qualifier/ice40_bitstream.bin > build/reports/input-bitstream.sha256
```

Keep complete AI prompts, context, and responses in `ai/`. Terminal outputs and simulator reports belong in `build/reports/`. A terminal report does not replace the AI transcripts required by the competition.

The repository ignore rules now exclude `.venv/` and generated `build/` files. Source RTL, testbenches, presentation files, and intentionally saved AI records remain eligible for version control.

## 3. Install the native FPGA tool bundle (10-25 minutes)

Use the native Apple Silicon build. The verified release for this guide is [OSS CAD Suite 2026-11-05](https://github.com/YosysHQ/oss-cad-suite-build/releases/tag/2026-11-05). Its `darwin-arm64` archive is approximately 525 MB.

```sh
mkdir -p "$HOME/Downloads" "$HOME/Tools"
curl -fL --retry 3 \
  -o "$HOME/Downloads/oss-cad-suite-darwin-arm64-20261105.tgz" \
  https://github.com/YosysHQ/oss-cad-suite-build/releases/download/2026-11-05/oss-cad-suite-darwin-arm64-20261105.tgz
tar -xzf "$HOME/Downloads/oss-cad-suite-darwin-arm64-20261105.tgz" -C "$HOME/Tools"
source "$HOME/Tools/oss-cad-suite/environment"
```

If you already use a suitable OSS CAD Suite installation, activate its existing `environment` instead of extracting over it. In each new Terminal session, run the `source` command again. Keep this session-based until the workflow is working.

The publisher documents macOS activation in the [installation instructions](https://github.com/YosysHQ/oss-cad-suite-build#installation). If macOS blocks an archive downloaded through a browser, use that documented activation process. The included `activate` script may request the Mac login password.

Verify the tools:

```sh
command -v yosys iceunpack icebox_vlog icebox_explain iverilog vvp nextpnr-ice40
yosys -V
iverilog -V
nextpnr-ice40 --version
```

Prefer tools from this one bundle for the recovery flow. Save their identities:

```sh
command -v yosys iceunpack icebox_vlog icebox_explain iverilog vvp nextpnr-ice40 > build/reports/tool-paths.txt
yosys -V > build/reports/yosys-version.txt
iverilog -V > build/reports/iverilog-version.txt 2>&1
nextpnr-ice40 --version > build/reports/nextpnr-version.txt 2>&1
```

## 4. Create the board communication environment (5 minutes)

From the project root, create a virtual environment using an explicit host Python. This keeps board communication independent of the Python selected by the FPGA suite:

```sh
/usr/bin/python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install pyserial==3.5 mpremote==1.29.0
.venv/bin/python -m pip freeze > build/reports/host-python-packages.txt
.venv/bin/python -m serial.tools.list_ports -v
```

These dependencies were checked against the published package metadata. `pyserial` supplies the programmer's `serial` module. `mpremote` communicates with MicroPython, as described in the [official documentation](https://docs.micropython.org/en/latest/reference/mpremote.html).

Retain explicit `.venv/bin/...` commands in this guide. There is no need to activate the virtual environment or change the simulator's PATH.

## 5. Get the vendor programmer and check AppMicro (10 minutes)

Clone the [vendor repository](https://github.com/kiwih/hackster-programmer) outside the challenge checkout:

```sh
git clone https://github.com/kiwih/hackster-programmer.git "$HOME/Tools/hackster-programmer"
git -C "$HOME/Tools/hackster-programmer" rev-parse HEAD > build/reports/hackster-programmer-commit.txt
```

If it is already cloned, use that checkout and record its commit. The inspected upstream commit was `e664a4335e14bdef1e95b8a1a7e2f3c340777f98`; later revisions may differ.

With the actual application port assigned to `CSAW_APP_PORT`, run:

```sh
.venv/bin/mpremote connect "$CSAW_APP_PORT" resume exec "import sys; print(sys.implementation); print('Hackster AppMicro ready')"
```

Expected result: MicroPython implementation details and `Hackster AppMicro ready`. This establishes communication with AppMicro. It does not establish which FPGA image is loaded.

For an interactive prompt:

```sh
.venv/bin/mpremote connect "$CSAW_APP_PORT" repl
```

Use Ctrl-C if an application is running. Exit with Ctrl-]. Close any Thonny, serial monitor, or other session using that same port before running another connection tool.

The FPGA programmer port speaks its own protocol, so use the vendor programmer there rather than `mpremote`.

## 6. Verify the simulator and waveform output (5 minutes)

The AI-generated `tb/environment_smoke.sv` checks a clock, synchronous reset, counter behavior, and waveform generation. Run it from the project root:

```sh
iverilog -g2012 -s environment_smoke \
  -o build/sim/environment_smoke.vvp tb/environment_smoke.sv
vvp build/sim/environment_smoke.vvp
```

Expected result:

```text
ENVIRONMENT_SMOKE_PASS: reset, clock, simulation, and VCD generation work
```

The waveform is `build/sim/environment_smoke.vcd`. If the bundle supplies GTKWave:

```sh
gtkwave build/sim/environment_smoke.vcd
```

Select `environment_smoke` and add `clk`, `rst_n`, and `count`. Expect two reset cycles followed by counts 1 through 5.

If GTKWave is unavailable or fails to launch on this Mac, use [Surfer](https://surfer-project.org/), which offers a macOS ARM build and a browser viewer. Open the VCD file there. The [Icarus documentation](https://steveicarus.github.io/iverilog/usage/getting_started.html) explains the compile/run sequence.

This is an environment check. Challenge verification still requires a testbench connected to the recovered accelerator.

## 7. Start bitstream recovery (5-10 minutes for the first export)

With the OSS CAD Suite activated:

```sh
iceunpack qualifier/ice40_bitstream.bin build/recovered/design.asc
icebox_vlog -n recovered_top build/recovered/design.asc > build/recovered/raw.v
icebox_explain build/recovered/design.asc > build/recovered/configuration.txt
```

These commands follow the [IceStorm recovery flow](https://prjicestorm.readthedocs.io/en/latest/overview.html). The output is a low-level circuit with generated names, rather than the original RTL hierarchy.

The vendor example build uses the `sg48` package. After confirming your board matches that hardware, also export a version with package pin names:

```sh
icebox_vlog -l -d sg48 -n recovered_top \
  build/recovered/design.asc > build/recovered/pin_named.v
iverilog -g2012 -s recovered_top -t null build/recovered/pin_named.v
```

The final command checks elaboration only. It does not run SPI transactions or prove cryptographic correctness. If it reports missing primitive modules, retain the exact error and add the corresponding simulation models from the tool suite as appropriate.

The `-l` and `-d` options are documented in the [icebox_vlog source](https://github.com/YosysHQ/icestorm/blob/main/icebox/icebox_vlog.py). The [`sg48` package setting](https://github.com/kiwih/hackster-programmer/blob/main/examples/hackster.mk) and the following pin references come from the vendor examples.

### Starting signal map

Use this as a reference to check against the recovered circuit. The challenge's MicroPython GPIO numbers and FPGA package pin numbers are different numbering systems.

| Signal | AppMicro GPIO in challenge script | FPGA package pin in vendor SPI example |
| --- | --- | --- |
| SCK | GP6 | 36 |
| RST_N | GP7 | 34 |
| MOSI | GP8 | 32 |
| MISO | GP9 | 31 |
| NORM_CS_N | GP10 | 28 |
| START | GP12 | 27 |
| ENC_DEC | GP13 | 25, named `ENCRYPT_NDECRYPT` in vendor example |
| BUSY | GP14 | 23 |
| ICE_LED | FPGA-controlled | 38 |

Pin assignments: [vendor SPI AES constraints](https://github.com/kiwih/hackster-programmer/blob/main/examples/spi_aes/spi_aes.pcf). AppMicro GPIOs: `qualifier/spi_ice40_crypto_ip_test.py`. Confirm the challenge's mode behavior in simulation, since its supplied references disagree on polarity.

The original host script imports MicroPython's `machine`, so it runs on AppMicro. The Mac runs the Verilog simulation testbench. A plain desktop Python invocation of that script will not simulate the FPGA.

## 8. Optional hardware baseline after setup (10-15 minutes)

This step replaces the FPGA's stored configuration with the supplied challenge image. It is useful if you also want real-board observations. For tomorrow's simulation presentation, finishing steps 1-7 is sufficient environment preparation.

First retain the programmer's 256 KiB FPGA-flash readback:

```sh
.venv/bin/python "$HOME/Tools/hackster-programmer/hackster-fpga-program.py" \
  r build/reports/previous-fpga-flash-256k.bin "$CSAW_PROG_PORT"
```

This is the range read by the upstream utility. It is not a backup of either RP2040's firmware or all possible flash contents.

Then load the unmodified challenge image:

```sh
.venv/bin/python "$HOME/Tools/hackster-programmer/hackster-fpga-program.py" \
  w qualifier/ice40_bitstream.bin "$CSAW_PROG_PORT"
```

The inspected programmer writes the image, reads it back, and starts the FPGA. Inspect the complete output: its current source prints a success message even after reporting a `Data mismatch`, so a success line alone is insufficient evidence of a correct write. Any mismatch needs investigation before proceeding.

Run the provided host script on AppMicro:

```sh
.venv/bin/mpremote connect "$CSAW_APP_PORT" \
  run qualifier/spi_ice40_crypto_ip_test.py
```

Retain the exact SPI, encryption, and decryption messages. The script starts with 50 kHz SPI mode 0 and MSB-first data. Its reported pass/fail outcomes are observations to compare with simulation, especially given the documented source discrepancies. A zero process exit status alone does not establish that all checks passed.

## Troubleshooting

| Symptom | Next check |
| --- | --- |
| No new serial device | Try a known data cable and a direct USB connection. Identify ports one at a time. The vendor specifically reports some Mac USB-C-to-C enumeration issues. |
| Only one port appears | Unplug and identify each separately. Try a different cable or USB-A-to-C connection through a suitable adapter. |
| `could not enter raw repl` or timeout | Confirm `CSAW_APP_PORT` belongs to USB2 and close competing serial applications. |
| Programmer does not acknowledge | Confirm `CSAW_PROG_PORT` belongs to USB1, check cable/re-enumeration, and retain the exact error. |
| `No module named serial` | Use `.venv/bin/python` for the programmer and install `pyserial` in that same environment. |
| `No module named machine` on the Mac | Run the host script through `mpremote` on AppMicro. Use a Verilog testbench for desktop simulation. |
| `iceunpack` not found | Source the OSS CAD Suite environment in that Terminal. |
| RTL elaborates but no simulation behavior occurs | Compile and run a testbench that drives reset, SCK, SPI, and control signals. Elaborating the recovered circuit alone supplies no stimulus. |

### Firmware recovery, only if needed

The vendor's [firmware appendix](https://cgi.cse.unsw.edu.au/~cs6420/labs/lab00introduction/#appendix-re-flashing-the-firmware-on-the-hackster) distinguishes the two RP2040s. Reflashing changes the selected processor's firmware and can affect its existing application/files. Keep existing application files before restoring firmware where practical.

- **Programmer:** connect USB1, hold `PRGMR USBBT` (SW1), tap `PRGMR RESET` (SW2), release USBBT, then copy `firmware/cse-hackster-fw-2026-feb.uf2` to the newly mounted boot drive.
- **AppMicro:** connect USB2, hold `APP USBBT` (SW3), tap `APP RESET` (SW4), release USBBT, then copy `firmware/micropython-RPI_PICO-20251209-v1.27.0.uf2` to its boot drive.

Match labels and board revision to the vendor documentation. Programmer and AppMicro use different firmware images.

## Environment-ready checkpoint

You are ready to begin baseline reverse engineering when:

1. Recovery tools resolve in the active Terminal.
2. The environment smoke test prints its pass line and its VCD opens in a waveform viewer.
3. The challenge bitstream exports to structural Verilog.
4. The board's two USB ports are identified and AppMicro responds, if using the physical bench.
5. You are preserving AI transcripts and reproducible command outputs.

The next implementation task is an AI-generated accelerator testbench with named pins, synchronous reset, SPI mode-0 transfers, explicit SCK pulses during computation, and assertions for observed outputs and timing.
