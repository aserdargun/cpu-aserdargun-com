"""Attach retained RTL aliases to each mapped instance output probe."""
import pathlib,json,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
args=sys.argv[1:]; draft='--draft' in args
for name in [a for a in args if not a.startswith('--')] or ['rv32i','rv32im']:
 out=root/'build/physical'/name;target=(root/'build/gates'/name/'designmap.json') if draft else root/'public/physical'/f'{name}-designmap.json'
 if not target.exists():continue
 with (out/'designmap.log').open('w')as f:subprocess.run(['yosys','-p',f'read_verilog {out}/mapped.v; write_json {out}/mapped-structural.json'],stdout=f,stderr=subprocess.STDOUT,check=True)
 net=json.loads((out/'mapped-structural.json').read_text())['modules']['physical_core'];reverse={}
 for key,value in net['netnames'].items():
  if not key.startswith('core.'):continue
  for i,bit in enumerate(value['bits']):
   if isinstance(bit,int):reverse.setdefault(bit,[]).append(key+(f'[{i}]'if len(value['bits'])>1 else ''))
 manifest=json.loads(target.read_text())
 manifest['ports']=net['ports']
 for p in manifest['probes']:
  connections=net['cells'].get(p['instance'],{}).get('connections',{})
  bits=connections.get(p['pin'],[])
  p['bitId']=bits[0] if bits else None;p['connections']=connections
  p['aliases']=sorted(set(alias for bit in bits for alias in reverse.get(bit,[])))
 target.write_text(json.dumps(manifest,separators=(',',':')))
 print(name,sum(bool(p['aliases'])for p in manifest['probes']),'probe outputs with retained RTL aliases')
