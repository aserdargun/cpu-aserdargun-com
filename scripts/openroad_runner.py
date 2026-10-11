"""Run the identical pinned OpenROAD binary in this project's dedicated VM."""
import pathlib,subprocess,shlex,os,json,hashlib,datetime
root=pathlib.Path(__file__).resolve().parents[1]
def run_openroad(out,script,log,fast=None):
 runtime=root/'build/tools/fast-openroad';fast=runtime.joinpath('manifest.json').exists()if fast is None else fast
 env=['env',f'CPU_PLATFORM={root}/build/tools/orfs/flow/platforms/sky130hd',f'CPU_PHYSICAL_OUT={out}']
 if fast:
  command=['limactl','shell','cpu-lab-fast',*env,f'TCL_LIBRARY={runtime}/tcl8.6','/mnt/lima-rosetta/rosetta',str(runtime/'ld-linux-x86-64.so.2'),'--library-path',str(runtime),str(runtime/'openroad'),'-exit',str(script)]
 else:
  shell=f'export LD_LIBRARY_PATH="$HOME/cpu-lab-tools/openroad/opt/or-tools/lib:$HOME/cpu-lab-tools/openroad/usr/lib/x86_64-linux-gnu"; '+ ' '.join(shlex.quote(s)for s in env)+' "$HOME/cpu-lab-tools/openroad/usr/bin/openroad" -exit '+shlex.quote(str(script))
  command=['limactl','shell','cpu-lab','bash','-lc',shell]
 metadata={'vm':'cpu-lab-fast'if fast else 'cpu-lab','engine':'OpenROAD 2.0-17598-ga008522d8','startedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script':str(pathlib.Path(script).relative_to(root)),'scriptSha256':hashlib.sha256(pathlib.Path(script).read_bytes()).hexdigest(),'mappedSha256':hashlib.sha256((pathlib.Path(out)/'mapped.v').read_bytes()).hexdigest()}
 (pathlib.Path(out)/(pathlib.Path(script).stem+'-run.json')).write_text(json.dumps(metadata,indent=2))
 with pathlib.Path(log).open('w')as f:subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,check=True)
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=pathlib.Path,required=True);parser.add_argument('--script',type=pathlib.Path,required=True);parser.add_argument('--log',type=pathlib.Path,required=True);args=parser.parse_args();run_openroad(args.out.resolve(),args.script.resolve(),args.log.resolve())
