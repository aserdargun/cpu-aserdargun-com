"""Map original RTL to SKY130 HD and run placement/CTS/routing in cpu-lab VM."""
import pathlib, subprocess, os, json, hashlib, shlex, sys
from openroad_runner import run_openroad
root=pathlib.Path(__file__).resolve().parents[1]
platform=root/'build/tools/orfs/flow/platforms/sky130hd'
lib=platform/'lib/sky130_fd_sc_hd__tt_025C_1v80.lib'
for name,pipeline,mext in [('rv32i',0,0),('rv32im',1,1)]:
 names=[v for v in sys.argv[1:]if not v.startswith('--')]
 if names and name not in names:continue
 out=root/'build/physical'/name;out.mkdir(parents=True,exist_ok=True)
 (out/'rtl-manifest.json').write_text(json.dumps({'rtl':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'rtl/execute.sv',root/'rtl/cpu.sv',root/'rtl/physical_core.sv']},'core':name,'pipeline':pipeline,'mExtension':mext},indent=2))
 ys=f'''read_verilog -sv rtl/execute.sv rtl/cpu.sv rtl/physical_core.sv
chparam -set PIPELINE {pipeline} -set M_EXT {mext} physical_core
synth -top physical_core -flatten
dfflibmap -liberty {lib}
abc -liberty {lib}
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
clean
rename -enumerate
check
write_verilog -noattr -noexpr {out}/mapped.v
write_json {out}/mapped.json
stat -liberty {lib}
'''
 (out/'synth.ys').write_text(ys)
 with (out/'synthesis.log').open('w') as f: subprocess.run(['yosys','-s',str(out/'synth.ys')],cwd=root,stdout=f,stderr=subprocess.STDOUT,check=True)
 # Structural netlist: all behavior is in mapped cells. OpenSTA's Verilog
 # reader does not accept signed wire declarations; signedness has no effect here.
 mapped=out/'mapped.v';mapped.write_text(mapped.read_text().replace('wire signed ', 'wire '))
 if '--map-only' in sys.argv:print(name,'mapped only',flush=True);continue
 run_openroad(out,root/'scripts/physical.tcl',out/'openroad.log')
 print(name,'mapped and routed')
