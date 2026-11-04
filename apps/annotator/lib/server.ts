import { env } from 'cloudflare:workers';
import { getChatGPTUser } from '@/app/chatgpt-auth';
import { createStore, StoreError } from './store';
import { analyzeText, configuredProviders, EngineError, type ModelEnv } from './llm';
import type { LlmSettings } from './types';
import { encodeWorkbook, decodeWorkbook, immutableRowConflicts, snapshotRevision } from './workbook';
export const modelEnv=()=>env as unknown as ModelEnv;
const json=(data:unknown,status=200)=>Response.json(data,{status,headers:{'Cache-Control':'no-store'}});
function id(value:unknown):string {if(typeof value!=='string'||!value||value.length>160)throw new StoreError(400,'无效的记录 ID');return value;}
export async function handleApi(request:Request):Promise<Response> {
 try {
 const url=new URL(request.url),path=url.pathname.replace(/\/$/,'');const method=request.method;
 if(path==='/api/health'&&method==='GET')return json({ok:true,modelConfigured:configuredProviders(modelEnv()).length>0,providers:configuredProviders(modelEnv()),schemaVersion:'3.0'});
 const user=await getChatGPTUser();if(!user)return json({error:'请登录后使用项目与标注功能。'},401);if(!env.DB)throw new Error('Database unavailable');
 if(method!=='GET'&&request.headers.has('origin')&&request.headers.get('origin')!==url.origin)throw new StoreError(403,'不允许跨站修改数据。');
 const store=createStore(env.DB,user.userId);const q=url.searchParams;
 let b:Record<string,unknown>={};
 if(method!=='GET'&&path!=='/api/import'){const raw=await request.text();if(raw.length>400000)throw new StoreError(413,'请求过大。');try{b=raw?JSON.parse(raw):{};}catch{throw new StoreError(400,'请求不是有效 JSON。');}if(!b||Array.isArray(b)||typeof b!=='object')throw new StoreError(400,'请求须为 JSON 对象。');}
 if(path==='/api/projects'){if(method==='GET')return json({projects:await store.listProjects()});if(method==='POST')return json({project:await store.createProject({name:b.name,description:b.description})},201);}
 if(path==='/api/texts'){if(method==='GET')return json({texts:await store.listTexts(id(q.get('projectId')))});if(method==='POST')return json({text:await store.createText({projectId:id(b.projectId),title:b.title,content:b.content,genre:b.genre,context:b.context})},201);if(method==='PATCH')return json({text:await store.updateText({id:id(b.id),version:b.version,title:b.title,content:b.content,genre:b.genre,context:b.context})});}
 if(path==='/api/annotations'){if(method==='GET')return json({annotations:await store.listAnnotations(id(q.get('textId')))});if(method==='PATCH')return json({annotation:await store.updateAnnotation({id:id(b.id),version:b.version,category:b.category,reviewNote:b.reviewNote,congruent:b.congruent,rationale:b.rationale})});}
 if(path==='/api/framework_manage'){if(method==='GET')return json({frameworks:await store.listFrameworks()});if(method==='POST')return json({framework:await store.createFramework({name:b.name,description:b.description,nodes:b.nodes,prompt:b.prompt})},201);}
 if(path==='/api/demo'&&method==='POST')return json(await store.createDemo());
 if(path==='/api/batch_review'){if(method==='GET')return json({annotations:await store.reviewQueue(id(q.get('projectId')),{category:q.get('category')||undefined,status:q.get('status')||undefined,textId:q.get('textId')||undefined,maxConfidence:q.has('maxConfidence')?Number(q.get('maxConfidence')):undefined})});if(method==='POST')return json(await store.batchReview({projectId:id(b.projectId),items:b.items as {id:string;version:number}[],action:String(b.action),note:b.note}));}
 if(path==='/api/auto_tag'&&method==='POST'){
  if(!['llm','demo'].includes(String(b.mode)))throw new StoreError(400,'请选择标注模式。');if(b.threshold!==undefined&&(!Number.isFinite(b.threshold)||Number(b.threshold)<0||Number(b.threshold)>1))throw new StoreError(400,'阈值须在 0 到 1 之间。');
  const framework=await store.getFramework(id(b.frameworkId));const settings=b.llm as LlmSettings|undefined;
  if(settings&&(!settings.provider||typeof settings.provider!=='string'||(settings.apiKey!==undefined&&(typeof settings.apiKey!=='string'||settings.apiKey.length>2048))||(settings.model!==undefined&&typeof settings.model!=='string')))throw new StoreError(400,'模型配置无效。');
  const mode=b.mode as 'llm'|'demo';const run=await store.beginRun(id(b.textId),framework,mode,settings?.provider,settings?.model);
  try {const result=await analyzeText({content:run.text.content,context:run.text.context,genre:run.text.genre,framework,mode,llm:settings},modelEnv());const annotations=await store.finishRun(run.runId,result.drafts,result.warnings);return json({annotations,runId:run.runId,warnings:result.warnings});}catch(error){await store.failRun(run.runId);throw error;}
 }
 if((path==='/api/export'&&method==='GET')||(path==='/api/import'&&method==='POST')){
  let form:FormData|undefined;
  if(path==='/api/import'){if(Number(request.headers.get('content-length')||0)>5.2*1024*1024)throw new StoreError(413,'文件不得超过 5 MB。');form=await request.formData();}
  const projectId=id(form?form.get('projectId'):q.get('projectId'));const project=await store.getProject(projectId);let texts=await store.listTexts(projectId);
  if(q.get('textId')){const textId=id(q.get('textId'));if(!texts.some(t=>t.id===textId))throw new StoreError(404,'文本不属于当前项目。');texts=texts.filter(t=>t.id===textId);}
  const annotations=(await Promise.all(texts.map(t=>store.listAnnotations(t.id)))).flat();const snapshot={project,texts,annotations};const revision=await snapshotRevision(snapshot);
  if(form){const file=form.get('file');if(!(file instanceof File)||file.size>5*1024*1024)throw new StoreError(400,'请上传 5 MB 以内的 XLSX 文件。');let imported;try{imported=await decodeWorkbook(new Uint8Array(await file.arrayBuffer()));}catch(error){throw new StoreError(400,(error as Error).message);}
   if(imported.projectId!==projectId)throw new StoreError(409,'工作簿不属于当前项目。');const conflicts=immutableRowConflicts(imported.originals,annotations);if(conflicts.length)return json({updated:0,conflicts});
   const byId=new Map(annotations.map(a=>[a.id,a]));const edits=imported.edits.filter(e=>{const a=byId.get(e.id)!;return e.category!==a.category||e.reviewStatus!==a.reviewStatus||e.reviewNote!==a.reviewNote||e.congruent!==a.congruent||e.rationale!==a.rationale;});
   return json(await store.applyReviewEdits(projectId,edits));
  }
  const headers={'Cache-Control':'no-store','X-Project-Revision':revision,'Content-Disposition':`attachment; filename="halliday-annotations.${q.get('format')==='json'?'json':'xlsx'}"`};
  if(q.get('format')==='json')return new Response(JSON.stringify({format:'halliday-lab-v1',schemaVersion:'3.0',revision,...snapshot},null,2),{headers:{...headers,'Content-Type':'application/json; charset=utf-8'}});
  if(q.get('format')!=='xlsx')throw new StoreError(400,'请选择 xlsx 或 json 导出格式。');
  let bytes:Uint8Array;try{bytes=await encodeWorkbook(snapshot);}catch(error){throw new StoreError(400,(error as Error).message);}return new Response(bytes as unknown as BodyInit,{headers:{...headers,'Content-Type':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}});
 }
 return json({error:'接口或方法不存在。'},404);
 }catch(error){if(error instanceof StoreError||error instanceof EngineError)return json({error:error.message},error.status);console.error('Annotation API internal failure',error instanceof Error ? error.name+': '+error.message : 'Unknown error');return json({error:'服务暂时无法完成操作，请稍后重试。'},500);}
}
