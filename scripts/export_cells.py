"""Run with Linux system Python (apt KLayout pya) to export mask polygons."""
import pathlib,json,re,hashlib
import pya
root=pathlib.Path(__file__).resolve().parents[1]
platform=root/'build/tools/orfs/flow/platforms/sky130hd'
gds=platform/'gds/sky130_fd_sc_hd.gds'
gds_hash=hashlib.sha256(gds.read_bytes()).hexdigest()
layout=pya.Layout();layout.read(str(gds))
layer_names={}
for name,layer,datatype in re.findall(r"'([^']+) : (\d+)/(\d+)'",(platform/'sky130hd.lyt').read_text()):layer_names[(int(layer),int(datatype))]=name
out=root/'public/physical/cells';out.mkdir(parents=True,exist_ok=True)
manifest=[]
for cell in layout.each_cell():
 if not cell.name.startswith('sky130_fd_sc_hd__'):continue
 layers=[]
 for index in layout.layer_indexes():
  info=layout.get_info(index);polygons=[]
  iterator=cell.begin_shapes_rec(index)
  while not iterator.at_end():
   shape=iterator.shape();poly=shape.polygon if shape.is_polygon() else pya.Polygon(shape.box) if shape.is_box() else shape.path.polygon() if shape.is_path() else None
   if poly is not None:
    poly=poly.transformed(iterator.trans());hull=[[round(p.x*layout.dbu,4),round(p.y*layout.dbu,4)]for p in poly.each_point_hull()];holes=[[[round(p.x*layout.dbu,4),round(p.y*layout.dbu,4)]for p in poly.each_point_hole(i)]for i in range(poly.holes())]
    polygons.append({'hull':hull,'holes':holes})
   iterator.next()
  if polygons:layers.append({'layer':info.layer,'datatype':info.datatype,'name':layer_names.get((info.layer,info.datatype),f'{info.layer}/{info.datatype}'),'polygons':polygons})
 bbox=cell.bbox();bounds=[round(v*layout.dbu,4)for v in [bbox.left,bbox.bottom,bbox.right,bbox.top]]
 data={'schemaVersion':1,'master':cell.name,'source':'SKY130 HD GDS mask geometry via KLayout','units':'um','bounds':bounds,'layers':layers,'verticalCoordinates':'illustrative exploded mask layers; GDS has XY geometry only','gdsSha256':gds_hash}
 (out/f'{cell.name}.json').write_text(json.dumps(data,separators=(',',':')))
 manifest.append({'master':cell.name,'bounds':bounds,'layers':len(layers),'polygons':sum(len(l['polygons'])for l in layers)})
 print(cell.name,manifest[-1]['polygons'],flush=True)
(out/'manifest.json').write_text(json.dumps({'sourceSha256':gds_hash,'cells':manifest},indent=2))
