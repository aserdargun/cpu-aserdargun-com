"""Educational transistor experiments; LEVEL=1 model is explicitly not a PDK."""
import pathlib,subprocess,json
root=pathlib.Path(__file__).resolve().parents[1];out=root/'build/spice';out.mkdir(parents=True,exist_ok=True)
models='''.model NM NMOS (LEVEL=1 VTO=0.45 KP=120u LAMBDA=0.02)
.model PM PMOS (LEVEL=1 VTO=-0.45 KP=60u LAMBDA=0.02)
'''
circuits={
'inverter':('CMOS inverter','Mp out in vdd vdd PM W=2u L=0.18u\nMn out in 0 0 NM W=1u L=0.18u\n',['in','out']),
'nand':('CMOS NAND, parallel PMOS and series NMOS','Vb b 0 PULSE(0 1.8 2n 100p 100p 2n 4n)\nMp1 out in vdd vdd PM W=2u L=0.18u\nMp2 out b vdd vdd PM W=2u L=0.18u\nMn1 out in mid 0 NM W=2u L=0.18u\nMn2 mid b 0 0 NM W=2u L=0.18u\n',['in','out','b']),
'chain':('Two inverter buffer','Mp1 mid in vdd vdd PM W=2u L=0.18u\nMn1 mid in 0 0 NM W=1u L=0.18u\nCmid mid 0 10f\nMp2 out mid vdd vdd PM W=2u L=0.18u\nMn2 out mid 0 0 NM W=1u L=0.18u\n',['in','out','mid'])}
for name,(title,devices,signals) in circuits.items():
 circuit=f'''{title} educational level-1 model
Vdd vdd 0 1.8
Vin in 0 PULSE(0 1.8 1n 100p 100p 4n 8n)
{devices}Cload out 0 10f
{models}.control
tran 20p 20n
set wr_singlescale
set wr_vecnames
wrdata {name}.dat {' '.join('v('+s+')'for s in signals)}
quit
.endc
.end
'''
 (out/f'{name}.cir').write_text(circuit)
 r=subprocess.run(['ngspice','-b',f'{name}.cir'],cwd=out,capture_output=True,text=True,check=True)
 (out/f'{name}.log').write_text(r.stdout+r.stderr)
 rows=[]
 for line in (out/f'{name}.dat').read_text().splitlines()[1:]:
  vals=list(map(float,line.split()));row={'ns':vals[0]*1e9,'input':vals[1],'output':vals[2]}
  if len(vals)>3:row['b' if name=='nand' else 'mid']=vals[3]
  rows.append(row)
 # Steady state samples independently exercise each transistor network's truth table.
 checked=0
 for ns in [0.5,2.7,4.7,6.7,8.7,10.7,12.7,14.7,16.7,18.7]:
  row=min(rows,key=lambda r:abs(r['ns']-ns));a=row['input']>.9
  expected=(not a) if name=='inverter' else (not(a and row['b']>.9)) if name=='nand' else a
  assert (row['output']>.9)==expected,(name,ns,row)
  checked+=1
 (root/'public/sim'/f'{name}.json').write_text(json.dumps({'name':name,'source':'ngspice transient analysis','model':'Educational MOS LEVEL=1, not SKY130','vdd':1.8,'samples':rows,'circuit':circuit,'steadyTruthChecks':checked},indent=2))
 print(name,len(rows),'transient samples;',checked,'steady-state checks passed')
