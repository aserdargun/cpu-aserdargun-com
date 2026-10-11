"""Compile one bare-metal C source into a browser-importable ELF32/DWARF image."""
import argparse, pathlib, subprocess, json, re, hashlib, struct
root=pathlib.Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',type=pathlib.Path,default=root/'examples/sum.c')
parser.add_argument('--name',default=None,help='output basename; defaults to the source stem')
parser.add_argument('--isa',choices=['rv32i','rv32im'],default='rv32i')
parser.add_argument('--output-dir',type=pathlib.Path,default=root/'public/programs')
args=parser.parse_args();source=args.source.resolve();name=args.name or source.stem
if not re.fullmatch(r'[A-Za-z0-9_-]+',name):parser.error('--name must contain only letters, numbers, hyphens or underscores')
if not source.is_file():parser.error(f'C source does not exist: {source}')
out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);elf=out/f'{name}.elf'
command=['riscv64-elf-gcc',f'-march={args.isa}','-mabi=ilp32','-O1','-g','-ffreestanding','-fno-builtin','-nostdlib','-fno-pic','-msmall-data-limit=0','-Wl,-T,examples/link.ld','examples/start.S',str(source),'-o',str(elf)]
subprocess.run(command,cwd=root,check=True)
dis=subprocess.check_output(['riscv64-elf-objdump','-d','-S',str(elf)],text=True)
(out/f'{name}.disassembly.txt').write_text(dis)
syms=subprocess.check_output(['riscv64-elf-nm','-n',str(elf)],text=True)
symbols={m.group(3):int(m.group(1),16) for line in syms.splitlines() if (m:=re.match(r'([0-9a-f]+)\s+(\w)\s+(\S+)',line))}
addresses=re.findall(r'^\s*([0-9a-f]+):\s+[0-9a-f]+\s',dis,re.M)
locations=subprocess.check_output(['riscv64-elf-addr2line','-e',str(elf),*[f'0x{a}' for a in addresses]],text=True).splitlines()
lines={}
for address,location in zip(addresses,locations):
    m=re.match(r'(.*?):(\d+)',location)
    if m and pathlib.Path(m[1]).resolve()==source and int(m[2]):lines[int(address,16)]=int(m[2])
instructions=[{'pc':int(m[1],16),'word':int(m[2],16),'assembly':m[3].strip()}for m in re.finditer(r'^\s*([0-9a-f]+):\s+([0-9a-f]{8})\s+(.+)$',dis,re.M)]
meta={'source':source.read_text(),'symbols':symbols,'lines':lines,'instructions':instructions,'isa':args.isa,'elfSha256':hashlib.sha256(elf.read_bytes()).hexdigest(),'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'compiler':subprocess.check_output(['riscv64-elf-gcc','--version'],text=True).splitlines()[0],'contract':'one C translation unit, main(), freestanding, no libc; linker limits code/data to 64 KiB each'}
(out/f'{name}.debug.json').write_text(json.dumps(meta,indent=2))
binary=elf.read_bytes();entry,ph=struct.unpack_from('<II',binary,24);size,count=struct.unpack_from('<HH',binary,42)
segments=[]
for i in range(count):
    kind,offset,address,_,filesize,memsize=struct.unpack_from('<IIIIII',binary,ph+i*size)
    if kind==1:segments.append({'address':address,'bytes':list(binary[offset:offset+filesize])+[0]*(memsize-filesize)})
image={'name':source.name,'source':meta['source'],'language':'c','entry':entry,'segments':segments,'symbols':symbols,'lines':lines,'instructions':instructions}
(out/f'{name}.experiment.json').write_text(json.dumps({'schemaVersion':1,'image':image,'config':{'core':args.isa,'latency':1,'cache':False},'cycle':0,'breakpoint':'','watchpoint':''},indent=2))
print(f'C → ELF32: {elf}; {len(lines)} instructions mapped to C lines; ISA {args.isa}')
