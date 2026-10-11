module lab_soc #(parameter PIPELINE=0, parameter M_EXT=0)(
 input clk, reset, cache_enable,
 output dbg_mem_req,dbg_mem_write,dbg_mem_ready,output [31:0] dbg_mem_addr,dbg_mem_wdata,output [2:0] dbg_mem_size,
 output [31:0] cache_ihit,cache_imiss,cache_dhit,cache_dmiss,
 output i_req, output [31:0] i_addr, input i_ready, input [31:0] i_data, input i_fault,
 output d_req, d_write, output [31:0] d_addr,d_wdata, output [2:0] d_size,
 input d_ready, input [31:0] d_rdata, input d_fault,
 output reg halted, output reg [3:0] trap_cause,
 output reg [31:0] trap_pc, trap_addr,
 output reg retire_valid, output reg [31:0] retire_pc,retire_insn,retire_value,
 output reg [4:0] retire_rd,
 output rvfi_valid, output reg [63:0] rvfi_order,
 output [31:0] rvfi_insn, output reg rvfi_trap, output rvfi_halt,rvfi_intr,
 output [1:0] rvfi_mode,rvfi_ixl,
 output reg [4:0] rvfi_rs1_addr,rvfi_rs2_addr,
 output reg [31:0] rvfi_rs1_rdata,rvfi_rs2_rdata,
 output [4:0] rvfi_rd_addr, output [31:0] rvfi_rd_wdata,
 output [31:0] rvfi_pc_rdata, output reg [31:0] rvfi_pc_wdata,
 output reg [31:0] rvfi_mem_addr,rvfi_mem_rdata,rvfi_mem_wdata,
 output reg [3:0] rvfi_mem_rmask,rvfi_mem_wmask,
 output [1023:0] dbg_regs,
 output [31:0] dbg_pc,dbg_insn,dbg_a,dbg_b,dbg_result,
 output [159:0] dbg_stage_pc,dbg_stage_insn, output [4:0] dbg_valid,
 output [2:0] dbg_state, output dbg_stall,dbg_flush,dbg_regwrite,
 output reg [31:0] cycle_count,instret_count,stall_count,branch_count
);
 wire ci_req,ci_ready,ci_fault,cd_req,cd_write,cd_ready,cd_fault;
 wire [31:0] ci_addr,ci_data,cd_addr,cd_wdata,cd_rdata;
 wire [2:0] cd_size;
 assign dbg_mem_req=cd_req;assign dbg_mem_write=cd_write;assign dbg_mem_ready=cd_ready;assign dbg_mem_addr=cd_addr;assign dbg_mem_wdata=cd_wdata;assign dbg_mem_size=cd_size;
 cpu #(.PIPELINE(PIPELINE),.M_EXT(M_EXT)) core(
 .i_req(ci_req),.i_addr(ci_addr),.i_ready(ci_ready),.i_data(ci_data),.i_fault(ci_fault),
 .d_req(cd_req),.d_write(cd_write),.d_addr(cd_addr),.d_wdata(cd_wdata),.d_size(cd_size),.d_ready(cd_ready),.d_rdata(cd_rdata),.d_fault(cd_fault),.*);
 wire unused_i_write;wire [31:0] unused_i_wdata;wire [2:0] unused_i_size;
 cache #(.INSTRUCTION(1)) icache(.clk(clk),.reset(reset),.enable(cache_enable&&PIPELINE),.req(ci_req),.write_op(1'b0),.addr(ci_addr),.wdata(32'b0),.size(3'd2),.ready(ci_ready),.rdata(ci_data),.fault(ci_fault),.mem_req(i_req),.mem_write(unused_i_write),.mem_addr(i_addr),.mem_wdata(unused_i_wdata),.mem_size(unused_i_size),.mem_ready(i_ready),.mem_rdata(i_data),.mem_fault(i_fault),.hits(cache_ihit),.misses(cache_imiss));
 cache #(.INSTRUCTION(0)) dcache(.clk(clk),.reset(reset),.enable(cache_enable&&PIPELINE),.req(cd_req),.write_op(cd_write),.addr(cd_addr),.wdata(cd_wdata),.size(cd_size),.ready(cd_ready),.rdata(cd_rdata),.fault(cd_fault),.mem_req(d_req),.mem_write(d_write),.mem_addr(d_addr),.mem_wdata(d_wdata),.mem_size(d_size),.mem_ready(d_ready),.mem_rdata(d_rdata),.mem_fault(d_fault),.hits(cache_dhit),.misses(cache_dmiss));
endmodule
