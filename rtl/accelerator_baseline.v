// AI-generated named wrapper around the bitstream-derived circuit.
module accelerator_baseline (
    input wire SCK, RST_N, MOSI, NORM_CS_N, START, ENC_DEC,
    output wire MISO, BUSY, ICE_LED
);
    recovered_core core (
        .pin_36(SCK), .pin_34(RST_N), .pin_32(MOSI),
        .pin_28(NORM_CS_N), .pin_27(START), .pin_25(ENC_DEC),
        .pin_31(MISO), .pin_23(BUSY), .pin_38(ICE_LED)
    );
endmodule
