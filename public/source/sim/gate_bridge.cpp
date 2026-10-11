// Functional mapped-cell simulation. No SDF delays: physical timing is in STA.
#include "Vphysical_core.h"
#include "verilated.h"
#include <memory>
#include <sstream>
#include <cstring>
#include <fstream>
#include <iostream>
#include <vector>
#ifdef __EMSCRIPTEN__
#include <pthread.h>
#include <sched.h>
extern "C" int pthread_getaffinity_np(pthread_t,size_t,cpu_set_t*){return -1;}
extern "C" int pthread_setaffinity_np(pthread_t,size_t,const cpu_set_t*){return -1;}
extern "C" int sched_getcpu(){return 0;}
#endif
double sc_time_stamp(){return 0;}
static std::unique_ptr<Vphysical_core> cpu;
static uint8_t code[65536],data[65536];
static uint32_t cycle=0,latency=1,gpio=0;
static std::string output,uart;
struct Pending{bool valid=false;uint32_t address=0,count=0;bool write=false;};
static Pending ip,dp;
static void serve(Pending&p,bool req,uint32_t address,bool write){if(!req){p.valid=false;return;}if(!p.valid||p.address!=address||p.write!=write)p={true,address,latency-1,write};else if(p.count)p.count--;}
static uint32_t readword(uint32_t address,bool instruction){uint32_t value=0;if(instruction&&address<=65532)memcpy(&value,code+address,4);else if(!instruction&&address>=0x10000000&&address<=0x1000fffc)memcpy(&value,data+address-0x10000000,4);else if(address==0x20000004)value=gpio;return value;}
extern "C" {
void create(){cpu=std::make_unique<Vphysical_core>();memset(code,0,sizeof(code));memset(data,0,sizeof(data));}
void configure(int delay,int){latency=delay<1?1:delay>20?20:delay;}
void put_byte(uint32_t address,uint32_t value){if(address<65536)code[address]=value;else if(address>=0x10000000&&address<0x10010000)data[address-0x10000000]=value;}
uint32_t get_byte(uint32_t address){if(address<65536)return code[address];if(address>=0x10000000&&address<0x10010000)return data[address-0x10000000];return 0;}
void reset(){cpu->reset=1;cpu->clk=0;cpu->eval();cpu->clk=1;cpu->eval();cpu->clk=0;cpu->reset=0;cpu->eval();cycle=gpio=0;ip={};dp={};uart.clear();}
void step(){if(cpu->halted)return;cpu->clk=0;cpu->i_ready=cpu->d_ready=0;cpu->eval();serve(ip,cpu->i_req,cpu->i_addr,false);serve(dp,cpu->d_req,cpu->d_addr,cpu->d_write);cpu->i_ready=ip.valid&&ip.count==0;cpu->d_ready=dp.valid&&dp.count==0;cpu->i_data=readword(cpu->i_addr,true);cpu->d_rdata=readword(cpu->d_addr&~3u,false);cpu->i_fault=cpu->i_addr>65532||cpu->i_addr%4;cpu->d_fault=!((cpu->d_addr>=0x10000000&&cpu->d_addr<0x10010000)||cpu->d_addr==0x20000000||cpu->d_addr==0x20000004);cpu->eval();bool ir=cpu->i_req&&cpu->i_ready,dr=cpu->d_req&&cpu->d_ready;if(dr&&cpu->d_write&&!cpu->d_fault){uint32_t a=cpu->d_addr;if(a==0x20000000)uart+=char(cpu->d_wdata&255);else if(a==0x20000004)gpio=cpu->d_wdata;else for(unsigned i=0;i<(1u<<(cpu->d_size&3));i++)data[a-0x10000000+i]=cpu->d_wdata>>(8*i);}cpu->clk=1;cpu->eval();cpu->clk=0;cpu->eval();cycle++;if(ir)ip.valid=false;if(dr)dp.valid=false;}
const char*snapshot(){std::ostringstream s;s<<"{\"cycle\":"<<cycle<<",\"halted\":"<<(cpu->halted?"true":"false")<<",\"trap\":"<<unsigned(cpu->trap_cause)<<",\"gpio\":"<<gpio<<",\"regs\":[";for(int i=0;i<32;i++){if(i)s<<',';s<<cpu->observe_regs[i];}s<<"],\"ports\":{\"clk\":0,\"reset\":0,\"i_data\":"<<cpu->i_data<<",\"i_ready\":"<<unsigned(cpu->i_ready)<<",\"i_fault\":"<<unsigned(cpu->i_fault)<<",\"d_rdata\":"<<cpu->d_rdata<<",\"d_ready\":"<<unsigned(cpu->d_ready)<<",\"d_fault\":"<<unsigned(cpu->d_fault)<<"},\"signals\":[";for(unsigned i=0;i<GATE_WORDS;i++){if(i)s<<',';s<<cpu->observe_gates[i];}s<<"]}";output=s.str();return output.c_str();}
}
#ifndef __EMSCRIPTEN__
int main(int argc,char**argv){create();configure(argc>2?std::stoi(argv[2]):1,0);if(argc>1){std::ifstream f(argv[1],std::ios::binary);uint32_t a,n;while(f.read((char*)&a,4)&&f.read((char*)&n,4)){std::vector<char>b(n);f.read(b.data(),n);for(unsigned i=0;i<n;i++)put_byte(a+i,uint8_t(b[i]));}}reset();int limit=100000;while(!cpu->halted&&limit--){step();std::cout<<snapshot()<<'\n';}int result=cpu->halted?0:2;cpu.reset();return result;}
#endif
