"""Run in the original x86 cpu-lab VM; package its exact OpenROAD runtime.

Copies only the executable, its ldd-resolved library closure and Tcl library
into this project's ignored build tree. No unrelated VM or system file is changed.
"""
import pathlib,subprocess,re,os,shutil,json,hashlib
root=pathlib.Path(__file__).resolve().parents[1];tool=pathlib.Path.home()/'cpu-lab-tools/openroad';binary=tool/'usr/bin/openroad';out=root/'build/tools/fast-openroad';out.mkdir(parents=True,exist_ok=True)
env={**os.environ,'LD_LIBRARY_PATH':f'{tool}/opt/or-tools/lib:{tool}/usr/lib/x86_64-linux-gnu'}
text=subprocess.check_output(['ldd',str(binary)],env=env,text=True)
if 'not found' in text:raise RuntimeError(text)
files=[binary]+[pathlib.Path(p)for p in re.findall(r'=>\s+(/\S+)\s+\(',text)]+[pathlib.Path('/lib64/ld-linux-x86-64.so.2')]
manifest={}
for file in files:
 target=out/file.name;shutil.copyfile(file,target);target.chmod(file.stat().st_mode);manifest[file.name]={'source':str(file),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
shutil.copytree('/usr/share/tcltk/tcl8.6',out/'tcl8.6',dirs_exist_ok=True)
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print(len(files),'ELF runtime files packaged')
