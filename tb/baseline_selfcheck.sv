// AI-generated self-checking baseline testbench for the recovered crypto core.
//
// Goal: establish trustworthy ordinary behavior BEFORE any Trojan is inserted.
// This bench drives the bitstream-derived netlist (via accelerator_baseline)
// and checks every result against a verified reference model. The reference
// vectors in build/sim/baseline_vectors.txt are produced by
// scripts/cipher_model.py, whose mode<->function mapping was itself validated
// against the recovered netlist's observed outputs and the mutual-inverse
// property. Nothing here is hand-copied from the netlist outputs.
//
// Checks performed:
//   1. SPI shift-register readback (loopback) is exact.
//   2. Both host-script sample vectors are asserted (encrypt + decrypt pair).
//   3. 60 inputs x 2 modes (edge cases + seeded random) match the model.
//   4. Round-trip: decrypt(encrypt(x)) == x and encrypt(decrypt(x)) == x.
//   5. Timing: sweep process edges after START to find the minimum safe
//      result-readback latency (does not assume BUSY-low means "ready").
//   6. Reset clears an in-flight result; back-to-back transactions (no
//      re-reset) still produce correct results.
`timescale 1ns/1ps
module baseline_selfcheck;
    reg SCK=0, RST_N=1, MOSI=0, NORM_CS_N=1, START=0, ENC_DEC=0;
    wire MISO, BUSY, ICE_LED;
    reg [31:0] rx;
    integer pass=0, fail=0;

    accelerator_baseline dut(.*);

    task pulse; begin #500; SCK=1; #500; SCK=0; end endtask

    task reset_core;
        begin
            SCK=0; NORM_CS_N=1; START=0; MOSI=0; RST_N=0;
            repeat(2) pulse();
            RST_N=1; pulse();
        end
    endtask

    task spi_word(input [31:0] tx, output [31:0] out);
        integer i;
        begin
            NORM_CS_N=0;
            for(i=31;i>=0;i=i-1) begin
                MOSI=tx[i];
                #500; SCK=1; #1; out[i]=MISO;
                #499; SCK=0;
            end
            NORM_CS_N=1;
        end
    endtask

    // Load `data`, assert START, run `nproc` process edges, read result.
    task run_cipher(input [31:0] data, input m, input integer nproc,
                    output [31:0] result);
        reg [31:0] junk;
        integer e;
        begin
            ENC_DEC=m;
            spi_word(data, junk);
            START=1; pulse(); START=0;              // edge 1
            for(e=2;e<=nproc;e=e+1) pulse();        // edges 2..nproc
            spi_word(32'b0, result);
        end
    endtask

    task check(input [31:0] got, input [31:0] exp, input [255:0] tag);
        begin
            if(got===exp) begin
                pass=pass+1;
            end else begin
                fail=fail+1;
                $display("  [FAIL] %0s got=%08h exp=%08h", tag, got, exp);
            end
        end
    endtask

    // ---- reference vectors ----
    integer fh, code, vmode, nvec;
    reg [31:0] vin, vexp;
    integer min_safe_m0, min_safe_m1, n;
    reg [31:0] enc, dec, back;

    initial begin
        $dumpfile("build/sim/baseline_selfcheck.vcd");
        $dumpvars(0, baseline_selfcheck);

        // 1. SPI loopback readback.
        reset_core();
        spi_word(32'h59C359C3, rx);     // first write loads the shift register
        spi_word(32'h59C359C3, rx);     // second readback returns prior word
        check(rx, 32'h59C359C3, "spi_readback");

        // 2+3. Vector file: every input x both modes vs. verified model.
        fh = $fopen("build/sim/baseline_vectors.txt", "r");
        if(fh==0) $fatal(1,"cannot open baseline_vectors.txt");
        nvec=0;
        while(!$feof(fh)) begin
            code = $fscanf(fh, "%d %h %h\n", vmode, vin, vexp);
            if(code==3) begin
                reset_core();
                run_cipher(vin, vmode[0], 8, rx);
                check(rx, vexp, "vector");
                nvec=nvec+1;
            end
        end
        $fclose(fh);
        $display("VECTORS checked=%0d", nvec);

        // 4. Round-trip property on the netlist itself (not just the model).
        reset_core(); run_cipher(32'h01234567, 1'b0, 8, enc);   // encrypt
        reset_core(); run_cipher(enc,          1'b1, 8, back);  // decrypt
        check(back, 32'h01234567, "roundtrip_enc_then_dec");
        reset_core(); run_cipher(32'h89ABCDEF, 1'b1, 8, dec);   // decrypt
        reset_core(); run_cipher(dec,          1'b0, 8, back);  // encrypt
        check(back, 32'h89ABCDEF, "roundtrip_dec_then_enc");

        // 5. Timing sweep: minimum process edges for a correct readback.
        min_safe_m0=-1; min_safe_m1=-1;
        for(n=1;n<=10;n=n+1) begin
            reset_core(); run_cipher(32'h59C359C3, 1'b0, n, rx);
            $display("TIMING mode=0 nproc=%0d rx=%08h %s",
                     n, rx, (rx===32'h9CD84392)?"MATCH":"--");
            if(rx===32'h9CD84392 && min_safe_m0<0) min_safe_m0=n;
        end
        for(n=1;n<=10;n=n+1) begin
            reset_core(); run_cipher(32'h59C359C3, 1'b1, n, rx);
            $display("TIMING mode=1 nproc=%0d rx=%08h %s",
                     n, rx, (rx===32'h137B1F72)?"MATCH":"--");
            if(rx===32'h137B1F72 && min_safe_m1<0) min_safe_m1=n;
        end
        $display("MIN_SAFE_READBACK_EDGES mode0=%0d mode1=%0d",
                 min_safe_m0, min_safe_m1);

        // 6. Reset clears an in-flight result; back-to-back without re-reset.
        reset_core();
        run_cipher(32'h59C359C3, 1'b0, 8, rx);
        check(rx, 32'h9CD84392, "pre_reset_result");
        RST_N=0; pulse(); pulse(); RST_N=1; pulse();   // mid-stream reset
        spi_word(32'b0, rx);
        if(rx===32'h9CD84392) begin
            fail=fail+1;
            $display("  [FAIL] result survived reset: %08h", rx);
        end else begin
            pass=pass+1;
            $display("  [INFO] post-reset readback=%08h (result cleared)", rx);
        end
        // Back-to-back: two transactions, single reset at the top only.
        reset_core();
        run_cipher(32'h01234567, 1'b0, 8, rx);
        check(rx, 32'h70AA949E, "b2b_1");
        run_cipher(32'h89ABCDEF, 1'b0, 8, rx);
        check(rx, 32'hE1019D31, "b2b_2");

        $display("SELFCHECK_SUMMARY pass=%0d fail=%0d", pass, fail);
        if(fail!=0) $fatal(1,"baseline self-check FAILED");
        $display("BASELINE_SELFCHECK_OK");
        $finish;
    end
    initial begin #50000000; $fatal(1,"self-check timeout"); end
endmodule
