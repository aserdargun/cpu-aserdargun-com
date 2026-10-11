import pathlib,subprocess,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
for name,pipeline,mext in [('rv32i',0,0),('rv32im',1,1),('full_adder',0,0)]:
 out=root/'build'/'synth'/name;out.mkdir(parents=True,exist_ok=True)
 files='rtl/full_adder.sv' if name=='full_adder' else 'rtl/execute.sv rtl/cpu.sv'
 top='full_adder' if name=='full_adder' else 'cpu'
 params='' if top=='full_adder' else f'chparam -set PIPELINE {pipeline} -set M_EXT {mext} cpu; '
 script=f'read_verilog -sv {files}; {params}hierarchy -top {top}; synth -top {top} -flatten; check; write_json {out}/netlist.json; stat -json'
 result=subprocess.run(['yosys','-p',script],cwd=root,capture_output=True,text=True)
 (out/'synthesis.log').write_text(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(result.stderr[-2000:])
 net=json.loads((out/'netlist.json').read_text())['modules'][top]
 cells=[{'id':k,'type':v['type'],'connections':v['connections'],'source':v.get('attributes',{}).get('src','')}for k,v in net.get('cells',{}).items()]
 artifact={'schemaVersion':1,'core':name,'kind':'synthesized-netlist','physical':False,'sourceHash':hashlib.sha256((root/'rtl/cpu.sv').read_bytes()).hexdigest(),'cellCount':len(cells),'cells':cells,'ports':net['ports']}
 (root/'public/physical'/f'{name}-netlist.json').write_text(json.dumps(artifact))
 print(name,len(cells),'cells; synthesis passed')
