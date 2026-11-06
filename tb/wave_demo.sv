// AI-generated waveform-capture bench. Produces a compact VCD with exactly
// the signals shown on the slides: an ordinary transaction (timing) and the
// Trojan payload (golden vs trojan serial output diverging by one bit).
`timescale 1ns/1ps
module wave_demo;
    localparam [31:0] SEQ0=32'h13375EED, SEQ1=32'hC0DEFACE, SEQ2=32'hA5A5A5A5;
    reg SCK=0, RST_N=1, MOSI=0, NORM_CS_N=1, START=0, ENC_DEC=0;
    wire MISO_g, BUSY, LED_g, MISO_t, BUSY_t, LED_t;
    reg [31:0] rxg, rxt;

    crypto_core_clean  golden(.SCK(SCK),.RST_N(RST_N),.MOSI(MOSI),.NORM_CS_N(NORM_CS_N),
        .START(START),.ENC_DEC(ENC_DEC),.MISO(MISO_g),.BUSY(BUSY),.ICE_LED(LED_g));
    crypto_core_trojan trojan(.SCK(SCK),.RST_N(RST_N),.MOSI(MOSI),.NORM_CS_N(NORM_CS_N),
        .START(START),.ENC_DEC(ENC_DEC),.MISO(MISO_t),.BUSY(BUSY_t),.ICE_LED(LED_t));

    task pulse; begin #500; SCK=1; #500; SCK=0; end endtask
    task reset_both; begin SCK=0; NORM_CS_N=1; START=0; MOSI=0; RST_N=0;
        repeat(2) pulse(); RST_N=1; pulse(); end endtask
    task spi_word(input [31:0] tx); integer i; begin
        NORM_CS_N=0;
        for(i=31;i>=0;i=i-1) begin MOSI=tx[i]; #500; SCK=1; #1; rxg[i]=MISO_g; rxt[i]=MISO_t; #499; SCK=0; end
        NORM_CS_N=1; end endtask
    task run_txn(input [31:0] data, input m); begin
        ENC_DEC=m; spi_word(data); START=1; pulse(); START=0; repeat(7) pulse(); spi_word(32'b0); end endtask

    initial begin
        $dumpfile("build/sim/wave_demo.vcd");
        $dumpvars(0, wave_demo);

        // Scenario A: ordinary transaction, zoom on START->BUSY->load timing.
        reset_both(); ENC_DEC=0;
        spi_word(32'h59C359C3);
        $display("MARK A_start %0t", $time);
        START=1; pulse(); START=0;              // edge 1
        repeat(7) pulse();                      // edges 2..8
        $display("MARK A_end %0t", $time);

        // Scenario B: arm with SEQ0,SEQ1 then fire on SEQ2; capture readback.
        reset_both();
        run_txn(SEQ0,0); run_txn(SEQ1,0);
        ENC_DEC=0; spi_word(SEQ2);
        START=1; pulse(); START=0; repeat(7) pulse();
        $display("MARK B_readback_start %0t", $time);
        spi_word(32'b0);                        // 32-bit readback, golden vs trojan
        $display("MARK B_readback_end %0t", $time);
        $display("B golden=%08h trojan=%08h", rxg, rxt);
        $finish;
    end
endmodule
