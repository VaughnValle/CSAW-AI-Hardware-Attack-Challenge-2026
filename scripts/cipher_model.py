#!/usr/bin/env python3
"""Independent reference model for the recovered 32-bit, 4-round cipher.

SUPPLIED (from qualifier/docs/les_block_diagrams.pdf, credited to the challenge):
  - The per-byte AES S-box / inverse S-box substitution.
  - The round key K = 0x8E043CB1.
  - The two round functions, four rounds each:
        PDF "encryption":  y_next = ROTL32(SBOX_per_byte(y XOR K), 8)
        PDF "decryption":  x_next = INV_SBOX_per_byte(ROTR32(x, 8)) XOR K

INDEPENDENT FINDING (verified here and against the recovered netlist):
  There is NO naming discrepancy. The silicon maps the modes to the PDF's
  functions by their plain names:
        mode 0 (ENC_DEC=0, "encrypt") == PDF "encryption" function
        mode 1 (ENC_DEC=1, "decrypt") == PDF "decryption" function
  pdf_encrypt(0x59C359C3) == 0x9CD84392, exactly the host script's
  plaintext->ciphertext encrypt pair. The two functions are exact inverses,
  so the pair round-trips in mode 1.

  This corrects the earlier handoff hypothesis (that the modes were swapped
  relative to the PDF labels). That hypothesis came from a mis-transcribed
  software cipher: the value 0x137B1F72 attributed to "encryption" of the
  plaintext is in fact pdf_decrypt(0x59C359C3), i.e. the mode-1 output. Once
  the round functions are implemented correctly, the mode-to-name mapping is
  direct and self-consistent.

This module is a *checker and vector generator*, not hardware. The RTL is
recovered from the bitstream; this only predicts its outputs.
"""
import argparse
import random

# AES S-box (FIPS-197). Supplied substitution primitive.
SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
]
INV_SBOX = [0] * 256
for _i, _v in enumerate(SBOX):
    INV_SBOX[_v] = _i

K = 0x8E043CB1
MASK = 0xFFFFFFFF


def rotl32(x, n):
    return ((x << n) | (x >> (32 - n))) & MASK


def rotr32(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK


def sbox_bytes(x, table):
    b0 = table[(x >> 24) & 0xFF]
    b1 = table[(x >> 16) & 0xFF]
    b2 = table[(x >> 8) & 0xFF]
    b3 = table[x & 0xFF]
    return (b0 << 24) | (b1 << 16) | (b2 << 8) | b3


def pdf_encrypt(y, rounds=4):
    """PDF 'encryption' round function == silicon mode 0 (ENC_DEC=0, encrypt)."""
    for _ in range(rounds):
        y = rotl32(sbox_bytes(y ^ K, SBOX), 8)
    return y & MASK


def pdf_decrypt(x, rounds=4):
    """PDF 'decryption' round function == silicon mode 1 (ENC_DEC=1, decrypt)."""
    for _ in range(rounds):
        x = sbox_bytes(rotr32(x, 8), INV_SBOX) ^ K
    return x & MASK


def model(value, mode):
    """Predict the recovered core output for the given ENC_DEC mode."""
    return pdf_decrypt(value) if mode == 1 else pdf_encrypt(value)


# Vectors observed from the recovered netlist (build/reports/baseline-probe*.log).
OBSERVED = [
    # (mode, input, expected_output, note)
    (0, 0x59C359C3, 0x9CD84392, "host-script encrypt pair (plaintext->ciphertext)"),
    (1, 0x9CD84392, 0x59C359C3, "host-script decrypt pair (ciphertext->plaintext)"),
    (1, 0x59C359C3, 0x137B1F72, "mode 1 of the plaintext"),
    (0, 0x9CD84392, 0xDD04D7AC, "mode 0 of the ciphertext"),
]


def selftest():
    ok = True
    print("== Reference model vs. observed netlist outputs ==")
    for mode, inp, exp, note in OBSERVED:
        got = model(inp, mode)
        status = "PASS" if got == exp else "FAIL"
        ok = ok and got == exp
        print(f"  [{status}] mode={mode} in=0x{inp:08X} model=0x{got:08X} "
              f"netlist=0x{exp:08X}  ({note})")
    print("== Inverse property (mode1 and mode0 are inverses) ==")
    rng = random.Random(0xC5A2026)
    inv_ok = True
    for _ in range(100000):
        x = rng.getrandbits(32)
        if pdf_encrypt(pdf_decrypt(x)) != x or pdf_decrypt(pdf_encrypt(x)) != x:
            inv_ok = False
            print(f"  [FAIL] round-trip broke at 0x{x:08X}")
            break
    if inv_ok:
        print("  [PASS] 100000 random words: mode1(mode0(x))==x and mode0(mode1(x))==x")
    ok = ok and inv_ok
    print("RESULT:", "ALL PASS" if ok else "FAILURE")
    return 0 if ok else 1


def gen_vectors(n, seed):
    """Emit 'mode input expected' lines for the SV reference bench to load."""
    rng = random.Random(seed)
    edge = [0x00000000, 0xFFFFFFFF, 0x59C359C3, 0x9CD84392,
            0x01234567, 0x89ABCDEF, 0x80000000, 0x00000001,
            0xAAAAAAAA, 0x55555555]
    vals = edge + [rng.getrandbits(32) for _ in range(n - len(edge))]
    for v in vals:
        for mode in (0, 1):
            print(f"{mode} {v:08x} {model(v, mode):08x}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", type=int, metavar="N",
                    help="emit N test vectors (x2 modes) as 'mode in expected'")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=0xC5A2026)
    args = ap.parse_args()
    if args.gen:
        gen_vectors(args.gen, args.seed)
    else:
        raise SystemExit(selftest())
