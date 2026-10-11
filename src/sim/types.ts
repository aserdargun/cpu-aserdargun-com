export type CoreId='rv32i'|'rv32im';
export type Lang='tr'|'en';
export type ViewId='system'|'datapath'|'gates'|'transistor'|'physical';
export interface Stage {valid:number;pc:number;insn:number}
export interface TraceFrame {cycle:number;instret:number;pc:number;insn:number;state:number;halted:boolean;trap:number;trapPc:number;trapAddr:number;a:number;b:number;result:number;stall:boolean;flush:boolean;regwrite:boolean;stalls:number;branches:number;regs:number[];stages:Stage[];retire:{valid:number;pc:number;insn:number;rd:number;value:number};bus:{req:number;write:number;addr:number;data:number;size:number;ready:number};cache:{enabled:boolean;ihit:number;imiss:number;dhit:number;dmiss:number};gpio:number;uart:number[]}
export interface ProgramImage {language?:'assembly'|'c'|'elf';name:string;source:string;entry:number;segments:{address:number;bytes:number[]}[];symbols:Record<string,number>;lines:Record<number,number>;instructions?:{pc:number;word:number;assembly:string}[]}
export interface SimulationConfig {core:CoreId;latency:number;cache:boolean}
export type SimulationCommand=({type:'load';image:ProgramImage;config:SimulationConfig;cycle?:number}|{type:'step';instruction?:boolean}|{type:'run';breakpoints:number[];watchpoints:number[]}|{type:'pause';sentAt?:number}|{type:'seek';cycle:number}|{type:'memory';address:number;length:number})&{generation?:number};
export type SimulationReply=({type:'frames';frames:TraceFrame[];running:boolean;reason?:string;pauseLatencyMs?:number}|{type:'ready';frame:TraceFrame}|{type:'memory';address:number;bytes:number[]}|{type:'error';message:string})&{generation?:number};
export const hex=(n:number,width=8)=>'0x'+(n>>>0).toString(16).padStart(width,'0');
export const trapNames:Record<number,[string,string]>={1:['Komut adresi hatası','Instruction address fault'],2:['Geçersiz komut','Illegal instruction'],3:['EBREAK · program durdu','EBREAK · program stopped'],4:['Hizasız okuma','Misaligned load'],5:['Okuma adresi hatası','Load access fault'],6:['Hizasız yazma','Misaligned store'],7:['Yazma adresi hatası','Store access fault'],11:['ECALL · ortam çağrısı','ECALL · environment call']};
