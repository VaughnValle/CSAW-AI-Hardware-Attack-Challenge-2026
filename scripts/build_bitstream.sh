#!/usr/bin/env bash
# Build real iCE40 UP5K (sg48) bitstreams from the clean and Trojan RTL.
# Does NOT flash — flashing/exploit commands are printed at the end.
#
#   source /Users/bon/Tools/oss-cad-suite/environment
#   bash scripts/build_bitstream.sh
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p build/hw
for t in yosys nextpnr-ice40 icepack; do
  command -v "$t" >/dev/null || { echo "ERROR: '$t' not found; source the OSS CAD Suite."; exit 2; }
done

build_one() {  # <top> <src>
  local top="$1" src="$2"
  echo "== synth $top =="
  yosys -q -p "read_verilog $src; synth_ice40 -top $top -json build/hw/$top.json"
  echo "== pnr $top (up5k/sg48, constraints/hackster.pcf) =="
  nextpnr-ice40 --up5k --package sg48 --pcf constraints/hackster.pcf \
    --json build/hw/$top.json --asc build/hw/$top.asc 2>&1 | grep -iE "Max frequency|ERROR" || true
  icepack build/hw/$top.asc build/hw/$top.bin
  echo "   -> build/hw/$top.bin ($(wc -c < build/hw/$top.bin) bytes)"
}

build_one crypto_core_clean  rtl/crypto_core_clean.v
build_one crypto_core_trojan rtl/crypto_core_trojan.v

cat <<'EOF'

Bitstreams built. To run the on-board demo (board connected):
  PROG=/dev/cu.usbmodem21401   APP=/dev/cu.usbmodem21301   # verify with: .venv/bin/python -m serial.tools.list_ports -v
  # back up current flash, then flash the Trojan image:
  .venv/bin/python ~/Tools/hackster-programmer/hackster-fpga-program.py r build/reports/previous-fpga-flash-256k.bin "$PROG"
  .venv/bin/python ~/Tools/hackster-programmer/hackster-fpga-program.py w build/hw/crypto_core_trojan.bin "$PROG"
  # ordinary behavior (dormant) then the exploit:
  .venv/bin/mpremote connect "$APP" resume run qualifier/spi_ice40_crypto_ip_test.py
  .venv/bin/mpremote connect "$APP" resume run scripts/hw_trojan_exploit.py
  # restore the clean original image afterwards:
  .venv/bin/python ~/Tools/hackster-programmer/hackster-fpga-program.py w qualifier/ice40_bitstream.bin "$PROG"
EOF
