#include "Vlab_soc.h"
#include "verilated.h"
#include <cstdint>
#include <cstring>
#include <sstream>
#include <string>
#include <iostream>
#include <fstream>
#include <vector>
#include <memory>
#ifdef __EMSCRIPTEN__
#include <pthread.h>
#include <sched.h>
// Single-thread WebAssembly: OS affinity is unavailable and never requested.
extern "C" int pthread_getaffinity_np(pthread_t, size_t, cpu_set_t*){return -1;}
extern "C" int pthread_setaffinity_np(pthread_t, size_t, const cpu_set_t*){return -1;}
extern "C" int sched_getcpu(){return 0;}
#endif
double sc_time_stamp(){ return 0; }
static std::unique_ptr<Vlab_soc> cpu;
static uint8_t imem[65536],dmem[65536];
static std::string output,uart;
static uint32_t gpio=0,latency=1;
static bool cache_on=false;
struct Pending{bool valid=false;uint32_t addr=0;bool write=false;uint32_t remain=0;};
static Pending ip,dp;
static uint32_t read32(uint32_t addr,bool instruction){
 if(instruction){if(addr>65532)return 0;uint32_t v;memcpy(&v,imem+addr,4);return v;}
 if(addr>=0x10000000&&addr<=0x1000fffc){uint32_t v;memcpy(&v,dmem+(addr-0x10000000),4);return v;}
 if(addr==0x20000004)return gpio;
 return 0;
}
static bool fault(uint32_t addr,bool instruction){return instruction?(addr>65532||addr%4):!((addr>=0x10000000&&addr<0x10010000)||addr==0x20000000||addr==0x20000004);}
static void serve(Pending &p,bool req,uint32_t addr,bool write,bool instruction){
 if(!req){p.valid=false;return;}
 if(!p.valid||p.addr!=addr||p.write!=write){
  p={true,addr,write,latency-1};
 } else if(p.remain)p.remain--;
}
static void complete(Pending &p){p.valid=false;}
extern "C" {
void create(){cpu=std::make_unique<Vlab_soc>();memset(imem,0,sizeof(imem));memset(dmem,0,sizeof(dmem));}
void configure(int delay,int cached){latency=delay<1?1:delay>20?20:delay;cache_on=cached!=0; if(cpu)cpu->cache_enable=cache_on;}
void put_byte(uint32_t addr,uint32_t value){if(addr<65536)imem[addr]=value;else if(addr>=0x10000000&&addr<0x10010000)dmem[addr-0x10000000]=value;}
uint32_t get_byte(uint32_t addr){if(addr<65536)return imem[addr];if(addr>=0x10000000&&addr<0x10010000)return dmem[addr-0x10000000];return 0;}
void reset(){
 if(!cpu)create();cpu->reset=1;cpu->clk=0;cpu->eval();cpu->clk=1;cpu->eval();cpu->clk=0;cpu->reset=0;
 ip={};dp={};gpio=0;uart.clear();cpu->eval();
}
void step(){
 if(!cpu||cpu->halted)return;
 cpu->clk=0;cpu->i_ready=0;cpu->d_ready=0;cpu->eval();
 serve(ip,cpu->i_req,cpu->i_addr,false,true);serve(dp,cpu->d_req,cpu->d_addr,cpu->d_write,false);
 cpu->i_data=read32(cpu->i_addr,true);cpu->i_fault=fault(cpu->i_addr,true);cpu->i_ready=ip.valid&&ip.remain==0;
 cpu->d_rdata=read32(cpu->d_addr&~3u,false);cpu->d_fault=fault(cpu->d_addr,false);cpu->d_ready=dp.valid&&dp.remain==0;
 cpu->eval();
 bool ir=cpu->i_req&&cpu->i_ready,dr=cpu->d_req&&cpu->d_ready;
 if(dr&&cpu->d_write&&!cpu->d_fault){
  uint32_t addr=cpu->d_addr;
  if(addr==0x20000000)uart.push_back(char(cpu->d_wdata&255));
  else if(addr==0x20000004)gpio=cpu->d_wdata;
  else {unsigned bytes=1u<<(cpu->d_size&3);for(unsigned j=0;j<bytes;j++)dmem[addr-0x10000000+j]=(cpu->d_wdata>>(j*8))&255;}
 }
 cpu->clk=1;cpu->eval();cpu->clk=0;cpu->eval();
 if(ir)complete(ip);if(dr)complete(dp);
}
const char* snapshot(){
 std::ostringstream s;
 s<<"{\"cycle\":"<<cpu->cycle_count<<",\"instret\":"<<cpu->instret_count<<",\"pc\":"<<cpu->dbg_pc<<",\"insn\":"<<cpu->dbg_insn<<",\"state\":"<<unsigned(cpu->dbg_state)<<",\"halted\":"<<(cpu->halted?"true":"false")<<",\"trap\":"<<unsigned(cpu->trap_cause)<<",\"trapPc\":"<<cpu->trap_pc<<",\"trapAddr\":"<<cpu->trap_addr;
 s<<",\"a\":"<<cpu->dbg_a<<",\"b\":"<<cpu->dbg_b<<",\"result\":"<<cpu->dbg_result<<",\"stall\":"<<(cpu->dbg_stall?"true":"false")<<",\"flush\":"<<(cpu->dbg_flush?"true":"false")<<",\"regwrite\":"<<(cpu->dbg_regwrite?"true":"false")<<",\"stalls\":"<<cpu->stall_count<<",\"branches\":"<<cpu->branch_count;
 s<<",\"regs\":[";for(int i=0;i<32;i++){if(i)s<<',';s<<cpu->dbg_regs[i];}s<<']';
 s<<",\"stages\":[";for(int i=0;i<5;i++){if(i)s<<',';s<<"{\"valid\":"<<((cpu->dbg_valid>>i)&1)<<",\"pc\":"<<cpu->dbg_stage_pc[i]<<",\"insn\":"<<cpu->dbg_stage_insn[i]<<'}';}s<<']';
 s<<",\"retire\":{\"valid\":"<<unsigned(cpu->retire_valid)<<",\"pc\":"<<cpu->retire_pc<<",\"insn\":"<<cpu->retire_insn<<",\"rd\":"<<unsigned(cpu->retire_rd)<<",\"value\":"<<cpu->retire_value<<'}';
 s<<",\"rvfi\":{\"order\":"<<cpu->rvfi_order<<",\"trap\":"<<unsigned(cpu->rvfi_trap)<<",\"nextPc\":"<<cpu->rvfi_pc_wdata<<",\"rs1\":"<<unsigned(cpu->rvfi_rs1_addr)<<",\"rs2\":"<<unsigned(cpu->rvfi_rs2_addr)<<",\"a\":"<<cpu->rvfi_rs1_rdata<<",\"b\":"<<cpu->rvfi_rs2_rdata<<",\"memAddr\":"<<cpu->rvfi_mem_addr<<",\"rmask\":"<<unsigned(cpu->rvfi_mem_rmask)<<",\"wmask\":"<<unsigned(cpu->rvfi_mem_wmask)<<",\"rdata\":"<<cpu->rvfi_mem_rdata<<",\"wdata\":"<<cpu->rvfi_mem_wdata<<'}';
 s<<",\"bus\":{\"req\":"<<unsigned(cpu->dbg_mem_req)<<",\"write\":"<<unsigned(cpu->dbg_mem_write)<<",\"addr\":"<<cpu->dbg_mem_addr<<",\"data\":"<<cpu->dbg_mem_wdata<<",\"size\":"<<unsigned(cpu->dbg_mem_size)<<",\"ready\":"<<unsigned(cpu->dbg_mem_ready)<<'}';
 s<<",\"cache\":{\"enabled\":"<<(cache_on?"true":"false")<<",\"ihit\":"<<cpu->cache_ihit<<",\"imiss\":"<<cpu->cache_imiss<<",\"dhit\":"<<cpu->cache_dhit<<",\"dmiss\":"<<cpu->cache_dmiss<<"},\"gpio\":"<<gpio<<",\"uart\":[";
 for(unsigned i=0;i<uart.size();i++){if(i)s<<',';s<<unsigned(uint8_t(uart[i]));}s<<"]}";output=s.str();return output.c_str();
}
}
#ifndef __EMSCRIPTEN__
int main(int argc,char**argv){create();if(argc>1){std::ifstream f(argv[1],std::ios::binary);std::vector<char>b((std::istreambuf_iterator<char>(f)),{});if(argc>5&&std::string(argv[5])=="packed"){size_t offset=0;while(offset+8<=b.size()){uint32_t addr,len;memcpy(&addr,b.data()+offset,4);memcpy(&len,b.data()+offset+4,4);offset+=8;if(len>b.size()-offset){cpu.reset();return 3;}for(unsigned i=0;i<len;i++)put_byte(addr+i,uint8_t(b[offset+i]));offset+=len;}}else for(unsigned i=0;i<b.size();i++)put_byte(i,uint8_t(b[i]));}configure(argc>2?std::stoi(argv[2]):1,argc>3?std::stoi(argv[3]):0);reset();int limit=argc>4?std::stoi(argv[4]):100000;while(!cpu->halted&&limit--){step();std::cout<<snapshot()<<'\n';}int result=cpu->halted?0:2;cpu.reset();return result;}
#endif
