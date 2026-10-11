import type {SimulationCommand,SimulationReply,SimulationConfig,ProgramImage,TraceFrame} from './types';
interface Wasm {_create():void;_configure(a:number,b:number):void;_put_byte(a:number,b:number):void;_get_byte(a:number):number;_reset():void;_step():void;_snapshot():number;UTF8ToString(p:number):string}
let model:Wasm|null=null,image:ProgramImage,config:SimulationConfig,running=false,epoch=0,generation=0,breakpoints:number[]=[],watchpoints:number[]=[];
const emit=(reply:SimulationReply)=>postMessage({...reply,generation});
const frame=():TraceFrame=>JSON.parse(model!.UTF8ToString(model!._snapshot()));
function reset(){model!._create();model!._configure(config.latency,config.cache?1:0);for(const seg of image.segments)for(let i=0;i<seg.bytes.length;i++)model!._put_byte(seg.address+i,seg.bytes[i]);model!._reset();}
async function replay(cycle:number,token:number){let left=Math.min(1_000_000,Math.max(0,Math.floor(cycle)));const frames:TraceFrame[]=[];while(left>0&&!frame().halted){const start=performance.now();while(left>0&&performance.now()-start<8&&!frame().halted){model!._step();left--;if(left<128)frames.push(frame());}await new Promise(r=>setTimeout(r,0));if(token!==epoch)return null;}return frames.length?frames:[frame()];}
async function init(cycle=0){const token=++epoch;running=false;model=null;const currentConfig=config;const mod=await import(/* @vite-ignore */ `${import.meta.env.BASE_URL}sim/${currentConfig.core}.js`);const instance:Wasm=await mod.default({locateFile:(f:string)=>`${import.meta.env.BASE_URL}sim/${f}`});if(token!==epoch)return;model=instance;reset();if(cycle){const frames=await replay(cycle,token);if(!frames)return;}emit({type:'ready',frame:frame()});}
function batch(token:number){if(token!==epoch||!running||!model)return;const frames:TraceFrame[]=[];let reason:string|undefined;const start=performance.now();while(frames.length<64&&performance.now()-start<8){model._step();const f=frame();frames.push(f);if(f.halted){running=false;reason='trap';break;}if(f.stages[1].valid&&breakpoints.includes(f.stages[1].pc)){running=false;reason='breakpoint';break;}if(f.bus.req&&watchpoints.includes(f.bus.addr)){running=false;reason='watchpoint';break;}}emit({type:'frames',frames,running,reason});if(running)setTimeout(()=>batch(token),16);}
onmessage=async ({data}:{data:SimulationCommand})=>{try{
 if(data.type==='load'){generation=data.generation??0;image=data.image;config=data.config;await init(data.cycle);return;}
 if((data.generation??0)!==generation)return;
 if(!model)throw new Error('RTL modeli yüklenmedi / RTL model not loaded');
 if(data.type==='pause'){epoch++;running=false;emit({type:'frames',frames:[frame()],running,pauseLatencyMs:data.sentAt===undefined?undefined:performance.timeOrigin+performance.now()-data.sentAt});}
 if(data.type==='run'){breakpoints=data.breakpoints;watchpoints=data.watchpoints;if(!running&&!frame().halted){running=true;batch(++epoch);}}
 if(data.type==='step'){epoch++;running=false;const start=frame();const frames:TraceFrame[]=[];do{model._step();frames.push(frame());}while(data.instruction&&frames.at(-1)!.instret===start.instret&&!frames.at(-1)!.halted&&frames.length<1000);emit({type:'frames',frames,running});}
 if(data.type==='seek'){const token=++epoch;running=false;reset();const frames=await replay(data.cycle,token);if(frames)emit({type:'frames',frames,running});}
 if(data.type==='memory'){const length=Math.min(512,Math.max(0,data.length));emit({type:'memory',address:data.address,bytes:Array.from({length},(_,i)=>model!._get_byte(data.address+i))});}
 }catch(e){if((data.generation??0)!==generation)return;running=false;emit({type:'error',message:(e as Error).message});}};
