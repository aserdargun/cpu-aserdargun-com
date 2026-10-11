// Direct-mapped 1KiB cache, 16-byte lines. Write-through, no write allocation.
module cache #(parameter INSTRUCTION=0)(
 input clk,reset,enable,
 input req,write_op, input [31:0] addr,wdata, input [2:0] size,
 output reg ready, output reg [31:0] rdata, output reg fault,
 output reg mem_req,mem_write, output reg [31:0] mem_addr,mem_wdata,output reg [2:0] mem_size,
 input mem_ready, input [31:0] mem_rdata, input mem_fault,
 output reg [31:0] hits,misses
);
 reg valid[0:63]; reg [21:0] tags[0:63]; reg [31:0] words[0:255];
 reg filling; reg [31:0] line_addr; reg [1:0] refill_word;
 reg response_fault,miss_response;
 wire cacheable=INSTRUCTION?(addr<32'h00010000):(addr>=32'h10000000&&addr<32'h10010000);
 wire active=enable&&cacheable;
 wire hit=valid[addr[9:4]]&&tags[addr[9:4]]==addr[31:10];
 reg [31:0] mask,merged;
 integer n;
 always @* begin
  ready=0;rdata=0;fault=0;mem_req=0;mem_write=0;mem_addr=addr;mem_wdata=wdata;mem_size=size;
  mask=(size[1:0]==0)?(32'hff<<(addr[1:0]*8)):(size[1:0]==1)?(32'hffff<<(addr[1:0]*8)):32'hffffffff;
  merged=(words[addr[9:2]]&~mask)|((wdata<<(addr[1:0]*8))&mask);
  if(filling)begin mem_req=1;mem_addr=line_addr+{28'b0,refill_word,2'b0};mem_size=2;end
  else if(response_fault)begin ready=req;fault=1;end
  else if(req)begin
   if(!active||write_op)begin mem_req=1;mem_write=write_op;ready=mem_ready;rdata=mem_rdata;fault=mem_fault;end
   else if(hit)begin ready=1;rdata=words[addr[9:2]];end
  end
 end
 always @(posedge clk)begin
  if(reset)begin filling<=0;line_addr<=0;refill_word<=0;response_fault<=0;miss_response<=0;hits<=0;misses<=0;for(n=0;n<64;n=n+1)valid[n]<=0;end
  else begin
   if(response_fault&&req)response_fault<=0;
   if(filling&&mem_ready)begin
    if(mem_fault)begin filling<=0;response_fault<=1;valid[line_addr[9:4]]<=0;end
    else begin
     words[{line_addr[9:4],refill_word}]<=mem_rdata;
     if(refill_word==3)begin filling<=0;miss_response<=1;tags[line_addr[9:4]]<=line_addr[31:10];valid[line_addr[9:4]]<=1;end
     else refill_word<=refill_word+1;
    end
   end else if(!filling&&req&&active&&!response_fault)begin
    if(write_op&&mem_ready)begin if(hit)begin hits<=hits+1;if(!mem_fault)words[addr[9:2]]<=merged;end else misses<=misses+1;end
    else if(!write_op)begin
     if(hit)begin if(!miss_response)hits<=hits+1;miss_response<=0;end
     else begin filling<=1;line_addr<={addr[31:4],4'b0};refill_word<=0;misses<=misses+1;end
    end
   end
  end
 end
endmodule
