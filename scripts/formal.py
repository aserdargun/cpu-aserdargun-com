"""Generate and run upstream riscv-formal bounded ISA checks for both cores.

Uses RV32I for pipeline control verification (M arithmetic separately compared
against Spike); exact depth and exclusions are recorded, never called full proof.
"""
import pathlib,subprocess,sys,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1];upstream=root/'build/tools/riscv-formal'
sby=root/'build/tools/sby/sbysrc/sby.py';py=root/'build/tools/formal-venv/bin/python'
names=sys.argv[1:] or ['rv32i','rv32im']
for name in names:
 core=upstream/'cores'/('cpu_lab_'+name);core.mkdir(exist_ok=True)
 cfg=f'''[options]
isa rv32i
solver bmc3
[depth]
insn 18
[defines]
`define RISCV_FORMAL_ALIGNED_MEM
`define CPU_PIPELINE {int(name=='rv32im')}
[verilog-files]
{root}/formal/rvfi_wrapper.sv
{root}/rtl/execute.sv
{root}/rtl/cpu.sv
'''
 (core/'checks.cfg').write_text(cfg)
 subprocess.run(['python3',str(upstream/'checks/genchecks.py')],cwd=core,check=True)
 # Sequential execution bounds memory usage and preserves complete individual logs.
 results={}
 for job in sorted((core/'checks').glob('insn_*.sby')):
  # The generated check predicate already selects cycle 18; ABC does not
  # support SBY's solver-specific skip option.
  job.write_text('\n'.join(l for l in job.read_text().splitlines() if not l.startswith('skip '))+'\n')
  with (core/(job.stem+'.log')).open('w') as f:r=subprocess.run([str(py),str(sby),'-f',str(job)],cwd=core/'checks',stdout=f,stderr=subprocess.STDOUT)
  status=core/'checks'/job.stem/'status';results[job.stem]=status.read_text().split()[0] if status.exists() else 'ERROR'
  print(name,job.stem,results[job.stem],flush=True)
  if r.returncode:break
 manifest={'engine':'upstream riscv-formal + SymbiYosys + ABC bmc3','core':name,'isa':'rv32i','mode':'bounded model checking','depth':18,'faultInputs':'tied zero for ISA checks; arbitrary ready/data','mArithmetic':'excluded; checked by Spike differential tests','results':results,'rtlSha256':hashlib.sha256((root/'rtl/cpu.sv').read_bytes()).hexdigest(),'sourceHashes':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [root/'rtl/cpu.sv',root/'rtl/execute.sv',root/'formal/rvfi_wrapper.sv']},'upstreamCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=upstream,text=True).strip()}
 (root/'public/sim'/f'{name}-formal.json').write_text(json.dumps(manifest,indent=2))
