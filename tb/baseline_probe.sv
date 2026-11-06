`timescale 1ns/1ps
module baseline_probe;
    reg SCK=0, RST_N=1, MOSI=0, NORM_CS_N=1, START=0, ENC_DEC=0;
    wire MISO, BUSY, ICE_LED;
    reg [31:0] received, ignored;
    integer mode, cycle;
    accelerator_baseline dut(.*);

    task pulse;
        begin #500; SCK=1; #500; SCK=0; end
    endtask

    task reset_core;
        begin
            SCK=0; NORM_CS_N=1; START=0; MOSI=0; RST_N=0;
            repeat(2) pulse();
            RST_N=1; pulse();
        end
    endtask

    task spi_word(input [31:0] tx, output [31:0] rx);
        integer bit_index;
        begin
            NORM_CS_N=0;
            for(bit_index=31; bit_index>=0; bit_index=bit_index-1) begin
                MOSI=tx[bit_index];
                #500; SCK=1; #1; rx[bit_index]=MISO;
                #499; SCK=0;
            end
            NORM_CS_N=1;
        end
    endtask

    initial begin
        $dumpfile("build/sim/baseline_probe.vcd");
        $dumpvars(0, baseline_probe);
        reset_core();
        spi_word(32'h59C359C3, ignored);
        spi_word(32'h59C359C3, received);
        $display("SPI_READBACK tx=59c359c3 rx=%08h", received);
        if(received !== 32'h59C359C3) $fatal(1,"SPI readback failed");
        for(mode=0; mode<2; mode=mode+1) begin
            reset_core(); ENC_DEC=mode;
            spi_word(32'h59C359C3, ignored);
            START=1; #1;
            $display("TIMING mode=%0d before_start_edge busy=%b", mode, BUSY);
            pulse(); START=0; #1;
            $display("TIMING mode=%0d edge=1 busy=%b", mode, BUSY);
            for(cycle=2; cycle<=8; cycle=cycle+1) begin
                pulse();
                $display("TIMING mode=%0d edge=%0d busy=%b", mode, cycle, BUSY);
            end
            spi_word(32'b0, received);
            $display("MODE_PROBE mode=%0d input=59c359c3 output=%08h", mode, received);
            reset_core(); ENC_DEC=mode;
            spi_word(32'h9CD84392, ignored);
            START=1; pulse(); START=0;
            repeat(7) pulse();
            spi_word(32'b0, received);
            $display("MODE_PROBE mode=%0d input=9cd84392 output=%08h", mode, received);
        end
        $display("PROBE_COMPLETE"); $finish;
    end
    initial begin #1000000; $fatal(1,"Probe timeout"); end
endmodule
