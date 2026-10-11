module rvfi_wrapper(input clock,reset, `RVFI_OUTPUTS);
 (* keep *) `rvformal_rand_reg [31:0] i_data,d_rdata;
 (* keep *) `rvformal_rand_reg i_ready,d_ready;
 wire i_req,d_req,d_write,halted;
 wire [31:0] i_addr,d_addr,d_wdata;
 wire [2:0] d_size;
 cpu #(.PIPELINE(`CPU_PIPELINE),.M_EXT(0)) dut(
 .clk(clock),.reset(reset),.i_req(i_req),.i_addr(i_addr),.i_ready(i_ready),.i_data(i_data),.i_fault(1'b0),
 .d_req(d_req),.d_write(d_write),.d_addr(d_addr),.d_wdata(d_wdata),.d_size(d_size),.d_ready(d_ready),.d_rdata(d_rdata),.d_fault(1'b0),.halted(halted),
 `RVFI_CONN);
endmodule
