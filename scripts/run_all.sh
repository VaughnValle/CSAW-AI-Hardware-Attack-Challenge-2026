#!/usr/bin/env bash
# One reproducible command for the whole flow: recover -> baseline self-check
# -> netlist/clean equivalence -> Trojan exploit -> synth resource diff ->
# waveforms. Exits non-zero if any simulation self-check fails.
#
# Usage:
#   source /Users/bon/Tools/oss-cad-suite/environment   # provides iverilog/yosys/icebox
#   bash scripts/run_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
OSS="/Users/bon/Tools/oss-cad-suite"
CELLS="$OSS/share/yosys/ice40/cells_sim.v"
mkdir -p build/recovered build/sim build/reports

for t in iverilog vvp yosys iceunpack; do
  command -v "$t" >/dev/null || { echo "ERROR: '$t' not found. Run: source $OSS/environment"; exit 2; }
done

echo "== [1/7] Recover circuit from bitstream =="
python3 scripts/recover.py

echo "== [2/7] Reference model self-test (Python) =="
/usr/bin/python3 scripts/cipher_model.py
/usr/bin/python3 scripts/cipher_model.py --gen 60 --seed 0xC5A2026 > build/sim/baseline_vectors.txt
echo "   generated $(wc -l < build/sim/baseline_vectors.txt) reference vectors"
/usr/bin/python3 -c "import scripts.cipher_model as c; open('rtl/sbox.hex','w').write('\n'.join('%02x'%v for v in c.SBOX)+'\n'); open('rtl/inv_sbox.hex','w').write('\n'.join('%02x'%v for v in c.INV_SBOX)+'\n')"

echo "== [3/7] Baseline self-check against recovered netlist =="
iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s baseline_selfcheck \
  -o build/sim/baseline_selfcheck.vvp "$CELLS" \
  rtl/recovered_core.v rtl/accelerator_baseline.v tb/baseline_selfcheck.sv
vvp build/sim/baseline_selfcheck.vvp | tee build/reports/baseline-selfcheck.log | grep -E "SUMMARY|MIN_SAFE|OK"

echo "== [4/7] Equivalence: recovered netlist vs clean refactor =="
iverilog -g2012 -DNO_ICE40_DEFAULT_ASSIGNMENTS -s equiv_check \
  -o build/sim/equiv_check.vvp "$CELLS" \
  rtl/recovered_core.v rtl/accelerator_baseline.v rtl/crypto_core_clean.v tb/equiv_check.sv
vvp build/sim/equiv_check.vvp | tee build/reports/equiv-check.log | grep -E "SUMMARY|OK"

echo "== [5/7] Trojan exploit validation (clean golden vs trojan) =="
iverilog -g2012 -s trojan_exploit -o build/sim/trojan_exploit.vvp \
  rtl/crypto_core_clean.v rtl/crypto_core_trojan.v tb/trojan_exploit.sv
vvp build/sim/trojan_exploit.vvp | tee build/reports/trojan-exploit.log | grep -E "DORMANT|FIRE|SUMMARY|OK"

echo "== [6/7] Synthesis resource comparison (iCE40) =="
for top in crypto_core_clean crypto_core_trojan; do
  yosys -q -p "read_verilog rtl/$top.v; synth_ice40 -top $top; tee -o build/reports/synth-$top.txt stat" >/dev/null
done
cln=$(grep -E "^\s+[0-9]+ cells" build/reports/synth-crypto_core_clean.txt  | awk '{print $1}')
trj=$(grep -E "^\s+[0-9]+ cells" build/reports/synth-crypto_core_trojan.txt | awk '{print $1}')
echo "   clean=$cln cells  trojan=$trj cells  delta=$((trj-cln)) cells"

echo "== [7/7] Render waveforms =="
iverilog -g2012 -s wave_demo -o build/sim/wave_demo.vvp \
  rtl/crypto_core_clean.v rtl/crypto_core_trojan.v tb/wave_demo.sv
vvp build/sim/wave_demo.vvp > build/reports/wave-demo.log
mkdir -p presentation/figures
/usr/bin/python3 scripts/vcd_wave.py --vcd build/sim/wave_demo.vcd \
  --out presentation/figures/wave_normal.svg --t0 34000000 --t1 44000000 \
  --title "Ordinary transaction: BUSY falls at edge 4, result loads at edge 5" \
  --signals "SCK:SCK:#2563eb,NORM_CS_N:NORM_CS_N:#64748b,START:START:#16a34a,BUSY:BUSY (=ICE_LED):#dc2626"
/usr/bin/python3 scripts/vcd_wave.py --vcd build/sim/wave_demo.vcd \
  --out presentation/figures/wave_trojan.svg --t0 258500000 --t1 262000000 \
  --title "Payload: golden vs Trojan serial output differ by one bit (LSB)" \
  --signals "SCK:SCK:#2563eb,NORM_CS_N:NORM_CS_N:#64748b,MISO_g:MISO golden:#16a34a,MISO_t:MISO trojan:#dc2626"

echo
echo "ALL STAGES COMPLETE. Evidence in build/reports and presentation/figures."
