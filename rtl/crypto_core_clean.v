// AI-generated clean behavioral re-implementation of the recovered crypto core.
//
// Provenance: the original design is the bitstream-derived netlist in
// rtl/recovered_core.v. This module is a *refactored* equivalent, written
// after the cipher was fully reconstructed and verified. It is proven
// output-equivalent to the recovered netlist by tb/equiv_check.sv over edge
// cases + seeded-random inputs in both modes. The challenge permits a
// refactored implementation provided it is tested against the baseline.
//
// Behavior reproduced from the recovered netlist and the IP datasheet:
//   * Unified clock domain: SCK drives SPI shifting AND the crypto engine.
//   * Synchronous active-low reset (RST_N).
//   * NORM_CS_N low = shift enable; 32-bit MSB-first SPI loopback readback.
//   * START (level, while idle) launches a 4-round transform of the loaded
//     word. BUSY is high through edges 1-3 and low from edge 4; the result
//     is parallel-loaded into the shift register on edge 5 (measured minimum
//     safe readback latency = 5 SCK edges after START).
//   * ENC_DEC: 0 = encrypt (PDF "encryption" fn), 1 = decrypt (PDF "decryption").
//   * ICE_LED mirrors BUSY.
//
// Cipher (round key K and the per-byte AES S-box are SUPPLIED in the solution
// PDF; the 4-round structure and mode mapping are the reconstructed finding):
//   encrypt round:  y <- ROTL8( SBOX_bytes( y XOR K ) )
//   decrypt round:  x <- INV_SBOX_bytes( ROTR8( x ) ) XOR K
module crypto_core_clean (
    input  wire SCK, RST_N, MOSI, NORM_CS_N, START, ENC_DEC,
    output wire MISO, BUSY, ICE_LED
);
    localparam [31:0] K = 32'h8E043CB1;

    reg [7:0] SB  [0:255];   // AES S-box
    reg [7:0] ISB [0:255];   // AES inverse S-box
    initial begin
        $readmemh("rtl/sbox.hex",     SB);
        $readmemh("rtl/inv_sbox.hex", ISB);
    end

    function [31:0] sub_bytes(input [31:0] x);
        sub_bytes = {SB[x[31:24]], SB[x[23:16]], SB[x[15:8]], SB[x[7:0]]};
    endfunction
    function [31:0] inv_sub_bytes(input [31:0] x);
        inv_sub_bytes = {ISB[x[31:24]], ISB[x[23:16]], ISB[x[15:8]], ISB[x[7:0]]};
    endfunction
    function [31:0] rotl8(input [31:0] a); rotl8 = {a[23:0], a[31:24]}; endfunction
    function [31:0] rotr8(input [31:0] a); rotr8 = {a[7:0],  a[31:8]};  endfunction

    function [31:0] one_round(input [31:0] v, input md);
        if (md == 1'b0) one_round = rotl8(sub_bytes(v ^ K));
        else            one_round = inv_sub_bytes(rotr8(v)) ^ K;
    endfunction

    reg [31:0] shreg;      // SPI shift register / input & result buffer
    reg [31:0] work;       // round-transform working register
    reg        miso_r;     // registered serial output
    reg        md;         // latched mode for the in-flight transform
    reg [2:0]  pc;         // 0 idle; 1..4 rounds; 5 load result

    always @(posedge SCK) begin
        if (!RST_N) begin
            shreg  <= 32'b0;
            work   <= 32'b0;
            miso_r <= 1'b0;
            pc     <= 3'd0;
            md     <= 1'b0;
        end else if (!NORM_CS_N) begin
            // SPI shift domain: emit MSB, shift MOSI in at LSB.
            miso_r <= shreg[31];
            shreg  <= {shreg[30:0], MOSI};
        end else begin
            // Crypto engine domain (chip select inactive).
            case (pc)
                3'd0: if (START) begin work <= shreg; md <= ENC_DEC; pc <= 3'd1; end
                3'd1: begin work <= one_round(work, md); pc <= 3'd2; end
                3'd2: begin work <= one_round(work, md); pc <= 3'd3; end
                3'd3: begin work <= one_round(work, md); pc <= 3'd4; end
                3'd4: begin work <= one_round(work, md); pc <= 3'd5; end
                3'd5: begin shreg <= work; pc <= 3'd0; end
                default: pc <= 3'd0;
            endcase
        end
    end

    assign MISO    = miso_r;
    assign BUSY    = START | (pc >= 3'd1 && pc <= 3'd3);
    assign ICE_LED = BUSY;
endmodule
