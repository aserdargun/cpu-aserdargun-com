"""Compile actual SKY130 mapped cell functions, with explicit instance probes."""
import pathlib,re,subprocess,math,json,sys,hashlib,concurrent.futures,shutil
root=pathlib.Path(__file__).resolve().parents[1]
library=root/'build/physical/sky130-functional.v'
liberty=root/'build/tools/orfs/flow/platforms/sky130hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
if not library.exists():subprocess.run(['yosys','-p',f'read_liberty -ignore_miss_func -ignore_miss_data_latch {liberty}; write_verilog -noattr {library}'],check=True)
libtext=library.read_text();outputs={}
for m in re.finditer(r'module (\S+)\([^;]*;(.*?)endmodule',libtext,re.S):outputs[m[1]]=re.findall(r'\boutput (\w+);',m[2])
for name in sys.argv[1:] or ['rv32i','rv32im']:
 source=root/'build/physical'/name/'mapped.v';text=source.read_text();out=root/'build/gates'/name;out.mkdir(parents=True,exist_ok=True)
 probes=[]
 for m in re.finditer(r'\n\s+(sky130_\w+)\s+(\S+)\s*\((.*?)\);',text,re.S):
  connections=dict(re.findall(r'\.(\w+)\(([^)]+)\)',m[3]))
  for pin in outputs[m[1]]:
   if pin in connections:probes.append({'instance':m[2],'master':m[1],'pin':pin,'net':connections[pin].strip(),'bit':len(probes)})
 words=math.ceil(len(probes)/32);width=words*32
 text=text.replace('module physical_core(', 'module physical_core(observe_regs, observe_gates, ',1)
 index=text.index(';',text.index('module physical_core'))+1
 assignments=f'\noutput [1023:0] observe_regs;\noutput [{width-1}:0] observe_gates;\nassign observe_regs[31:0]=0;\n'
 for i in range(1,32):assignments+=f'assign observe_regs[{i*32}+:32]=\\core.regs[{i}] ;\n'
 for p in probes:assignments+=f"assign observe_gates[{p['bit']}]={p['net']} ;\n"
 if width>len(probes):assignments+=f'assign observe_gates[{width-1}:{len(probes)}]=0;\n'
 text=text[:index]+assignments+text[index:];(out/'observed.v').write_text(text)
 manifest={'schemaVersion':1,'core':name,'kind':'mapped-functional-gates','timing':'zero delay; no SDF; use OpenROAD STA for timing','cache':False,'mappedSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'librarySha256':hashlib.sha256(liberty.read_bytes()).hexdigest(),'probes':probes,'probeCount':len(probes)}
 (out/'designmap.json').write_text(json.dumps(manifest,separators=(',',':')))
 subprocess.run(['python3',str(root/'scripts/designmap.py'),name,'--draft'],check=True)
 run=lambda args:subprocess.run(args,cwd=root,check=True)
 run(['verilator','--cc','--top-module','physical_core','--Mdir',str(out),'-Wno-fatal',str(library),str(out/'observed.v')])
 vr=subprocess.check_output(['verilator','--getenv','VERILATOR_ROOT'],text=True).strip()
 cpp=[str(p)for p in out.glob('Vphysical_core*.cpp')]+[vr+'/include/verilated.cpp',vr+'/include/verilated_threads.cpp','sim/gate_bridge.cpp']
 inc=['-I'+str(out),'-I'+vr+'/include','-I'+vr+'/include/vltstd',f'-DGATE_WORDS={words}']
 def objects(compiler,flags,suffix):
  def compile_one(pair):
   i,source=pair;obj=out/f'obj-{i}-{suffix}.o';run([compiler,'-std=c++17','-O1',*flags,*inc,'-c',source,'-o',str(obj)]);return str(obj)
  with concurrent.futures.ThreadPoolExecutor(max_workers=4)as pool:return list(pool.map(compile_one,enumerate(cpp)))
 native=objects('clang++',['-pthread'],'native')
 run(['clang++','-pthread',*native,'-o',str(out/'gates-native')])
 wasm=objects('em++',['-DVL_NO_THREADS'],'wasm')
 run(['em++','-O1',*wasm,'-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker,node','-sALLOW_MEMORY_GROWTH=1','-sFILESYSTEM=0','-sEXPORTED_FUNCTIONS=["_create","_configure","_put_byte","_get_byte","_reset","_step","_snapshot"]','-sEXPORTED_RUNTIME_METHODS=["UTF8ToString"]','-o',str(out/f'{name}-gates.js')])
 manifest=json.loads((out/'designmap.json').read_text())
 for extension in ['js','wasm']:
  file=out/f'{name}-gates.{extension}';manifest[extension+'Sha256']=hashlib.sha256(file.read_bytes()).hexdigest();shutil.copyfile(file,root/'public/sim'/file.name)
 manifest['bridgeSha256']=hashlib.sha256((root/'sim/gate_bridge.cpp').read_bytes()).hexdigest()
 target=root/'public/physical'/f'{name}-designmap.json';temporary=target.with_suffix('.tmp');temporary.write_text(json.dumps(manifest,separators=(',',':')));temporary.replace(target)
 print(name,len(probes),'actual mapped gate outputs compiled')
