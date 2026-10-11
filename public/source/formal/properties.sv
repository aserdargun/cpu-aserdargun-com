module properties(input clk);
 reg reset=1;
 always @(posedge clk)reset<=0;
 (* anyseq *) reg i_ready,d_ready,i_fault,d_fault;
 (* anyseq *) reg [31:0] i_data,d_rdata;
 wire halted,d_req,d_write,i_req;
 wire [31:0] d_addr,d_wdata,i_addr;
 wire [2:0] d_size;
 wire [1023:0] regs;
 wire [3:0] trap;
 wire regwrite;
 cpu #(.PIPELINE(1),.M_EXT(0)) dut(.clk(clk),.reset(reset),.i_req(i_req),.i_addr(i_addr),.i_ready(i_ready),.i_data(i_data),.i_fault(i_fault),.d_req(d_req),.d_write(d_write),.d_addr(d_addr),.d_wdata(d_wdata),.d_size(d_size),.d_ready(d_ready),.d_rdata(d_rdata),.d_fault(d_fault),.halted(halted),.trap_cause(trap),.dbg_regs(regs),.dbg_regwrite(regwrite));
 reg past_valid=0;
 always @(posedge clk)begin
  past_valid<=1;
  if(past_valid&&!reset)begin
   assert(regs[31:0]==0);
   if(halted)assert(!d_req&&!i_req);
   if($past(halted)&&!$past(reset))assert(halted&&$stable(regs));
   if($past(d_req&&!d_ready)&&!$past(reset)&&!halted)assert(d_req&&$stable(d_addr)&&$stable(d_wdata)&&$stable(d_size)&&$stable(d_write));
   if(halted)assert(!regwrite);
  end
 end
endmodule
