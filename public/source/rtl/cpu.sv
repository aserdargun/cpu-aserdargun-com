module cpu #(parameter PIPELINE=0, parameter M_EXT=0)(
 input clk, reset,
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
 reg [31:0] regs[0:31];
 genvar g; generate for(g=0;g<32;g=g+1)begin:R assign dbg_regs[g*32+:32]=regs[g]; end endgenerate
 reg [31:0] fetch_pc;
 // Each stage retains actual instruction and address; trap is carried to retirement.
 reg dv,xv,mv,wv,df,xf;
 reg [31:0] dp,di,xp,xi,mp,mi,wp,wi;
 reg [31:0] mr,ma,mb,wr;
 reg [4:0] md,wd;
 reg ml,ms,mwe,wwe;
 reg [2:0] mz;
 reg [3:0] mt,wt;
 reg [31:0] mta,wta;
 reg [31:0] mnext,wnext,mrs1,mrs2,wrs1,wrs2,wmaddr,wmread,wmwrite;
 reg [4:0] mrs1id,mrs2id,wrs1id,wrs2id;
 reg [3:0] wmrmask,wmwmask;
 reg [63:0] retire_order;
 wire reads_rs1=(xi[6:0]==7'h67||xi[6:0]==7'h63||xi[6:0]==7'h03||xi[6:0]==7'h23||xi[6:0]==7'h13||xi[6:0]==7'h33);
 wire reads_rs2=(xi[6:0]==7'h63||xi[6:0]==7'h23||xi[6:0]==7'h33);
 wire [3:0] access_mask=mz[1:0]==0?4'b0001:mz[1:0]==1?4'b0011:4'b1111;
 assign rvfi_valid=retire_valid;assign rvfi_insn=retire_insn;
 assign rvfi_halt=retire_valid&&rvfi_trap;assign rvfi_intr=0;
 assign rvfi_mode=3;assign rvfi_ixl=1;
 assign rvfi_rd_addr=rvfi_trap?0:retire_rd;
 assign rvfi_rd_wdata=(rvfi_rd_addr==0)?0:retire_value;
 assign rvfi_pc_rdata=retire_pc;
 reg [2:0] state;
 reg [5:0] m_wait;
 wire [4:0] r1,r2,rd;
 wire [2:0] sz;
 wire [31:0] result,address,target;
 wire we,lo,so,redir,bad,sys,mop;
 reg [31:0] mvalue;
 wire [31:0] shifted_data=d_rdata >> (ma[1:0]*8);
 always @* begin
  case(mz)
   0:mvalue={{24{shifted_data[7]}},shifted_data[7:0]};
   1:mvalue={{16{shifted_data[15]}},shifted_data[15:0]};
   4:mvalue={24'b0,shifted_data[7:0]};
   5:mvalue={16'b0,shifted_data[15:0]};
   default:mvalue=d_rdata;
  endcase
 end
 wire mem_done=mv&&(!(ml||ms)||d_ready||mt!=0);
 wire [31:0] a=(r1==0)?0:(mv&&mwe&&md==r1&&mt==0&&(!ml||mem_done))?(ml?mvalue:mr):(wv&&wwe&&wd==r1&&wt==0)?wr:regs[r1];
 wire [31:0] b=(r2==0)?0:(mv&&mwe&&md==r2&&mt==0&&(!ml||mem_done))?(ml?mvalue:mr):(wv&&wwe&&wd==r2&&wt==0)?wr:regs[r2];
 execute #(.M_EXT(M_EXT)) ex(.insn(xi),.pc(xp),.a(a),.b(b),.result(result),.address(address),.target(target),.write_rd(we),.load_op(lo),.store_op(so),.redirect(redir),.illegal(bad),.system_trap(sys),.m_op(mop),.rs1(r1),.rs2(r2),.rd(rd),.size(sz));
 wire misalign=(lo||so)&&((sz[1:0]==1&&address[0])||(sz[1:0]==2&&address[1:0]!=0));
 wire jump_bad=redir&&target[1:0]!=0;
 wire [3:0] xt=xf?4'd1:bad?4'd2:sys?(xi[20]?4'd3:4'd11):jump_bad?4'd1:misalign?(so?4'd6:4'd4):4'd0;
 wire memory_error=mem_done&&d_req&&d_fault;
 wire xready=xv&&(!mv||mem_done)&&(!mop||m_wait==0)&&!memory_error;
 wire flush=xready&&redir&&xt==0;
 wire trap_drain=(mv&&mt!=0)||(wv&&wt!=0);
 assign i_req=!halted&&!trap_drain&&!memory_error&&(PIPELINE?(!dv||(!xv||xready)):state==0);
 assign i_addr=fetch_pc;
 assign d_req=mv&&(ml||ms)&&mt==0&&!halted;
 assign d_write=ms; assign d_addr=ma; assign d_wdata=mb; assign d_size=mz;
 assign dbg_pc=fetch_pc; assign dbg_insn=xi; assign dbg_a=a; assign dbg_b=b; assign dbg_result=result;
 assign dbg_stage_pc={wp,mp,xp,dp,fetch_pc}; assign dbg_stage_insn={wi,mi,xi,di,i_data};
 assign dbg_valid={wv,mv,xv,dv,i_req}; assign dbg_state=state;
 assign dbg_stall=!halted&&((mv&&(ml||ms)&&!d_ready)||(xv&&mop&&m_wait!=0)||(i_req&&!i_ready));
 assign dbg_flush=flush; assign dbg_regwrite=wv&&wwe&&wd!=0&&wt==0;
 integer n;
 always @(posedge clk)begin
  if(reset)begin
   for(n=0;n<32;n=n+1)regs[n]<=0;
   fetch_pc<=0; df<=0;xf<=0;dv<=0;xv<=0;mv<=0;wv<=0;dp<=0;di<=0;xp<=0;xi<=0;mp<=0;mi<=0;wp<=0;wi<=0;
   mr<=0;ma<=0;mb<=0;wr<=0;md<=0;wd<=0;ml<=0;ms<=0;mwe<=0;wwe<=0;mz<=0;mt<=0;wt<=0;mta<=0;wta<=0;
   state<=0;m_wait<=0;halted<=0;trap_cause<=0;trap_pc<=0;trap_addr<=0;
   retire_valid<=0;retire_pc<=0;retire_insn<=0;retire_rd<=0;retire_value<=0;
   retire_order<=0;rvfi_order<=0;rvfi_trap<=0;rvfi_rs1_addr<=0;rvfi_rs2_addr<=0;
   rvfi_rs1_rdata<=0;rvfi_rs2_rdata<=0;rvfi_pc_wdata<=0;rvfi_mem_addr<=0;rvfi_mem_rdata<=0;rvfi_mem_wdata<=0;rvfi_mem_rmask<=0;rvfi_mem_wmask<=0;
   mnext<=0;wnext<=0;mrs1<=0;mrs2<=0;wrs1<=0;wrs2<=0;mrs1id<=0;mrs2id<=0;wrs1id<=0;wrs2id<=0;wmaddr<=0;wmread<=0;wmwrite<=0;wmrmask<=0;wmwmask<=0;
   cycle_count<=0;instret_count<=0;stall_count<=0;branch_count<=0;
  end else if(!halted)begin
   cycle_count<=cycle_count+1; retire_valid<=0; regs[0]<=0;
   if(dbg_stall)stall_count<=stall_count+1;
   if(wv)begin
    retire_valid<=1;retire_pc<=wp;retire_insn<=wi;retire_rd<=wwe?wd:0;retire_value<=wr;
    rvfi_order<=retire_order;retire_order<=retire_order+1;rvfi_trap<=wt!=0;
    rvfi_rs1_addr<=wrs1id;rvfi_rs2_addr<=wrs2id;rvfi_rs1_rdata<=wrs1;rvfi_rs2_rdata<=wrs2;
    rvfi_pc_wdata<=wnext;rvfi_mem_addr<=wmaddr;rvfi_mem_rdata<=wmread;rvfi_mem_wdata<=wmwrite;
    rvfi_mem_rmask<=wt==0?wmrmask:0;rvfi_mem_wmask<=wt==0?wmwmask:0;
    if(wt!=0)begin halted<=1;trap_cause<=wt;trap_pc<=wp;trap_addr<=wta;dv<=0;xv<=0;mv<=0; end
    else begin
     instret_count<=instret_count+1;
     if(wwe&&wd!=0)regs[wd]<=wr;
    end
    wv<=0;
    if(!PIPELINE)state<=0;
   end
   if(mem_done&&!trap_drain)begin
    wv<=1;wp<=mp;wi<=mi;wd<=memory_error?0:md;wr<=memory_error?0:(ml?mvalue:mr);wwe<=memory_error?0:mwe;
    wnext<=mnext;wrs1<=mrs1;wrs2<=mrs2;wrs1id<=mrs1id;wrs2id<=mrs2id;
    wmaddr<=(ml||ms)?{ma[31:2],2'b00}:0;wmread<=ml?d_rdata:0;wmwrite<=ms?(mb<<(ma[1:0]*8)):0;wmrmask<=ml?(access_mask<<ma[1:0]):0;wmwmask<=ms?(access_mask<<ma[1:0]):0;
    if(memory_error)begin dv<=0;xv<=0; end
    wt<=d_req&&d_fault?(ms?4'd7:4'd5):mt;wta<=ma;mv<=0;
    if(!PIPELINE)state<=4;
   end
   // Traps in MEM also move to WB, while younger work is discarded.
   if(mv&&mt!=0)begin
    wv<=1;wp<=mp;wi<=mi;wd<=0;wr<=0;wwe<=0;wt<=mt;wta<=mta;mv<=0;dv<=0;xv<=0;
    wnext<=mnext;wrs1<=mrs1;wrs2<=mrs2;wrs1id<=mrs1id;wrs2id<=mrs2id;wmrmask<=0;wmwmask<=0;
    if(!PIPELINE)state<=4;
   end
   if(xv&&mop&&m_wait!=0)m_wait<=m_wait-1;
   if(xready&&!trap_drain)begin
    mv<=1;mp<=xp;mi<=xi;md<=rd;mr<=result;ma<=address;mb<=b;ml<=lo;ms<=so;mz<=sz;mwe<=we;
    mnext<=redir?target:xp+4;mrs1id<=reads_rs1?r1:0;mrs2id<=reads_rs2?r2:0;mrs1<=reads_rs1?a:0;mrs2<=reads_rs2?b:0;
    mt<=xt;mta<=xf?xp:jump_bad?target:address;xv<=0;
    if(redir&&xt==0)begin fetch_pc<=target;dv<=0;branch_count<=branch_count+1; end
    if(xt!=0)dv<=0;
    if(!PIPELINE)state<=3;
   end
   if(PIPELINE)begin
    if(dv&&(!xv||xready)&&!flush&&!trap_drain&&!memory_error&&!(xready&&xt!=0))begin
     xv<=1;xp<=dp;xi<=di;xf<=df;dv<=0;
     m_wait<=(M_EXT&&di[6:0]==7'h33&&di[31:25]==1)?(di[14]?6'd31:6'd3):0;
    end
    if(i_req&&i_ready&&!flush&&!trap_drain&&!memory_error&&!(xready&&xt!=0))begin
     dv<=1;dp<=fetch_pc;di<=i_data;df<=i_fault;fetch_pc<=fetch_pc+4;
    end
   end else begin
    if(state==0&&i_req&&i_ready)begin
     dv<=1;dp<=fetch_pc;di<=i_data;df<=i_fault;fetch_pc<=fetch_pc+4;state<=1;
    end
    if(state==1)begin xv<=1;xp<=dp;xi<=di;xf<=df;dv<=0;state<=2;m_wait<=0; end
   end
  end else retire_valid<=0;
 end
endmodule
