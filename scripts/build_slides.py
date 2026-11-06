#!/usr/bin/env python3
"""Build the 8-slide deck from one content source.

Outputs (under presentation/):
  slides/slideN.svg   editable per-slide sources (1280x720, 16:9)
  CSAW2026-trojan.pdf  combined PDF (via rsvg-convert)
  CSAW2026-trojan.html self-contained on-screen deck with speaker-notes panel
  speaker-notes.md     the speaker notes, standalone

Figures (presentation/figures/*.svg) are embedded inline so the PDF is
self-contained. Run scripts/run_all.sh first so the figures exist.
"""
import html
import os
import re
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRES = ROOT / "presentation"
SLIDES = PRES / "slides"
FIG = PRES / "figures"
SLIDES.mkdir(parents=True, exist_ok=True)

W, H = 1280, 720
C = dict(
    bg="#0f1724", panel="#16213a", panel2="#1c2b4a",
    blue="#4f8cff", green="#34d399", red="#f87171",
    text="#e8eefc", muted="#9fb0cc", amber="#fbbf24",
    line="#2a3a5c",
)


def esc(s):
    return html.escape(str(s), quote=True)


def embed_figure(path, x, y, w, h):
    """Inline an external SVG's inner content into a translated/scaled group."""
    src = Path(path).read_text()
    m = re.search(r"<svg[^>]*?width=\"([\d.]+)\"[^>]*?height=\"([\d.]+)\"", src)
    sw, sh = (float(m.group(1)), float(m.group(2))) if m else (940.0, 298.0)
    inner = re.sub(r"^.*?<svg[^>]*>", "", src, count=1, flags=re.S)
    inner = re.sub(r"</svg>\s*$", "", inner, flags=re.S)
    s = min(w / sw, h / sh)
    tx = x + (w - sw * s) / 2
    ty = y + (h - sh * s) / 2
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#ffffff"/>'
            f'<g transform="translate({tx:.1f},{ty:.1f}) scale({s:.4f})">{inner}</g>')


def wrap(textstr, width):
    out = []
    for para in textstr.split("\n"):
        out.extend(textwrap.wrap(para, width=width) or [""])
    return out


def bullets_svg(items, x, y, col_w, size=22, lh=33, gap=13):
    """Render bullet list; items may be (text, color) or str."""
    parts = []
    cy = y
    cpl = max(16, int(col_w / (size * 0.50)))
    for it in items:
        txt, color, sub = (it + (False,))[:3] if isinstance(it, tuple) else (it, C["text"], False)
        bx = x + (22 if sub else 0)
        marker_col = color if color else C["blue"]
        lines = wrap(txt, cpl - (2 if sub else 0))
        parts.append(f'<circle cx="{bx+6}" cy="{cy-8}" r="{4 if not sub else 3}" fill="{marker_col}"/>')
        for i, ln in enumerate(lines):
            parts.append(f'<text x="{bx+22}" y="{cy}" font-size="{size}" '
                         f'fill="{C["text"] if not sub else C["muted"]}">{esc(ln)}</text>')
            cy += lh
        cy += gap
    return "\n".join(parts), cy


def tag(x, y, label, color):
    w = 14 + len(label) * 9
    return (f'<rect x="{x}" y="{y-18}" width="{w}" height="26" rx="13" '
            f'fill="none" stroke="{color}" stroke-width="1.4"/>'
            f'<text x="{x+w/2}" y="{y}" font-size="15" text-anchor="middle" '
            f'fill="{color}">{esc(label)}</text>')


def frame(num, kicker, title, body_svg, time_label):
    accent = C["blue"]
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">
<rect width="{W}" height="{H}" fill="{C['bg']}"/>
<rect x="0" y="0" width="12" height="{H}" fill="{accent}"/>
<text x="64" y="62" font-size="18" fill="{accent}" letter-spacing="2">{esc(kicker)}</text>
<text x="64" y="112" font-size="40" font-weight="bold" fill="{C['text']}">{esc(title)}</text>
<line x1="64" y1="134" x2="{W-56}" y2="134" stroke="{C['line']}" stroke-width="1.5"/>
{body_svg}
<text x="{W-56}" y="{H-28}" font-size="15" text-anchor="end" fill="{C['muted']}">CSAW 2026 AI Hardware Attack Challenge — NYU Design Project</text>
<text x="64" y="{H-28}" font-size="15" fill="{C['muted']}">{num}/8 · {esc(time_label)}</text>
</svg>'''


def title_slide():
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Helvetica,Arial,sans-serif">
<rect width="{W}" height="{H}" fill="{C['bg']}"/>
<rect x="0" y="0" width="{W}" height="8" fill="{C['blue']}"/>
<rect x="0" y="{H-8}" width="{W}" height="8" fill="{C['red']}"/>
<text x="64" y="210" font-size="20" fill="{C['blue']}" letter-spacing="3">CSAW 2026 · AI HARDWARE ATTACK CHALLENGE (QUALIFIER)</text>
<text x="64" y="300" font-size="58" font-weight="bold" fill="{C['text']}">An AI-generated hardware Trojan</text>
<text x="64" y="366" font-size="58" font-weight="bold" fill="{C['text']}">in a recovered iCE40 crypto core</text>
<text x="64" y="440" font-size="26" fill="{C['muted']}">Bitstream recovery → verified baseline → Trojan → simulated exploit</text>
<text x="64" y="556" font-size="22" fill="{C['text']}">Vaughn — NYU Design Project (solo)</text>
<text x="64" y="590" font-size="19" fill="{C['muted']}">AI collaborators: GPT-6.1 (recovery) · Claude Opus 4.8 (baseline, Trojan, exploit)</text>
<text x="64" y="624" font-size="19" fill="{C['muted']}">Tools: OSS CAD Suite (IceStorm, Yosys, Icarus Verilog), Python</text>
<text x="{W-56}" y="{H-30}" font-size="16" text-anchor="end" fill="{C['muted']}">2026-11-06</text>
</svg>'''
    return svg


# ---------------- slide content ----------------
SPK = {}

def build():
    slides = []

    # Slide 1 (title acts as 0; outline slide 1 = goal+progress)
    slides.append(("title", title_slide()))

    # Slide: goal + progress
    b, _ = bullets_svg([
        ("Goal: recover the supplied FPGA crypto IP, verify it, then have AI insert and exploit one hardware Trojan.", C["blue"]),
        ("Bitstream recovered; cipher reconstructed; self-checking baseline passes 127/127.", C["green"]),
        ("AI-generated Trojan + exploit: 140/140 simulation checks; waveforms + resource diff captured.", C["green"]),
        ("Confirmed end-to-end on the real Hackster board: dormant in normal use, payload fires on cue.", C["green"]),
        ("One reproducible command regenerates every simulation result.", C["amber"]),
    ], 64, 182, W-128)
    slides.append(("p1", frame(1, "FINDINGS OVERVIEW", "Project goal and what we found", b, "0:40")))
    SPK[1] = ("Our IP core is a small crypto accelerator delivered only as an FPGA bitstream. "
              "The project is a three-part arc: recover an inspectable circuit, prove we understand its normal behavior, "
              "then use AI to insert and demonstrate a hardware Trojan. All three are done. The baseline passes 127 "
              "self-checks, the Trojan and its exploit pass 140, and a single script reproduces every simulation result. "
              "We also took the attack all the way onto the physical Hackster board: it behaves exactly like the clean "
              "core until a secret input sequence fires the payload. These slides walk through those findings.")

    # Slide: architecture + ordinary transaction
    b, _ = bullets_svg([
        ("32-bit, 4-round block cipher. Raw SPI peripheral + sideband control (no AXI/Wishbone).", C["blue"]),
        ("Unified clock: SCK drives both the SPI shift register and the crypto engine.", C["text"]),
        ("Transaction: reset → shift 32 bits in (CS low) → pulse START → wait → shift 32 bits out.", C["text"]),
        ("BUSY high through edges 1-3, low from edge 4; result loads on edge 5.", C["green"]),
        ("ENC_DEC: 0 = encrypt, 1 = decrypt. BUSY is mirrored on ICE_LED.", C["muted"]),
    ], 64, 182, 600)
    fig = embed_figure(FIG / "wave_normal.svg", 704, 196, 512, 300)
    slides.append(("p2", frame(2, "WHAT IT DOES", "Accelerator architecture & ordinary transaction", b + fig, "1:00")))
    SPK[2] = ("The core takes a 32-bit word over SPI, where the RP2040 is the controller and the FPGA is the peripheral. "
              "It deliberately avoids a heavy bus. The key architectural quirk is a unified clock domain: the same SCK that "
              "shifts SPI bits also clocks the cipher. A normal transaction loads 32 bits with chip-select low, pulses START, "
              "then reads 32 bits back. The waveform on the right is from our simulation: BUSY asserts with START, stays high "
              "for three clock edges, and drops at edge four — but note the result only becomes readable at edge five, which "
              "matters later.")

    # Slide: recovery + tools
    b, _ = bullets_svg([
        ("iceunpack bitstream → .asc (device 5k); icebox_vlog → structural Verilog (~3.2k lines, 9 ports, 4 block RAMs).", C["blue"]),
        ("recover.py is deterministic: records input SHA-256 + exact commands; asserts the circuit body is byte-identical.", C["green"]),
        ("Only edit: ANSI→non-ANSI scalar port headers so Icarus accepts the netlist. Memory primitives via cells_sim.v.", C["text"]),
        ("Open tools only: OSS CAD Suite — IceStorm, Yosys, Icarus Verilog — plus Python. No vendor tools.", C["amber"]),
        ("Supplied vs independent: bitstream + datasheet + solution PDF are supplied; the netlist + analysis are ours.", C["muted"]),
    ], 64, 182, W-128)
    slides.append(("p3", frame(3, "REVERSE ENGINEERING", "Bitstream recovery and open tools", b, "1:05")))
    SPK[3] = ("We start from only the .bin. iceunpack turns it into an ASCII config — that's how we learn it's the 5k device — "
              "and icebox_vlog lifts it to a structural Verilog netlist with nine ports and four block RAMs. Our recover.py is "
              "content-addressed: it hashes the input, logs every command, and asserts that the one cosmetic edit we make — "
              "converting ANSI scalar port headers so Icarus will compile it — leaves the circuit body byte-for-byte unchanged. "
              "Everything is open-source: IceStorm, Yosys, Icarus Verilog. Be clear about provenance: the bitstream, the "
              "datasheet, and the solution PDF with the key and round functions were supplied; the recovered netlist and all "
              "analysis are ours.")

    # Slide: baseline verification + resolved naming
    b, _ = bullets_svg([
        ("Independent Python reference model of the two PDF round functions (AES S-box, K=0x8E043CB1, 4 rounds).", C["blue"]),
        ("Self-checking bench vs the recovered netlist: 60 inputs x 2 modes = 120/120; round-trip + reset + back-to-back.", C["green"]),
        ("Resolved the open question: NO mode/function swap. mode0 = PDF encrypt, mode1 = PDF decrypt — names agree.", C["amber"]),
        ("The earlier 'swap' came from a mis-transcribed software cipher (0x137B1F72 is really the decrypt output).", C["muted"]),
        ("Measured timing: minimum safe readback = 5 SCK edges, not 4 (BUSY-low ≠ result ready).", C["green"]),
    ], 64, 182, W-128)
    slides.append(("p4", frame(4, "TRUSTWORTHY BASELINE", "Baseline verification & resolved naming question", b, "1:00")))
    SPK[4] = ("Before touching anything, we prove we understand the normal core. I built an independent reference model of the "
              "two round functions from the solution PDF and ran 120 vectors — edge cases plus seeded random, both modes — "
              "against the recovered netlist. All pass, plus round-trip, reset, and back-to-back checks. This also settled an "
              "open question from the handoff: there is no mode-versus-name swap. Encrypt mode really is the PDF's encryption "
              "function; the earlier swap theory came from a software mis-transcription. And a concrete measured finding: the "
              "result isn't actually ready when BUSY drops at edge four — you need five edges. The host script's eight is safely "
              "conservative.")

    # Slide: AI workflow + guardrails
    b, _ = bullets_svg([
        ("Inputs to the AI: recovered netlist, the datasheet, the PDF's S-box/key/round functions, observed vectors.", C["blue"]),
        ("Generate-test-revise is logged. Real revision: first reference model failed all 4 vectors → fixed the mode mapping → passed.", C["green"]),
        ("All RTL, testbenches, scripts, and waveplots are AI-generated; the human reviews, runs, and accepts.", C["text"]),
        ("Guardrails — honest account: no refusal and no bypass. In a sanctioned academic context the model built the Trojan directly.", C["amber"]),
        ("Only 'guardrail-like' behavior was voluntary: narrow scope, Trojan logic labeled, stealth stated as detectable.", C["muted"]),
    ], 64, 182, W-128)
    slides.append(("p5", frame(5, "AI USAGE", "AI inputs, generate–test–revise, guardrails", b, "1:00")))
    SPK[5] = ("The challenge is really about AI usage, so we log it. The AI received the recovered netlist, the datasheet, the "
              "supplied S-box, key and round equations, and the observed vectors. The process is generate-test-revise and it's "
              "recorded — the clearest example: my first reference model failed all four known vectors because the mode mapping "
              "was backwards; the test output drove the fix, and it then passed. Every line of RTL and every testbench is "
              "AI-generated; I review and run them. On guardrails, the honest answer is the interesting one: nothing refused this "
              "and I used no bypass. Given an authorized academic security context, the model generated the Trojan trigger and "
              "payload directly. The only safety-shaped behavior was self-imposed — keeping it tiny, labeling the malicious code, "
              "and reporting honestly that it's detectable rather than claiming it's invisible.")

    # Slide: trojan design + taxonomy
    b, _ = bullets_svg([
        ("Insertion: design-time, RTL source. Diff crypto_core_clean.v vs crypto_core_trojan.v = the whole change.", C["blue"]),
        ("Trigger: digital, input-controlled, SEQUENTIAL — rare ordered 3-word sequence 13375EED → C0DEFACE → A5A5A5A5.", C["red"]),
        ("Any wrong completed transaction resets progress; a word = SEQ0 restarts it; RST_N dis-arms.", C["text"]),
        ("Payload: functional corruption, INTEGRITY — invert output bit 0 of exactly ONE result.", C["red"]),
        ("Channel: the EXISTING SPI output — no added ports. Added state: 32-bit input capture + 2-bit counter.", C["muted"]),
    ], 64, 182, W-128)
    slides.append(("p6", frame(6, "THE TROJAN", "Trigger, payload, insertion point & taxonomy", b, "1:10")))
    SPK[6] = ("The Trojan is inserted at design time into readable RTL, so a two-file diff is the entire modification. The trigger "
              "is a sequential, input-controlled one: it only arms after three specific 32-bit words arrive in order, each as a "
              "completed transaction. Any wrong word resets progress, and a hardware reset dis-arms it — so it's rare and "
              "controllable. The payload is deliberately surgical: it inverts a single output bit on exactly one result, delivered "
              "through the existing SPI output path, so there are no new pins. In taxonomy terms: design-time RTL insertion, "
              "digital sequential trigger, functional-corruption integrity payload, existing channel, one-result scope. The cost is "
              "just a capture register and a two-bit counter.")

    # Slide: evidence + limitations
    b, _ = bullets_svg([
        ("Dormant: 120 ordinary vectors bit-identical to the golden core. Fires: 0x4f92e7f9 → 0x4f92e7f8 (bit 0).", C["green"]),
        ("On the real Hackster board: ordinary test still passes; armed SEQ2 returns 4f92e7f8; recovers after.", C["green"]),
        ("Near misses, reset dis-arm, one-result scope, re-arm: all correct — 140/140 in sim.", C["green"]),
        ("Stealth is MEASURED: +96 cells (+3.4%), +34 flops — not area-invisible; a known-answer test exposes it.", C["amber"]),
        ("Coverage is extensive but not a universal-equivalence proof (seeds + counts recorded).", C["muted"]),
    ], 64, 182, 600)
    fig = embed_figure(FIG / "wave_trojan.svg", 704, 196, 512, 300)
    slides.append(("p7", frame(7, "EVIDENCE", "Simulation and on-board evidence", b + fig, "1:00")))
    SPK[7] = ("Here's the proof. On 120 ordinary transactions the Trojan core is bit-identical to the clean golden core — fully "
              "dormant. When the secret sequence completes, the output changes by exactly one bit: the waveform on the right shows "
              "the golden and Trojan serial outputs agreeing until the very last bit, which flips. Every near-miss case — wrong "
              "final word, wrong middle word, wrong order, reset in the middle — correctly suppresses the payload, and it re-arms "
              "and fires again cleanly. That's 140 checks, zero failures. And this isn't only simulation: we synthesized the Trojan "
              "to a real bitstream, flashed it to the Hackster board, and the ordinary encrypt/decrypt test still passed while our "
              "exploit sent the three-word sequence and read back the corrupted value 4f92e7f8 on real silicon, recovering right "
              "after. Crucially I measured stealth instead of assuming it: the Trojan adds about three-and-a-half percent more "
              "cells, so an area diff or a known-answer test would catch it. Simulation is thorough but not a universal proof.")

    # Slide: labor + next milestone
    b, _ = bullets_svg([
        ("Solo project. Human: requirements, scope, board, running/reviewing/accepting all code, this talk.", C["blue"]),
        ("AI collaborators do the hardware code: GPT-6.1 (recovery + first probe), Claude Opus 4.8 (baseline, Trojan, exploit, slides).", C["text"]),
        ("All hardware/exploit code is AI-generated; full prompts, code, and test feedback are kept in ai/.", C["green"]),
        ("Next step: power side-channel (CPA) to recover the key independently — board exposes ICE_PWR + ICE_TRIG.", C["amber"]),
        ("Then the finals' physical challenges. Deliverables on GitHub: RTL, testbenches, AI logs, brief, deck + PDF.", C["muted"]),
    ], 64, 182, W-128)
    slides.append(("p8", frame(8, "WRAP-UP", "Solo responsibilities & next steps", b, "0:45")))
    SPK[8] = ("Division of labor: I work solo, so I own the requirements, scope decisions, the board, and running, reviewing and "
              "accepting every piece of generated code — and giving this talk. The hardware itself is written by my AI "
              "collaborators: GPT-6.1 handled recovery and the first probe, and Claude Opus did the baseline hardening, the Trojan, "
              "the exploit, and these slides. Per the rules, all hardware and exploit code is AI-generated and I keep the full "
              "prompts, generated code, and test feedback in the repo. We already took it onto the real board — confirmed AppMicro, "
              "backed up and flashed the FPGA, reproduced the exploit on silicon, and restored the clean image. The clear next "
              "step is a power side-channel attack — correlation power analysis on the first-round S-box output — to recover the "
              "key independently from the chip rather than relying on the value the PDF supplied; the board already exposes a "
              "power tap and a trigger connector for exactly that. After that come the finals' physical challenges. Everything — "
              "RTL, testbenches, AI logs, the technical brief, and this deck — goes to my GitHub fork.")

    # write slide svgs
    paths = []
    for i, (name, svg) in enumerate(slides):
        p = SLIDES / f"slide{i+1:02d}_{name}.svg"
        p.write_text(svg)
        paths.append(p)
    return paths


def make_pdf(paths):
    out = PRES / "CSAW2026-trojan.pdf"
    subprocess.run(["rsvg-convert", "-f", "pdf", "-o", str(out)] + [str(p) for p in paths], check=True)
    return out


def make_notes():
    lines = ["# Speaker notes — CSAW 2026 Trojan talk (target ~7:40)\n"]
    titles = {1: "Goal & progress (0:40)", 2: "Architecture & transaction (1:00)",
              3: "Recovery & tools (1:05)", 4: "Baseline & naming (1:00)",
              5: "AI usage & guardrails (1:00)", 6: "Trojan & taxonomy (1:10)",
              7: "Evidence & limits (1:00)", 8: "Labor & next (0:45)"}
    for k in range(1, 9):
        lines.append(f"## Slide {k+1} — {titles[k]}\n\n{SPK[k]}\n")
    (PRES / "speaker-notes.md").write_text("\n".join(lines))


def make_html(paths):
    import base64
    embeds = []
    for p in paths:
        data = base64.b64encode(p.read_bytes()).decode()
        embeds.append(f'data:image/svg+xml;base64,{data}')
    # deck slide index (0-based): 0 = title, 1..8 = content slides SPK[1..8]
    notes_js = {str(i): SPK[i] for i in range(1, 9)}
    import json
    slides_json = json.dumps(embeds)
    notes_json = json.dumps(notes_js)
    htmldoc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CSAW 2026 Trojan deck</title>
<style>
  :root{{color-scheme:dark}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:#0a0f1a;color:#e8eefc;font-family:Helvetica,Arial,sans-serif}}
  .stage{{display:flex;flex-direction:column;align-items:center;gap:12px;padding:16px}}
  .slidebox{{width:min(100%,1100px);aspect-ratio:16/9;background:#000;border-radius:10px;overflow:hidden;box-shadow:0 10px 40px rgba(0,0,0,.6)}}
  .slidebox img{{width:100%;height:100%;display:block}}
  .bar{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:center}}
  button{{background:#16213a;color:#e8eefc;border:1px solid #2a3a5c;border-radius:8px;padding:8px 14px;font-size:15px;cursor:pointer}}
  button:hover{{background:#1c2b4a}}
  .notes{{width:min(100%,1100px);background:#111a2e;border:1px solid #2a3a5c;border-radius:10px;padding:14px 18px;font-size:15px;line-height:1.5;color:#c9d6ef}}
  .notes h3{{margin:.1em 0 .4em;color:#4f8cff;font-size:15px;letter-spacing:1px}}
  .count{{min-width:70px;text-align:center;color:#9fb0cc}}
  @media print{{.bar,.notes{{display:none}} .slidebox{{box-shadow:none;border-radius:0}}}}
</style></head><body>
<div class="stage">
  <div class="bar">
    <button onclick="go(-1)">◀ Prev</button>
    <span class="count" id="count"></span>
    <button onclick="go(1)">Next ▶</button>
    <button onclick="toggleNotes()">Toggle notes (N)</button>
  </div>
  <div class="slidebox"><img id="slide" alt="slide"></div>
  <div class="notes" id="notes"><h3>SPEAKER NOTES</h3><div id="noteText"></div></div>
</div>
<script>
  const slides={slides_json};
  const notes={notes_json};
  let i=0, showNotes=true;
  function render(){{
    document.getElementById('slide').src=slides[i];
    document.getElementById('count').textContent=(i+1)+' / '+slides.length;
    document.getElementById('noteText').textContent=notes[String(i)]||'(title slide)';
  }}
  function go(d){{i=Math.max(0,Math.min(slides.length-1,i+d));render();}}
  function toggleNotes(){{showNotes=!showNotes;document.getElementById('notes').style.display=showNotes?'block':'none';}}
  addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')go(1);else if(e.key==='ArrowLeft')go(-1);else if(e.key.toLowerCase()==='n')toggleNotes();}});
  render();
</script></body></html>'''
    (PRES / "CSAW2026-trojan.html").write_text(htmldoc)


if __name__ == "__main__":
    os.chdir(ROOT)
    paths = build()
    make_notes()
    make_html(paths)
    pdf = make_pdf(paths)
    print("slides:", len(paths))
    print("pdf:", pdf.relative_to(ROOT), f"({pdf.stat().st_size} bytes)")
    print("html:", (PRES / 'CSAW2026-trojan.html').relative_to(ROOT))
    print("notes:", (PRES / 'speaker-notes.md').relative_to(ROOT))
