#!/usr/bin/env python3
import pathlib, subprocess, os, json, hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
os.chdir(ROOT)
def run(args): subprocess.run(args,check=True)
for name,pipeline,m_ext in [('rv32i',0,0),('rv32im',1,1)]:
 out=ROOT/'build'/name; out.mkdir(parents=True,exist_ok=True)
 run(['verilator','--cc','--top-module','lab_soc','--Mdir',str(out),'-Wno-fatal','-GPIPELINE='+str(pipeline),'-GM_EXT='+str(m_ext),'rtl/execute.sv','rtl/cpu.sv','rtl/cache.sv','rtl/lab_soc.sv'])
 vr=subprocess.check_output(['verilator','--getenv','VERILATOR_ROOT'],text=True).strip()
 cpp=[str(p) for p in out.glob('Vlab_soc*.cpp')]+[vr+'/include/verilated.cpp',vr+'/include/verilated_threads.cpp','sim/bridge.cpp']
 inc=['-I'+str(out),'-I'+vr+'/include','-I'+vr+'/include/vltstd']
 run(['clang++','-std=c++17','-O2','-pthread',*inc,*cpp,'-o',str(out/'cpu-native')])
 run(['em++','-std=c++17','-O2','-DVL_NO_THREADS',*inc,*cpp,'-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node','-sALLOW_MEMORY_GROWTH=1','-sFILESYSTEM=0','-sEXPORTED_FUNCTIONS=["_create","_configure","_put_byte","_get_byte","_reset","_step","_snapshot"]','-sEXPORTED_RUNTIME_METHODS=["UTF8ToString"]','-o',str(ROOT/'public'/'sim'/f'{name}.js')])
manifest={'schemaVersion':1,'source':'SystemVerilog → Verilator → Emscripten','rtl':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'rtl').glob('*.sv')},'tools':{t:subprocess.check_output([t,'--version'],text=True).splitlines()[0] for t in ['verilator','emcc']},'models':{n:hashlib.sha256((ROOT/'public/sim'/f'{n}.wasm').read_bytes()).hexdigest() for n in ['rv32i','rv32im']}}
(ROOT/'public/sim/manifest.json').write_text(json.dumps(manifest,indent=2))
