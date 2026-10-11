// RV32I/RV32M execution unit. No privileged extension. EEI traps are explicit.
module execute #(parameter M_EXT=0)(
 input [31:0] insn, pc, a, b,
 output reg [31:0] result, address, target,
 output reg write_rd, load_op, store_op, redirect, illegal, system_trap, m_op,
 output [4:0] rs1, rs2, rd,
 output [2:0] size
);
 wire [6:0] op=insn[6:0], f7=insn[31:25];
 wire [2:0] f3=insn[14:12];
 wire [31:0] ii={{20{insn[31]}},insn[31:20]};
 wire [31:0] si={{20{insn[31]}},insn[31:25],insn[11:7]};
 wire [31:0] bi={{19{insn[31]}},insn[31],insn[7],insn[30:25],insn[11:8],1'b0};
 wire [31:0] ji={{11{insn[31]}},insn[31],insn[19:12],insn[20],insn[30:21],1'b0};
 wire signed [63:0] sa={{32{a[31]}},a};
 wire signed [63:0] sb={{32{b[31]}},b};
 wire signed [63:0] ub={32'b0,b};
 wire signed [31:0] signed_quot=$signed(a)/$signed(b);
 wire signed [31:0] signed_rem=$signed(a)%$signed(b);
 wire signed [31:0] signed_shift=$signed(a)>>>rhs[4:0];
 reg [63:0] product;
 reg [31:0] rhs;
 assign rs1=insn[19:15]; assign rs2=insn[24:20]; assign rd=insn[11:7]; assign size=f3;
 always @* begin
  result=0; address=0; target=pc+4; write_rd=0; load_op=0; store_op=0;
  redirect=0; illegal=0; system_trap=0; m_op=0; rhs=b; product=0;
  case(op)
   7'h37: begin result={insn[31:12],12'b0}; write_rd=1; end
   7'h17: begin result=pc+{insn[31:12],12'b0}; write_rd=1; end
   7'h6f: begin result=pc+4; target=pc+ji; redirect=1; write_rd=1; end
   7'h67: begin result=pc+4; target=(a+ii)&32'hfffffffe; redirect=1; write_rd=1; illegal=(f3!=0); end
   7'h63: begin
    target=pc+bi;
    case(f3)
     0:redirect=(a==b); 1:redirect=(a!=b); 4:redirect=($signed(a)<$signed(b));
     5:redirect=($signed(a)>=$signed(b)); 6:redirect=(a<b); 7:redirect=(a>=b);
     default:illegal=1;
    endcase
   end
   7'h03: begin address=a+ii; load_op=1; write_rd=1; illegal=!(f3==0||f3==1||f3==2||f3==4||f3==5); end
   7'h23: begin address=a+si; store_op=1; illegal=!(f3==0||f3==1||f3==2); end
   7'h13,7'h33: begin
    write_rd=1; rhs=(op==7'h13)?ii:b;
    if(op==7'h33&&f7==1&&M_EXT) begin
     m_op=1; illegal=!M_EXT;
     case(f3)
      0:result=a*b;
      1:begin product=sa*sb; result=product[63:32]; end
      2:begin product=sa*ub; result=product[63:32]; end
      3:begin product={32'b0,a}*{32'b0,b}; result=product[63:32]; end
      4:result=(b==0)?32'hffffffff:((a==32'h80000000&&b==32'hffffffff)?a:signed_quot);
      5:result=(b==0)?32'hffffffff:a/b;
      6:result=(b==0)?a:((a==32'h80000000&&b==32'hffffffff)?0:signed_rem);
      7:result=(b==0)?a:a%b;
     endcase
    end else begin
     case(f3)
      0: begin result=(op==7'h33&&f7==7'h20)?a-rhs:a+rhs; if(op==7'h33&&f7!=0&&f7!=7'h20)illegal=1; end
      1: begin result=a<<rhs[4:0]; if(f7!=0)illegal=1; end
      2: begin result={31'b0,($signed(a)<$signed(rhs))}; if(op==7'h33&&f7!=0)illegal=1; end
      3: begin result={31'b0,(a<rhs)}; if(op==7'h33&&f7!=0)illegal=1; end
      4: begin result=a^rhs; if(op==7'h33&&f7!=0)illegal=1; end
      5: begin result=(f7==7'h20)?signed_shift:a>>rhs[4:0]; if(f7!=0&&f7!=7'h20)illegal=1; end
      6: begin result=a|rhs; if(op==7'h33&&f7!=0)illegal=1; end
      7: begin result=a&rhs; if(op==7'h33&&f7!=0)illegal=1; end
     endcase
    end
   end
   7'h0f: begin illegal=(f3!=0); end // FENCE ignores reserved rs1/rd fields; blocking ordered memory needs no extra action.
   7'h73: begin system_trap=(insn==32'h00000073||insn==32'h00100073); illegal=!system_trap; end
   default:illegal=1;
  endcase
 end
endmodule
