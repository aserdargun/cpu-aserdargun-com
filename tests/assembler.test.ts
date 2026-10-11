import {describe,it,expect} from 'vitest';
import {assemble,loadElf} from '../src/sim/assembler';
import {programs} from '../src/content/programs';
describe('RISC-V assembly input',()=>{
 it('encodes canonical instructions',()=>{const p=assemble('addi x1,x0,5\naddi x2,x0,7\nadd x3,x1,x2\nebreak');const bytes=Uint8Array.from(p.segments[0].bytes);const v=new DataView(bytes.buffer);expect([0,4,8,12].map(i=>v.getUint32(i,true))).toEqual([0x500093,0x700113,0x2081b3,0x100073]);});
 it('assembles every experiment with separate code and data',()=>{for(const p of programs){const result=assemble(p.source);expect(result.segments[0].address).toBe(0);expect(result.segments[0].bytes.length).toBeGreaterThan(0);}});
 it('rejects register, shift, immediate, duplicate labels and overlap',()=>{for(const s of ['addi x32,x0,1','slli x1,x2,32','addi x1,x0,2048','x:\nnop\nx:\nnop','.word 1\n.org 0\n.word 2'])expect(()=>assemble(s)).toThrow();});
 it('rejects truncated / incompatible ELF',()=>expect(()=>loadElf(new ArrayBuffer(24),'bad')).toThrow());
});
it('keeps two-pass widths stable for binary and symbolic li and preserves quoted #',()=>{const image=assemble('li x1, 0b10000000000000\nli x2, target\ntarget: ebreak\n.data\n.asciz "A#B"');expect(image.symbols.target).toBe(16);expect(image.segments[0].bytes.length).toBe(20);expect(image.segments[1].bytes).toEqual([65,35,66,0]);expect(()=>assemble('addi x1, x0, 1, 2')).toThrow('Operand count');expect(()=>assemble('.align 30')).toThrow('align range');});
it('encodes signed hexadecimal/binary literals and rejects malformed pseudo operands and oversized li',()=>{expect(assemble('li x1,-0x1\nli x2,+0b10').segments[0].bytes).toEqual(assemble('li x1,-1\nli x2,2').segments[0].bytes);for(const src of ['nop x1','ret x1','mv x1','li x1,0x100000000','li x1,999999999999999999999'])expect(()=>assemble(src)).toThrow();});
