"""Convert generated DEF/LEF geometry to browser data, preserving every cell.
Metal elevations in 3D are an exploded drawing, not measured process thickness.
"""
import pathlib,re,json,hashlib,sys
from def_routes import route_segments
root=pathlib.Path(__file__).resolve().parents[1]
platform=root/'build/tools/orfs/flow/platforms/sky130hd'
lef=(platform/'lef/sky130_fd_sc_hd_merged.lef').read_text()
sizes={}
for m in re.finditer(r'^MACRO (\S+)\s+(.*?)^END \1\s*$',lef,re.M|re.S):
 size=re.search(r'SIZE\s+([\d.]+)\s+BY\s+([\d.]+)',m[2]);sizes[m[1]]=[float(size[1]),float(size[2])] if size else [0,0]
for name in sys.argv[1:] or ['rv32i','rv32im']:
 out=root/'build/physical'/name
 candidates=[out/p for p in ['routed.def','global.def'] if (out/p).exists() and (out/p).stat().st_mtime>=(out/'mapped.v').stat().st_mtime]
 if not candidates:print(name,'current layout pending');continue
 deffile=candidates[0]
 text=deffile.read_text();unit=int(re.search(r'UNITS DISTANCE MICRONS (\d+)',text)[1]);die=[int(v)/unit for v in re.search(r'DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)',text).groups()]
 cells=[]
 comp=text.split('COMPONENTS ',1)[1].split('END COMPONENTS',1)[0]
 for cell in re.finditer(r'^\s*-\s+(\S+)\s+(\S+).*?\+\s+(?:PLACED|FIXED)\s+\(\s+(-?\d+)\s+(-?\d+)\s+\)\s+(\S+)\s*;',comp,re.M|re.S):
  instance,master,x,y,orientation=cell.groups()
  if master not in sizes:raise ValueError(f'Unknown LEF master {master}')
  cells.append([instance,master,int(x)/unit,int(y)/unit,*sizes[master],orientation])
 expected=int(comp.split(';',1)[0]);assert len(cells)==expected,(name,len(cells),expected)
 nets='\n'.join(section[1] for section in re.finditer(r'^(?:SPECIALNETS|NETS)\s+\d+\s*;(.*?)^END (?:SPECIALNETS|NETS)',text,re.M|re.S))
 routes,net_count=route_segments(nets,unit)
 log=(out/'openroad.log').read_text();log=((out/'global-stage.log').read_text()if (out/'global-stage.log').exists()else '')+log;area=re.search(r'Design area (\S+) u',log);slack=re.search(r'worst slack\s+(-?[\d.]+)',log)
 artifact={'schemaVersion':1,'core':name,'kind':'physical-layout','physical':True,'status':'detailed-routed' if deffile.name=='routed.def' else 'placed-and-global-routed','units':'um','platform':'SKY130 HD TT 25C 1.8V','die':die,'cellCount':len(cells),'netCount':net_count,'routeSegmentCount':len(routes),'cells':cells,'routes':routes,'cellFormat':['instance','master','x','y','width','height','orientation'],'routeFormat':['net','layer','x1','y1','x2','y2'],'routeGeometry':'DEF centerlines; full width, cut and via geometry is in the native GDS','metalHeights':'illustrative exploded layer spacing; XY is exact DEF geometry','sourceHash':hashlib.sha256((root/'rtl/cpu.sv').read_bytes()).hexdigest(),'defSha256':hashlib.sha256(deffile.read_bytes()).hexdigest(),'platformCommit':__import__('subprocess').check_output(['git','rev-parse','HEAD'],cwd=platform,text=True).strip(),'timing':{'clockTargetNs':100,'worstSlackNs':float(slack[1]) if slack else None,'cellAreaUm2':float(area[1]) if area else None},'manufacturingSignoff':False}
 drc=re.findall(r'Number of violations\s*=\s*(\d+)',log);artifact['routerDrcViolations']=int(drc[-1])if drc and deffile.name=='routed.def' else None
 artifact['drcScope']='OpenROAD detailed-router DRC, not full foundry DRC/LVS signoff'
 timing=out/'timing.json'
 if timing.exists():
  post=json.loads(timing.read_text())
  if post['defSha256']==artifact['defSha256']:artifact['postRouteTiming']=post
 artifact['runtime']='OpenROAD 2.0-17598-ga008522d8'
 artifact['rtlManifest']=json.loads((out/'rtl-manifest.json').read_text()) if (out/'rtl-manifest.json').exists() else None
 artifact['mappedSha256']=hashlib.sha256((out/'mapped.v').read_bytes()).hexdigest()
 (root/'public/physical'/f'{name}-layout.json').write_text(json.dumps(artifact,separators=(',',':')))
 (root/'public/physical'/f'{name}-report.json').write_text(json.dumps({k:v for k,v in artifact.items() if k not in ['cells','routes']},indent=2))
 print(name,len(cells),'cells;',len(routes),'route segments;',artifact['status'])
