"""Extract routed RC and record STA/antenna evidence for the exact routed DEF."""
import pathlib,subprocess,shlex,json,re,hashlib,sys
from openroad_runner import run_openroad
root=pathlib.Path(__file__).resolve().parents[1];platform=root/'build/tools/orfs/flow/platforms/sky130hd'
for name in sys.argv[1:] or ['rv32i','rv32im']:
 out=root/'build/physical'/name;source=out/'routed.def'
 if not source.exists() or source.stat().st_mtime<(out/'mapped.v').stat().st_mtime:raise RuntimeError(f'{name}: current detailed routing required')
 log=out/'post-route.log'
 run_openroad(out,root/'scripts/post_route.tcl',log)
 text=log.read_text();slack=re.search(r'worst slack\s+(-?[\d.]+)',text);tns=re.search(r'tns\s+(-?[\d.]+)',text)
 antenna_nets=re.search(r'Found (\d+) net violations',text);antenna_pins=re.search(r'Found (\d+) pin violations',text)
 if not(slack and tns and antenna_nets and antenna_pins):raise RuntimeError('Incomplete RC/STA/antenna results')
 result={'core':name,'defSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'clockTargetNs':100,'parasitics':'OpenRCX extracted routed RC, SKY130 platform rcx_patterns.rules','worstSlackNs':float(slack[1]),'tnsNs':float(tns[1]),'timingTargetMet':float(slack[1])>=0 and float(tns[1])==0,'spefSha256':hashlib.sha256((out/'routed.spef').read_bytes()).hexdigest(),'antennaNetViolations':int(antenna_nets[1]),'antennaPinViolations':int(antenna_pins[1]),'antennaReport':'/physical/'+name+'-antenna.rpt','manufacturingSignoff':False}
 __import__('shutil').copyfile(out/'antenna.rpt',root/'public/physical'/f'{name}-antenna.rpt')
 (out/'timing.json').write_text(json.dumps(result,indent=2));print(result)
