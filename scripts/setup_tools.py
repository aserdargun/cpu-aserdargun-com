"""Prepare pinned upstream tooling; --physical prepares only the cpu-lab VM.

Host compilers/package manager are explicit prerequisites, documented in TOOLCHAIN.md.
Existing upstream checkouts must already match the lock; no existing checkout is reset.
"""
import argparse,pathlib,subprocess,json,hashlib,urllib.request,shlex,shutil
root=pathlib.Path(__file__).resolve().parents[1];base=root/'build/tools';base.mkdir(parents=True,exist_ok=True)
repos={
 'spike':('https://github.com/riscv-software-src/riscv-isa-sim.git','17e8a69fb75546dea445cfc0fb78769d2510f339'),
 'riscv-formal':('https://github.com/YosysHQ/riscv-formal.git','c992aa61fdfe0846c5ed90324c596202a1c69b76'),
 'sby':('https://github.com/YosysHQ/sby.git','b1a1e98cba941ec8433f8dc27f416cd7bb7f14be'),
 'orfs':('https://github.com/The-OpenROAD-Project/OpenROAD-flow-scripts.git','3451ca1f56902a49baf50bb8eba345eb709cf9c8')}
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--physical',action='store_true');parser.add_argument('--fast',action='store_true',help='prepare the same OpenROAD runtime on an ARM/Rosetta VM after --physical');args=parser.parse_args()
def run(command,**kwargs):subprocess.run(command,check=True,**kwargs)
def capture(command,**kwargs):return subprocess.check_output(command,text=True,**kwargs).strip()
versions={}
for tool in ['node','python3','verilator','emcc','yosys','ngspice','riscv64-elf-gcc','limactl']:
 if not shutil.which(tool):raise RuntimeError(f'Missing {tool}; see docs/TOOLCHAIN.md')
 lines=capture([tool,'--version']).splitlines();versions[tool]=next((line.strip()for line in lines if 'ngspice-' in line),lines[0])
for name,(url,commit)in repos.items():
 dest=base/name
 if not dest.exists():
  if args.check:raise RuntimeError(f'Missing pinned checkout: {name}')
  run(['git','init',str(dest)]);run(['git','-C',str(dest),'remote','add','origin',url]);run(['git','-C',str(dest),'fetch','--depth','1','origin',commit])
  if name=='orfs':run(['git','-C',str(dest),'sparse-checkout','set','flow/platforms/sky130hd','flow/scripts','flow/util'])
  run(['git','-C',str(dest),'checkout','--detach','FETCH_HEAD'])
 if capture(['git','-C',str(dest),'rev-parse','HEAD'])!=commit:raise RuntimeError(f'{name}: checkout differs from pinned revision; existing checkout was preserved')
# SKY130 HD points to the HS extraction rules through a symlink.
rcx=base/'orfs/flow/platforms/sky130hs/rcx_patterns.rules'
if not rcx.exists():
 if args.check:raise RuntimeError('Missing SKY130 extraction rules')
 rcx.parent.mkdir(exist_ok=True);rcx.write_text(capture(['git','-C',str(base/'orfs'),'show','HEAD:flow/platforms/sky130hs/rcx_patterns.rules'])+'\n')
venv=base/'formal-venv'
if not args.check:
 if not venv.exists():run(['python3','-m','venv',str(venv)])
 run([str(venv/'bin/python'),'-m','pip','install','click==8.5.0'])
if args.physical:
 downloads=root/'build/downloads';downloads.mkdir(exist_ok=True)
 files={
  'openroad.deb':('https://github.com/Precision-Innovations/OpenROAD/releases/download/2024-12-14/openroad_2.0-17598-ga008522d8_amd64-ubuntu-22.04.deb','40ed178396b0276a5d5dfbbe695c9de9aac9088157a6655be02b39a0cef07207'),
  'libpython3.10.deb':('https://archive.ubuntu.com/ubuntu/pool/main/p/python3.10/libpython3.10_3.10.12-1~22.04.18_amd64.deb','cd9ffe066be6207dd4fcb25fe037222e90429b0923d1a5eb6e897afcbb151833')}
 for name,(url,digest)in files.items():
  file=downloads/name
  if not file.exists():urllib.request.urlretrieve(url,file)
  if hashlib.sha256(file.read_bytes()).hexdigest()!=digest:raise RuntimeError(f'Download hash mismatch: {name}')
 states=[json.loads(line)for line in capture(['limactl','list','--json']).splitlines()if line.strip()];state=next((s for s in states if s['name']=='cpu-lab'),None)
 if not state:
  config={'vmType':'qemu','arch':'x86_64','cpus':4,'memory':'6GiB','disk':'24GiB','images':[{'location':'https://cloud-images.ubuntu.com/releases/noble/release-20260926/ubuntu-24.04-server-cloudimg-amd64.img','arch':'x86_64','digest':'sha256:6a81c37564db9b1ee84e141922625e1d7c5b389b99bb3c572e0243607d5bb4d2'}],'mounts':[{'location':str(root),'mountPoint':str(root),'writable':True}]}
  file=root/'build/cpu-lab.yaml';file.write_text(json.dumps(config,indent=2));run(['limactl','create','--name','cpu-lab',str(file)])
 elif state.get('arch')!='x86_64':raise RuntimeError('Existing cpu-lab is not x86_64; it was preserved')
 run(['limactl','start','--yes','cpu-lab'])
 # Confirm the exact project mount before installing guest tooling.
 run(['limactl','shell','cpu-lab','test','-f',str(root/'rtl/cpu.sv')])
 run(['limactl','shell','cpu-lab','sudo','apt-get','update'])
 run(['limactl','shell','cpu-lab','sudo','apt-get','install','-y','yosys','klayout','python3','make','tcl','tk','libgomp1','tcl-tclreadline','libqt5charts5'])
 command='mkdir -p "$HOME/cpu-lab-tools/openroad"; '+ ' '.join(['dpkg-deb','-x',shlex.quote(str(downloads/'openroad.deb')),'"$HOME/cpu-lab-tools/openroad"'])+'; '+ ' '.join(['dpkg-deb','-x',shlex.quote(str(downloads/'libpython3.10.deb')),'"$HOME/cpu-lab-tools/openroad"'])
 run(['limactl','shell','cpu-lab','bash','-lc',command])
if args.fast:
 run(['limactl','shell','cpu-lab','python3',str(root/'scripts/prepare_fast_runtime.py')])
 config={'vmType':'vz','arch':'aarch64','rosetta':{'enabled':True,'binfmt':True},'cpus':4,'memory':'6GiB','disk':'24GiB','images':[{'location':'https://cloud-images.ubuntu.com/releases/noble/release-20260926/ubuntu-24.04-server-cloudimg-arm64.img','arch':'aarch64','digest':'sha256:1d6bffe64b848468ac97f821d369a4846d983de1800ccf6b5ec8853e85cefc55'}],'mounts':[{'location':str(root),'mountPoint':str(root),'writable':True}],'containerd':{'system':False,'user':False}}
 file=root/'build/cpu-lab-fast.yaml';file.write_text(json.dumps(config,indent=2))
 states=[json.loads(line)for line in capture(['limactl','list','--json']).splitlines()if line.strip()]
 state=next((s for s in states if s['name']=='cpu-lab-fast'),None)
 if state and (state.get('arch')!='aarch64'or state.get('vmType')!='vz'):raise RuntimeError('Existing cpu-lab-fast is not ARM/VZ; it was preserved')
 if not state:run(['limactl','create','--name','cpu-lab-fast',str(file)])
 run(['limactl','start','--yes','cpu-lab-fast'])
 runtime=root/'build/tools/fast-openroad'
 run(['limactl','shell','cpu-lab-fast','env',f'TCL_LIBRARY={runtime}/tcl8.6','/mnt/lima-rosetta/rosetta',str(runtime/'ld-linux-x86-64.so.2'),'--library-path',str(runtime),str(runtime/'openroad'),'-version'])
lock={'hostTools':versions,'upstream':{name:{'url':url,'commit':commit}for name,(url,commit)in repos.items()},'physicalEngine':'2.0-17598-ga008522d8; dedicated x86_64 cpu-lab VM'}
runtime=base/'fast-openroad'
if (runtime/'manifest.json').exists():
 lock['physicalExecution']='same pinned x86_64 engine on cpu-lab-fast ARM/VZ/Rosetta; KLayout on cpu-lab'
 lock['physicalRuntime']=json.loads((runtime/'manifest.json').read_text())
 for name,entry in lock['physicalRuntime'].items():
  if hashlib.sha256((runtime/name).read_bytes()).hexdigest()!=entry['sha256']:raise RuntimeError(f'Runtime hash mismatch: {name}')
(root/'build/toolchain-check.json').write_text(json.dumps(lock,indent=2));print(json.dumps(lock,indent=2))
