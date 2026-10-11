// Independent ISA oracle: upstream Spike processor, matched bare-metal EEI.
#include "processor.h"
#include "simif.h"
#include "cfg.h"
#include <array>
#include <fstream>
#include <iostream>
#include <cstring>
struct Environment:simif_t {
 cfg_t cfg;std::map<size_t,processor_t*> harts;
 std::array<char,65536> code{},data{};uint32_t gpio=0;std::string uart;
 Environment(){cfg.pmpregions=0;cfg.hartids={0};cfg.mem_layout={mem_cfg_t(0,65536),mem_cfg_t(0x10000000,65536)};}
 char* addr_to_mem(reg_t a)override {if(a<65536)return code.data()+a;if(a>=0x10000000&&a<0x10010000)return data.data()+a-0x10000000;return nullptr;}
 bool mmio_load(reg_t a,size_t n,uint8_t*b)override {if(a==0x20000004&&n<=4){memcpy(b,&gpio,n);return true;}if(a==0x20000000&&n<=4){memset(b,0,n);return true;}return false;}
 bool mmio_store(reg_t a,size_t n,const uint8_t*b)override {if(a==0x20000000){uart+=char(b[0]);return true;}if(a==0x20000004&&n<=4){memcpy(&gpio,b,n);return true;}return false;}
 void proc_reset(unsigned)override{}
 const cfg_t&get_cfg()const override{return cfg;}
 const std::map<size_t,processor_t*>&get_harts()const override{return harts;}
 const char*get_symbol(uint64_t)override{return nullptr;}
};
int main(int argc,char**argv){if(argc<2)return 1;Environment env;std::ifstream f(argv[1],std::ios::binary);uint32_t address,length;while(f.read((char*)&address,4)&&f.read((char*)&length,4)){char*p=env.addr_to_mem(address);if(!p||length>65536)return 2;f.read(p,length);}
 FILE*quiet=tmpfile();processor_t p(argc>2?argv[2]:"RV32IM","M",&env.cfg,&env,0,false,quiet,std::cerr);env.harts[0]=&p;p.get_state()->pc=0;
 for(unsigned step=0;step<100000;step++){auto*s=p.get_state();uint32_t pc=s->pc,insn=0;char*ptr=env.addr_to_mem(pc);if(ptr)memcpy(&insn,ptr,4);std::array<uint32_t,32> before;for(int i=0;i<32;i++)before[i]=s->XPR[i];reg_t old=s->minstret->read();p.step(1);bool trap=s->minstret->read()==old;std::cout<<"{\"pc\":"<<pc<<",\"insn\":"<<insn<<",\"trap\":"<<(trap?s->mcause->read():0)<<",\"nextPc\":"<<uint32_t(s->pc)<<",\"before\":[";for(int i=0;i<32;i++){if(i)std::cout<<',';std::cout<<before[i];}std::cout<<"],\"regs\":[";for(int i=0;i<32;i++){if(i)std::cout<<',';std::cout<<uint32_t(s->XPR[i]);}std::cout<<"],\"memory\":[";for(int i=0;i<128;i++){if(i)std::cout<<',';std::cout<<unsigned(uint8_t(env.data[i]));}std::cout<<"],\"gpio\":"<<env.gpio<<",\"uart\":[";for(size_t i=0;i<env.uart.size();i++){if(i)std::cout<<',';std::cout<<unsigned(uint8_t(env.uart[i]));}std::cout<<"]}\n";if(trap){fclose(quiet);return 0;}}
 return 3;}
