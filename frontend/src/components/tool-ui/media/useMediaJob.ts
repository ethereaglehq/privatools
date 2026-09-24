import { useCallback, useEffect, useRef, useState } from 'react';
import { downloadBlob, uploadFile, postFormData } from '@/lib/api';
import { emitToolRun } from '@/lib/toolRun';
import { friendlyError } from '@/lib/utils';
export function useMediaJob() {
 const [status,setStatus]=useState<'idle'|'processing'|'done'>('idle');const [error,setError]=useState<string|null>(null);const [result,setResult]=useState<{blob:Blob;name:string}|null>(null);const controller=useRef<AbortController|null>(null);
 useEffect(()=>()=>controller.current?.abort(),[]);
 const run=useCallback(async({endpoint,file,files,params={},name,extra}:{endpoint:string;file?:File;files?:File[];params?:Record<string,string|number|boolean>;name:string;extra?:Record<string,File>})=>{
  if(controller.current)return;const abort=new AbortController();controller.current=abort;setStatus('processing');setError(null);
  try{const res=files||extra?await postFormData(endpoint,()=>{const data=new FormData();if(file)data.append('file',file);files?.forEach(f=>data.append('files',f));Object.entries(extra||{}).forEach(([key,f])=>data.append(key,f));Object.entries(params).forEach(([key,value])=>data.append(key,String(value)));return data;},{signal:abort.signal}):await uploadFile(endpoint,file!,params,{signal:abort.signal});const blob=await res.blob();if(abort.signal.aborted)return;setResult({blob,name});setStatus('done');downloadBlob(blob,name);emitToolRun({outcome:'success',files:files?files.length:1});}catch(e){if(abort.signal.aborted){setStatus('idle');return;}const message=e instanceof Error?e.message:'Processing failed';setError(message.includes('Subtitle rendering')&&message.includes('unavailable')?'Subtitle rendering is unavailable on this server. Your files have been kept here so you can try again when it is available.':friendlyError(message,'We could not process that file. Check the settings and try again.'));setStatus('idle');emitToolRun({outcome:'error',files:files?files.length:1},e);}finally{if(controller.current===abort)controller.current=null;}
 },[]);
 const cancel=()=>{controller.current?.abort();setStatus('idle');};
 const reset=()=>{if(controller.current)return;setStatus('idle');setResult(null);setError(null);};
 return {status,error,result,run,cancel,reset,busy:status==='processing'};
}
