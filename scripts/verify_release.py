"""Verify the published engineering evidence without the private build workspace.
This does not rerun native Spike, formal, routing or hardware performance tests.
"""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256((root/p).read_bytes()).hexdigest()
def read(p):return json.loads((root/p).read_text())
def require(ok,message):
 if not ok:raise RuntimeError(message)
v=read('public/evidence/verification.json')
require(v['status']in ['verified','functional-verified-physical-issues'],'Unaccepted engineering evidence')
require(v['tests']['passed']>=85 and v['tests']['failed']==0,'Functional acceptance')
require(v['browser']['passed']>=9 and v['browser']['failed']==0,'Browser acceptance')
require(all(c['passed']for c in v['checks']),'Recorded artifact checks')
for path,digest in v['sourceHashes'].items():require(sha(path)==digest,'Source changed since engineering acceptance: '+path)
manifest=read('public/sim/manifest.json')
for core in ['rv32i','rv32im']:
 require(sha(f'public/sim/{core}.wasm')==manifest['models'][core],core+' RTL WASM')
 gate=read(f'public/physical/{core}-designmap.json');report=read(f'public/physical/{core}-report.json');gds=read(f'public/physical/{core}-gds.json')
 for ext in ['js','wasm']:require(sha(f'public/sim/{core}-gates.{ext}')==gate[ext+'Sha256'],core+' gate '+ext)
 require(report['mappedSha256']==gate['mappedSha256']and report['status']=='detailed-routed',core+' physical correspondence')
 require(gds['defSha256']==report['defSha256']and gds['mergeErrors']==0 and sha(f'public/physical/{core}.gds')==gds['sha256'],core+' GDS')
 proof=read(f'public/sim/{core}-formal.json');require(len(proof['results'])==37 and all(r=='PASS'for r in proof['results'].values()),core+' bounded proofs')
 for path,digest in proof['sourceHashes'].items():require(sha(path)==digest,core+' proof source '+path)
for entry in read('public/physical/cells/manifest.json')['cells']:
 cell=read('public/physical/cells/'+entry['master']+'.json');require(sum(len(l['polygons'])for l in cell['layers'])==entry['polygons'],'Cell polygons '+entry['master'])
if '--dist' in sys.argv:
 for p in (root/'public').rglob('*'):
  if p.is_file():
   destination=root/'dist'/p.relative_to(root/'public');require(destination.is_file()and hashlib.sha256(destination.read_bytes()).hexdigest()==sha(p.relative_to(root)),'Dist copy '+str(p))
 require((root/'dist/index.html').is_file(),'Missing static entry point')
print(f"Published engineering evidence matches {len(v['sourceHashes'])} source files; {v['tests']['passed']} historical native/ISA tests, {v['browser']['passed']} browser workflows. Physical issues remain explicitly recorded.")
