import {useEffect,useRef,useState} from 'react';
import type {ProgramImage,SimulationConfig} from './types';
export interface Probe {instance:string;master:string;pin:string;net:string;bit:number;aliases:string[];bitId:number;connections:Record<string,(number|string)[]>}
export interface DesignMap {mappedSha256:string;core:string;timing:string;probeCount:number;probes:Probe[];ports:Record<string,{direction:string;bits:(number|string)[]}>}
export interface GateFrame {cycle:number;halted:boolean;trap:number;gpio:number;regs:number[];signals:number[];ports:Record<string,number>}
export function useGates(image:ProgramImage,config:SimulationConfig,cycle:number,enabled:boolean){const worker=useRef<Worker|null>(null);const [frame,setFrame]=useState<GateFrame|null>(null),[map,setMap]=useState<DesignMap|null>(null),[error,setError]=useState('');const target=useRef(cycle);target.current=cycle;
 useEffect(()=>{setFrame(null);setMap(null);setError('');if(!enabled||config.cache)return;let active=true;const w=new Worker(new URL('./gateWorker.ts',import.meta.url),{type:'module'});worker.current=w;w.onmessage=({data})=>{if(!active)return;if(data.type==='snapshot')setFrame(data.frame);if(data.type==='map')setMap(data.map);if(data.type==='error')setError(data.message);};w.onerror=e=>setError(e.message);w.postMessage({type:'load',image,config,cycle:target.current});return()=>{active=false;w.terminate();worker.current=null;};},[image,config,enabled]);
 useEffect(()=>{worker.current?.postMessage({type:'seek',cycle});},[cycle]);return {frame,map,error};}
export const probeValue=(frame:GateFrame|null,bit:number)=>frame?frame.signals[bit>>>5]>>>(bit&31)&1:null;
