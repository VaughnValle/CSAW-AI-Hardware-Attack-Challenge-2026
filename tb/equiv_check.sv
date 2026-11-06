// AI-generated equivalence testbench: recovered netlist vs. clean refactor.
//
// Drives the bitstream-derived netlist (accelerator_baseline -> recovered_core)
// and the clean behavioral refactor (crypto_core_clean) with identical stimulus
// and asserts their SPI readback and BUSY timing agree, and that both match the
// verified reference vectors. This is the proof that the refactor is a faithful
// baseline, so Trojan comparisons against it are meaningful.
`timescale 1ns/1ps
module equiv_check;
    reg SCK=0, RST_N=1, MOSI=0, NORM_CS_N=1, START=0, ENC_DEC=0;
    wire MISO_a, BUSY_a, LED_a;   // recovered netlist
    wire MISO_b, BUSY_b, LED_b;   // clean refactor
    reg [31:0] rxa, rxb;
    integer pass=0, fail=0, busy_mismatch=0;

    accelerator_baseline netlist(
        .SCK(SCK), .RST_N(RST_N), .MOSI(MOSI), .NORM_CS_N(NORM_CS_N),
        .START(START), .ENC_DEC(ENC_DEC), .MISO(MISO_a), .BUSY(BUSY_a), .ICE_LED(LED_a));
    crypto_core_clean clean(
        .SCK(SCK), .RST_N(RST_N), .MOSI(MOSI), .NORM_CS_N(NORM_CS_N),
        .START(START), .ENC_DEC(ENC_DEC), .MISO(MISO_b), .BUSY(BUSY_b), .ICE_LED(LED_b));

    task pulse; begin #500; SCK=1; #500; SCK=0; end endtask

    task reset_both;
        begin
            SCK=0; NORM_CS_N=1; START=0; MOSI=0; RST_N=0;
            repeat(2) pulse();
            RST_N=1; pulse();
        end
    endtask

    task spi_word(input [31:0] tx);
        integer i;
        begin
            NORM_CS_N=0;
            for(i=31;i>=0;i=i-1) begin
                MOSI=tx[i];
                #500; SCK=1; #1; rxa[i]=MISO_a; rxb[i]=MISO_b;
                #499; SCK=0;
            end
            NORM_CS_N=1;
        end
    endtask

    task run_both(input [31:0] data, input m);
        integer e;
        begin
            ENC_DEC=m;
            spi_word(data);
            START=1; pulse(); START=0;
            // compare BUSY on edges 2..8 (plus the load edge) while processing
            for(e=2;e<=8;e=e+1) begin
                pulse();
                if(BUSY_a!==BUSY_b) begin
                    busy_mismatch=busy_mismatch+1;
                    $display("  [BUSY] edge=%0d netlist=%b clean=%b", e, BUSY_a, BUSY_b);
                end
            end
            spi_word(32'b0);   // readback into rxa (netlist) and rxb (clean)
        end
    endtask

    integer fh, code, vmode, nvec;
    reg [31:0] vin, vexp;

    initial begin
        $dumpfile("build/sim/equiv_check.vcd");
        $dumpvars(0, equiv_check);

        fh = $fopen("build/sim/baseline_vectors.txt", "r");
        if(fh==0) $fatal(1,"cannot open baseline_vectors.txt");
        nvec=0;
        while(!$feof(fh)) begin
            code = $fscanf(fh, "%d %h %h\n", vmode, vin, vexp);
            if(code==3) begin
                reset_both();
                run_both(vin, vmode[0]);
                if(rxa!==rxb) begin
                    fail=fail+1;
                    $display("  [FAIL equiv] mode=%0d in=%08h netlist=%08h clean=%08h",
                             vmode, vin, rxa, rxb);
                end else if(rxa!==vexp) begin
                    fail=fail+1;
                    $display("  [FAIL model] mode=%0d in=%08h dut=%08h model=%08h",
                             vmode, vin, rxa, vexp);
                end else pass=pass+1;
                nvec=nvec+1;
            end
        end
        $fclose(fh);

        $display("EQUIV_SUMMARY vectors=%0d pass=%0d fail=%0d busy_mismatch=%0d",
                 nvec, pass, fail, busy_mismatch);
        if(fail!=0 || busy_mismatch!=0) $fatal(1,"equivalence check FAILED");
        $display("EQUIV_OK netlist==clean over %0d vectors", pass);
        $finish;
    end
    initial begin #80000000; $fatal(1,"equiv timeout"); end
endmodule
