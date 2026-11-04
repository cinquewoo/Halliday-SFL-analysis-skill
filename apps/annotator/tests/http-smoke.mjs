import assert from 'node:assert/strict';
const base=process.env.TEST_BASE_URL||'http://localhost:5173';
assert.ok(new URL(base).hostname==='localhost'||new URL(base).hostname==='127.0.0.1','Run only against local preview');
let response=await fetch(base+'/api/projects');assert.equal(response.status,401);
response=await fetch(base+'/signin-with-chatgpt?return_to=/',{redirect:'manual'});
const cookie=response.headers.getSetCookie().map(s=>s.split(';')[0]).join('; ');assert.ok(cookie);
async function api(path,body,method='POST'){const r=await fetch(base+path,{method:body===undefined?'GET':method,headers:{cookie,...(body===undefined?{}:{'content-type':'application/json'})},body:body===undefined?undefined:JSON.stringify(body)});const json=await r.json();assert.ok(r.ok,`${path} ${r.status}: ${JSON.stringify(json)}`);return json;}
const demo=await api('/api/demo',{});const result=await api('/api/auto_tag',{textId:demo.text.id,frameworkId:demo.frameworkId,mode:'demo'});assert.equal(result.annotations.length,6);
const annotation=result.annotations[0];await api('/api/batch_review',{projectId:demo.project.id,items:[{id:annotation.id,version:annotation.version}],action:'accept'});
for(let repetition=0;repetition<3;repetition++){
const exportResponse=await fetch(base+'/api/export?'+new URLSearchParams({projectId:demo.project.id,format:'xlsx'}),{headers:{cookie}});assert.equal(exportResponse.status,200);const file=await exportResponse.blob();assert.ok(file.size>5000);const form=new FormData();form.append('projectId',demo.project.id);form.append('file',file,'review.xlsx');const imported=await fetch(base+'/api/import',{method:'POST',headers:{cookie},body:form});assert.equal(imported.status,200);assert.deepEqual(await imported.json(),{updated:0,conflicts:[]});
}
const rejected=await fetch(base+'/api/projects',{method:'POST',headers:{cookie,origin:'https://untrusted.invalid','content-type':'application/json'},body:JSON.stringify({name:'bad'})});assert.equal(rejected.status,403);
console.log('HTTP smoke passed: auth, D1 demo, model route, review, XLSX export/import, CSRF');
