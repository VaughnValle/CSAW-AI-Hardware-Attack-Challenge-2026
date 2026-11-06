# scripts/recover.py — deterministic, content-addressed recovery
sha_in = sha256(open("ice40_bitstream.bin", "rb").read())    # pin exact input

run("iceunpack  ice40_bitstream.bin  design.asc")            # .bin -> .asc
run("icebox_vlog -l -d sg48 -n recovered_core design.asc")   # -> structural netlist

# the ONLY edit: ANSI port header -> non-ANSI (Icarus compatibility)
header = "module recovered_core (" + ", ".join(ports) + ");"

# PROOF the edit is lossless: body after the header is byte-identical
assert normalized.split(";", len(ports)+1)[-1] == raw[match.end():]

manifest = {"input_sha256":  sha_in,
            "commands":      cmds,
            "output_sha256": sha256(recovered_core_v)}        # reproducible
