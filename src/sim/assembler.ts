import type {ProgramImage} from './types';
const aliases:Record<string,number>={zero:0,ra:1,sp:2,gp:3,tp:4,t0:5,t1:6,t2:7,s0:8,fp:8,s1:9,a0:10,a1:11,a2:12,a3:13,a4:14,a5:15,a6:16,a7:17,s2:18,s3:19,s4:20,s5:21,s6:22,s7:23,s8:24,s9:25,s10:26,s11:27,t3:28,t4:29,t5:30,t6:31};
const r=(x:string)=>{if(Object.hasOwn(aliases,x))return aliases[x];const m=/^x(\d+)$/.exec(x);if(m&&+m[1]<32)return +m[1];throw new Error(`Yazmaç / register: ${x}`)};
function num(x:string,labels:Record<string,number>){if(x in labels)return labels[x];if(/^[-+]?(?:0x[0-9a-f]+|0b[01]+|\d+)$/i.test(x)){const v=(x[0]==='-'?-1:1)*Number(x.replace(/^[-+]/,''));if(Number.isSafeInteger(v))return v;}if(/^'.'$/.test(x))return x.charCodeAt(1);throw new Error(`Sayı veya etiket / number or label: ${x}`)}
const range=(v:number,bits:number)=>{if(!Number.isInteger(v)||v<-(2**(bits-1))||v>2**(bits-1)-1)throw new Error(`${bits}-bit immediate: ${v}`);return v&((2**bits)-1)};
const R=(f7:number,f3:number,d:number,a:number,b:number)=>((f7<<25)|(b<<20)|(a<<15)|(f3<<12)|(d<<7)|0x33)>>>0;
const I=(op:number,f3:number,d:number,a:number,v:number)=>((range(v,12)<<20)|(a<<15)|(f3<<12)|(d<<7)|op)>>>0;
export function assemble(source:string,name='program.s'):ProgramImage{
 const labels:Record<string,number>=Object.create(null),lines:Record<number,number>={},segments=new Map<number,number[]>();
 const stripComment=(s:string)=>{let quoted=false,escape=false;for(let i=0;i<s.length;i++){if(escape){escape=false;continue;}if(s[i]==='\\'){escape=true;continue;}if(s[i]==='"')quoted=!quoted;if(s[i]==='#'&&!quoted)return s.slice(0,i);}return s;};
 const raw=source.split('\n').map((s,i)=>({s:stripComment(s).trim(),line:i+1}));
 function pass(emit:boolean){let pc=0;for(const row of raw){let s=row.s;if(!s)continue;while(/^\w+:/.test(s)){const k=s.slice(0,s.indexOf(':'));if(!emit){if(k in labels)throw new Error(`Tekrarlı etiket / duplicate label ${k}`);labels[k]=pc;}s=s.slice(s.indexOf(':')+1).trim();}if(!s)continue;
 try{
  if(s==='.text'){pc=0;continue;}if(s==='.data'){pc=0x10000000;continue;}
  if(/^\.(globl|global|type|size|option)\b/.test(s))continue;
  const value=(x:string)=>{if(emit)return num(x,labels);try{return num(x,Object.create(null))}catch{return 0}};
  const write=(bytes:number[])=>{if(emit){if(!(pc>=0&&pc+bytes.length<=65536)&&!(pc>=0x10000000&&pc+bytes.length<=0x10010000))throw new Error('Bellek sınırı / memory bounds');for(let i=0;i<bytes.length;i++){if(segments.has(pc+i))throw new Error('Çakışan adres / overlapping address');segments.set(pc+i,[bytes[i]&255]);}lines[pc]=row.line;}pc+=bytes.length;};
  if(s.startsWith('.org ')){pc=num(s.slice(5).trim(),labels);continue;}
  if(s.startsWith('.align ')){const power=num(s.slice(7).trim(),labels);if(!Number.isInteger(power)||power<0||power>16)throw new Error('align range: 0..16');const align=2**power;write(new Array((align-pc%align)%align).fill(0));continue;}
  if(s.startsWith('.space ')){const length=num(s.slice(7).trim(),labels);if(length<0||length>65536)throw new Error('space range');write(new Array(length).fill(0));continue;}
  const directive=/^\.(word|byte)\s+(.+)$/.exec(s);if(directive){const bytes:number[]=[];for(const x of directive[2].split(',').map(x=>x.trim())){const v=value(x);if(directive[1]==='byte')bytes.push(v&255);else bytes.push(v&255,v>>>8&255,v>>>16&255,v>>>24&255);}write(bytes);continue;}
  const str=/^\.(ascii|asciz)\s+(".*")$/.exec(s);if(str){const bytes=Array.from(new TextEncoder().encode(JSON.parse(str[2])));if(str[1]==='asciz')bytes.push(0);write(bytes);continue;}
  if(s.startsWith('.'))throw new Error(`Desteklenmeyen direktif / unsupported directive ${s}`);
  let [op,...args]=s.replace(/,/g,' ').trim().split(/\s+/);const insns:number[]=[];
  const add=(x:number)=>insns.push(x>>>0);
  const pseudoCount:Record<string,number>={nop:0,mv:2,ret:0,j:1,call:1,beqz:2,bnez:2};if(op in pseudoCount&&args.length!==pseudoCount[op])throw new Error(`Operand count: ${op} expects ${pseudoCount[op]}`);
  if(op==='nop'){op='addi';args=['x0','x0','0'];}if(op==='mv'){op='addi';args=[args[0],args[1],'0'];}if(op==='ret'){op='jalr';args=['x0','0(ra)'];}if(op==='j'){op='jal';args=['x0',args[0]];}if(op==='call'){op='jal';args=['ra',args[0]];}if(op==='beqz'||op==='bnez'){op=op==='beqz'?'beq':'bne';args=[args[0],'x0',args[1]];}
  if(op==='jal'&&args.length===1)args=['ra',args[0]];
  const operandCount=['ecall','ebreak','fence'].includes(op)?0:['li','la','lui','auipc','jal','jalr','lb','lh','lw','lbu','lhu','sb','sh','sw'].includes(op)?2:3;
  if(args.length!==operandCount)throw new Error(`Operand count: ${op} expects ${operandCount}`);
  const n=(i:number)=>value(args[i]);const d=()=>r(args[0]);const a=()=>r(args[1]);const b=()=>r(args[2]);
  if(op==='li'||op==='la'){const immediate=n(1);if(immediate< -0x80000000||immediate>0xffffffff)throw new Error('32-bit immediate range');const v=immediate|0;const symbolic=/^[A-Za-z_]\w*$/.test(args[1]);const two=op==='la'||symbolic||v< -2048||v>2047;if(two){add((((v+0x800)>>>12)<<12)|(d()<<7)|0x37);add(I(0x13,0,d(),d(),(v<<20)>>20));}else add(I(0x13,0,d(),0,v));}
  else if(op==='lui'||op==='auipc'){const v=n(1);if(v<0||v>0xfffff)throw new Error('U immediate range');add((v<<12)|(d()<<7)|(op==='lui'?0x37:0x17));}
  else if(op==='ecall'||op==='ebreak')add(op==='ecall'?0x73:0x100073);
  else if(op==='fence')add(0x0ff0000f);
  else if(op==='jal'){const v=range(value(args[1])-pc,21);if(v&1)throw new Error('jump alignment');add(((v>>>20)<<31)|((v>>>1&1023)<<21)|((v>>>11&1)<<20)|((v>>>12&255)<<12)|(d()<<7)|0x6f);}
  else if(['beq','bne','blt','bge','bltu','bgeu'].includes(op)){const f3={beq:0,bne:1,blt:4,bge:5,bltu:6,bgeu:7}[op]!;const v=range(value(args[2])-pc,13);if(v&1)throw new Error('branch alignment');add(((v>>>12)<<31)|((v>>>5&63)<<25)|(r(args[1])<<20)|(r(args[0])<<15)|(f3<<12)|((v>>>1&15)<<8)|((v>>>11&1)<<7)|0x63);}
  else if(op==='jalr'||['lb','lh','lw','lbu','lhu','sb','sh','sw'].includes(op)){const m=/^(.+)\((\w+)\)$/.exec(args[1]);if(!m)throw new Error('offset(register)');const off=range(value(m[1]),12),base=r(m[2]);if(op==='jalr')add(I(0x67,0,d(),base,(off<<20)>>20));else if(op.startsWith('s')){const f3={sb:0,sh:1,sw:2}[op]!;add((off>>>5<<25)|(d()<<20)|(base<<15)|(f3<<12)|((off&31)<<7)|0x23);}else add(I(3,{lb:0,lh:1,lw:2,lbu:4,lhu:5}[op]!,d(),base,(off<<20)>>20));}
  else if(['addi','slti','sltiu','xori','ori','andi','slli','srli','srai'].includes(op)){const f3={addi:0,slti:2,sltiu:3,xori:4,ori:6,andi:7,slli:1,srli:5,srai:5}[op]!;let v=n(2);if(['slli','srli','srai'].includes(op)){if(v<0||v>31)throw new Error('shift range');if(op==='srai')v|=0x400;}add(I(0x13,f3,d(),a(),v));}
  else {const map:Record<string,[number,number]>={add:[0,0],sub:[0x20,0],sll:[0,1],slt:[0,2],sltu:[0,3],xor:[0,4],srl:[0,5],sra:[0x20,5],or:[0,6],and:[0,7],mul:[1,0],mulh:[1,1],mulhsu:[1,2],mulhu:[1,3],div:[1,4],divu:[1,5],rem:[1,6],remu:[1,7]};if(!map[op])throw new Error(`Komut / instruction: ${op}`);add(R(...map[op],d(),a(),b()));}
  if(pc%4)throw new Error('Komut hizası / instruction alignment');write(insns.flatMap(v=>[v&255,v>>>8&255,v>>>16&255,v>>>24&255]));
 }catch(e){throw new Error(`Satır / line ${row.line}: ${(e as Error).message}`);}
 }}
 pass(false);pass(true);const addresses=[...segments.keys()].sort((a,b)=>a-b);const grouped:ProgramImage['segments']=[];for(const addr of addresses){const last=grouped.at(-1);if(last&&last.address+last.bytes.length===addr)last.bytes.push(...segments.get(addr)!);else grouped.push({address:addr,bytes:segments.get(addr)!});}
 return {language:'assembly',name,source,entry:0,segments:grouped,symbols:labels,lines};
}
export function loadElf(buffer:ArrayBuffer,name:string):ProgramImage{
 const v=new DataView(buffer);if(v.byteLength<52||v.getUint32(0,true)!==0x464c457f||v.getUint8(4)!==1||v.getUint8(5)!==1||v.getUint16(18,true)!==243)throw new Error('ELF32 little-endian RISC-V gerekli / required');
 const entry=v.getUint32(24,true);if(entry!==0)throw new Error('Giriş adresi 0 olmalı / entry must be 0');
 const segments:ProgramImage['segments']=[];const ph=v.getUint32(28,true),size=v.getUint16(42,true),count=v.getUint16(44,true);if(size<32||count>128)throw new Error('ELF program header');
 for(let i=0;i<count;i++){const p=ph+i*size;if(p+32>v.byteLength)throw new Error('ELF bounds');if(v.getUint32(p,true)!==1)continue;const offset=v.getUint32(p+4,true),address=v.getUint32(p+8,true),fs=v.getUint32(p+16,true),ms=v.getUint32(p+20,true);if(fs>ms||offset+fs>v.byteLength||!((address+ms<=65536)||(address>=0x10000000&&address+ms<=0x10010000)))throw new Error('ELF segment bounds');const bytes=new Array(ms).fill(0);bytes.splice(0,fs,...new Uint8Array(buffer,offset,fs));segments.push({address,bytes});}
 return validateImage({language:'elf',name,source:'// ELF32 · yerel derleyici / local compiler',entry,segments,symbols:{},lines:{}});
}
export function disassemble(i:number){if(!i)return '—';if(i===0x100073)return 'ebreak';if(i===0x73)return 'ecall';const op=i&127,d=i>>>7&31,a=i>>>15&31,b=i>>>20&31,f=i>>>12&7,f7=i>>>25;const imm=i>>20;
 if(op===0x13)return `${['addi','slli','slti','sltiu','xori',f7===32?'srai':'srli','ori','andi'][f]} x${d}, x${a}, ${f===1||f===5?b:imm}`;
 if(op===0x33)return `${f7===1?['mul','mulh','mulhsu','mulhu','div','divu','rem','remu'][f]:['add','sll','slt','sltu','xor','srl','or','and'].map((n,k)=>f7===32?(k===0?'sub':k===5?'sra':n):n)[f]} x${d}, x${a}, x${b}`;
 if(op===3)return `${['lb','lh','lw','?','lbu','lhu'][f]} x${d}, ${imm}(x${a})`;
 if(op===0x23)return `${['sb','sh','sw'][f]} x${b}, ${(i>>25<<5)|(i>>>7&31)}(x${a})`;
 if(op===0x37||op===0x17)return `${op===0x37?'lui':'auipc'} x${d}, 0x${(i>>>12).toString(16)}`;
 if(op===0x63)return `${({0:'beq',1:'bne',4:'blt',5:'bge',6:'bltu',7:'bgeu'} as Record<number,string>)[f]} x${a}, x${b}`;
 if(op===0x6f)return `jal x${d}`;if(op===0x67)return `jalr x${d}, ${imm}(x${a})`;if(op===0xf)return 'fence';return '0x'+i.toString(16).padStart(8,'0');}

export function validateImage(data:unknown):ProgramImage {const p=data as ProgramImage;if(!p||typeof p.name!=='string'||typeof p.source!=='string'||p.source.length>1000000||p.entry!==0||!Array.isArray(p.segments)||p.segments.length>128)throw new Error('Geçersiz program / invalid program');const used=new Set<number>();for(const seg of p.segments){if(!Number.isInteger(seg.address)||!Array.isArray(seg.bytes)||seg.bytes.length>65536||!((seg.address>=0&&seg.address+seg.bytes.length<=65536)||(seg.address>=0x10000000&&seg.address+seg.bytes.length<=0x10010000)))throw new Error('Segment bounds');seg.bytes.forEach((b,i)=>{if(!Number.isInteger(b)||b<0||b>255||used.has(seg.address+i))throw new Error('Segment bytes / overlap');used.add(seg.address+i);});}return {...p,symbols:p.symbols??{},lines:p.lines??{}};}
