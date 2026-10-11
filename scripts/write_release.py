"""Record the actual Git commit and hashes of every prebuilt deployment asset."""
import datetime,hashlib,json,os,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[1];dist=root/'dist'
commit=os.environ.get('GITHUB_SHA')or subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
files={str(p.relative_to(dist)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}for p in sorted(dist.rglob('*'))if p.is_file()and p.name not in ['release.json']}
release={'repository':'aserdargun/cpu-aserdargun-com','commit':commit,'builtAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runId':os.environ.get('GITHUB_RUN_ID'),'artifact':'dist','files':files,'artifactSha256':hashlib.sha256(json.dumps(files,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
(dist/'release.json').write_text(json.dumps(release,indent=2))
print('Release',commit,len(files),'files',sum(f['bytes']for f in files.values()),'bytes')
