`timescale 1ns/1ps

// AI-generated environment check, separate from the challenge accelerator.
module environment_smoke;
    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg [3:0] count = 4'd0;

    // A 1 MHz clock, with a synchronous active-low reset.
    always #500 clk = ~clk;

    always @(posedge clk) begin
        if (!rst_n)
            count <= 4'd0;
        else
            count <= count + 1'b1;
    end

    initial begin
        $dumpfile("build/sim/environment_smoke.vcd");
        $dumpvars(0, environment_smoke);

        repeat (2) @(negedge clk);
        if (count !== 4'd0)
            $fatal(1, "Environment check failed: synchronous reset");

        rst_n = 1'b1;
        repeat (5) @(negedge clk);
        if (count !== 4'd5)
            $fatal(1, "Environment check failed: expected count 5, got %0d", count);

        $display("ENVIRONMENT_SMOKE_PASS: reset, clock, simulation, and VCD generation work");
        $finish;
    end

    initial begin
        #20000;
        $fatal(1, "Environment check timed out");
    end
endmodule
