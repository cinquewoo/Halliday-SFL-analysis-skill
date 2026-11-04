'use client';
import { useEffect,useRef,useState } from 'react';
import {createPortal} from 'react-dom';
type Handle={getFile:()=>Promise<File>;createWritable:()=>Promise<{write:(b:Blob)=>Promise<void>;close:()=>Promise<void>}>};
export default function ExcelSync({projectId,onSynced,visible}:{projectId:string;onSynced:()=>void|Promise<void>;visible:boolean}){
 const [target,setTarget]=useState<HTMLElement|null>(null);
 useEffect(()=>setTarget(visible?document.getElementById('excel-sync-target'):null),[visible]);
 const [active,setActive]=useState(false),[message,setMessage]=useState(''),[supported,setSupported]=useState(false);const handle=useRef<Handle|null>(null),last=useRef({modified:0,revision:''}),busy=useRef(false),callback=useRef(onSynced);callback.current=onSynced;
 useEffect(()=>setSupported('showSaveFilePicker' in window),[]);
 useEffect(()=>{setActive(false);handle.current=null;last.current={modified:0,revision:''};},[projectId]);
 async function sync(initial=false){if(!handle.current||busy.current)return false;busy.current=true;try{
 const local=await handle.current.getFile();if(!initial&&local.lastModified!==last.current.modified){const form=new FormData();form.append('projectId',projectId);form.append('file',local);const r=await fetch('/api/import',{method:'POST',body:form});const data=await r.json() as {error?:string;conflicts?:unknown[]};if(!r.ok||data.conflicts?.length)throw new Error(data.error||'本地与云端存在版本冲突。请分别保留文件、重新导出并核对。');await callback.current();}
 const r=await fetch('/api/export?'+new URLSearchParams({projectId,format:'xlsx'}),{cache:'no-store'});if(!r.ok)throw new Error('同步下载失败，请检查登录状态及导出限制。');const revision=r.headers.get('X-Project-Revision')||'';
 if(initial||revision!==last.current.revision||local.lastModified!==last.current.modified){const blob=await r.blob();const latest=await handle.current.getFile();if(latest.lastModified!==local.lastModified)throw new Error('同步期间本地文件已变化，已暂停以免覆盖。');const writable=await handle.current.createWritable();await writable.write(blob);await writable.close();last.current={modified:(await handle.current.getFile()).lastModified,revision};}else await r.body?.cancel();
 setMessage('已同步 · '+new Date().toLocaleTimeString());return true;
 }catch(error){setActive(false);setMessage((error as Error).message);return false;}finally{busy.current=false;}}
 useEffect(()=>{if(!active)return;const timer=setInterval(()=>void sync(),10000);return()=>clearInterval(timer);},[active,projectId]);
 async function connect(){try{const pick=(window as unknown as {showSaveFilePicker:(options:unknown)=>Promise<Handle>}).showSaveFilePicker;handle.current=await pick({suggestedName:'halliday-live-review.xlsx',types:[{description:'Excel 工作簿',accept:{'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':['.xlsx']}}]});setMessage('首次连接将用当前云端数据建立工作簿。');const success=await sync(true);if(success)setActive(true);}catch(error){if((error as Error).name!=='AbortError')setMessage((error as Error).message);}}
 return target ? createPortal(<div style={{border:'1px solid #d8dfd6',borderRadius:10,padding:14,marginTop:14}}><strong>连接本地工作簿</strong><p style={{fontSize:12,lineHeight:1.7}}>浏览器打开期间每 10 秒双向同步审核列。请使用专用新文件；冲突会暂停同步。{!supported&&' 当前浏览器不支持文件连接，请使用导出／导入。'}</p><button type="button" className="button secondary" disabled={!projectId||!supported} onClick={()=>active?setActive(false):void connect()}>{active?'暂停同步':'选择同步文件'}</button><span role="status" style={{display:'block',fontSize:12,marginTop:8}}>{message}</span></div>,target):null;
}
