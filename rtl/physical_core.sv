// Cacheless implementation boundary. Observation ports are omitted so that
// instrumentation does not inflate the physical design or external pin count.
module physical_core #(parameter PIPELINE=0, M_EXT=0)(
 input clk, reset,
 output i_req, output [31:0] i_addr, input i_ready, input [31:0] i_data, input i_fault,
 output d_req,d_write,output [31:0] d_addr,d_wdata,output [2:0] d_size,
 input d_ready,input [31:0] d_rdata,input d_fault,
 output halted,output [3:0] trap_cause
);
 cpu #(.PIPELINE(PIPELINE),.M_EXT(M_EXT)) core(
 .clk(clk),.reset(reset),.i_req(i_req),.i_addr(i_addr),.i_ready(i_ready),.i_data(i_data),.i_fault(i_fault),
 .d_req(d_req),.d_write(d_write),.d_addr(d_addr),.d_wdata(d_wdata),.d_size(d_size),.d_ready(d_ready),.d_rdata(d_rdata),.d_fault(d_fault),
 .halted(halted),.trap_cause(trap_cause));
endmodule
