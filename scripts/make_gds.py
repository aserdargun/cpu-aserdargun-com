"""Run as `klayout -b -r scripts/make_gds.py`; merge routed DEF and cell GDS."""
import pathlib,importlib.util,subprocess,hashlib,json,shutil,tempfile
import pya
root=pathlib.Path(__file__).resolve().parents[1];orfs=root/'build/tools/orfs';platform=orfs/'flow/platforms/sky130hd'
spec=importlib.util.spec_from_file_location('def2stream',orfs/'flow/util/def2stream.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for name in ['rv32i','rv32im']:
 out=root/'build/physical'/name;deffile=out/'routed.def'
 if not deffile.exists() or deffile.stat().st_mtime<(out/'mapped.v').stat().st_mtime:print(name,'routed DEF pending');continue
 tech=out/'sky130hd.lyt'
 subprocess.run(['python3',str(orfs/'flow/util/generate_klayout_tech.py'),'--template',str(platform/'sky130hd.lyt'),'--output',str(tech),'--lef-files',str(platform/'lef/sky130_fd_sc_hd.tlef'),str(platform/'lef/sky130_fd_sc_hd_merged.lef')],check=True)
 # Write on the guest's native filesystem before copying to the shared mount.
 temporary=tempfile.TemporaryDirectory(prefix='cpu-gds-');gds=pathlib.Path(temporary.name)/'cpu.gds'
 errors=module.merge_gds(pya,str(tech),'',str(deffile),'physical_core',str(platform/'gds/sky130_fd_sc_hd.gds'),'',str(gds))
 if errors:raise RuntimeError(f'{name}: {errors} missing cells / GDS merge errors')
 check=pya.Layout();check.read(str(gds));top=check.cell('physical_core');bbox=top.bbox()
 result={'core':name,'kind':'GDSII','sha256':hashlib.sha256(gds.read_bytes()).hexdigest(),'defSha256':hashlib.sha256(deffile.read_bytes()).hexdigest(),'cells':check.cells(),'layers':len(check.layer_indexes()),'dbuUm':check.dbu,'top':'physical_core','bboxUm':[v*check.dbu for v in [bbox.left,bbox.bottom,bbox.right,bbox.top]],'mergeErrors':errors,'manufacturingSignoff':False}
 shutil.copyfile(gds,out/'cpu.gds');shutil.copyfile(gds,root/'public/physical'/f'{name}.gds');(root/'public/physical'/f'{name}-gds.json').write_text(json.dumps(result,indent=2));temporary.cleanup();print(name,'GDS read-back verified',result,flush=True)
