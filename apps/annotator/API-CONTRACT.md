# Annotator integration contract

UI annotation DTO offsets are JavaScript UTF-16 code units in the full document, half-open `[start,end)`. Canonical Schema v3 record offsets remain Unicode code points within `record.sentence`; the engine validates and converts between these coordinate systems. All persistent APIs require a signed-in Sites identity and enforce project ownership. Never trust a client-supplied owner ID. JSON errors are `{error:string}` with meaningful HTTP status codes. Never silently replace a model call with demo data. The UI is Chinese.

## DTOs

- Project: `{id,name,description,createdAt,textCount?,annotationCount?}`
- Text: `{id,projectId,title,content,version,genre,context,createdAt,updatedAt}`
- FrameworkNode: `{id,label,color,children?:FrameworkNode[]}`
- Framework: `{id,name,description,version,nodes:FrameworkNode[],prompt,builtin:boolean}`
- Annotation: `{id,textId,start,end,surface,category,categoryLabel,confidence:number,rationale,congruent,evidence:string[],counterEvidence:string[],reviewStatus:'pending'|'accepted'|'rejected'|'modified',reviewNote,version,source:'demo'|'llm'|'manual',record:object,createdAt,updatedAt}`. Confidence is an uncalibrated model self-rating, not accuracy. All generated records start pending regardless of score. The original machine record is immutable; human edits update an audited review projection. `record` is a full validated Schema v3 GM record for the GM framework, or a validated generic record for custom frameworks. `category` uses a framework leaf ID.

## Routes and JSON

- GET `/api/health`: `{ok:true,modelConfigured:boolean,providers:string[],schemaVersion:'3.0'}` (no secrets)
- GET `/api/projects`: `{projects:Project[]}`
- POST `/api/projects` `{name,description?}` -> `{project:Project}`
- GET `/api/texts?projectId=...`: `{texts:Text[]}`
- POST `/api/texts` `{projectId,title,content,genre?,context?}` -> `{text:Text}`
- PATCH `/api/texts` `{id,version,title?,content?,genre?,context?}` -> `{text:Text}`; content edits create a new version and retain old annotation/version history. GET annotations returns current version only.
- GET `/api/annotations?textId=...`: `{annotations:Annotation[]}`
- PATCH `/api/annotations` `{id,version,category?,reviewNote?,congruent?,rationale?}` -> `{annotation:Annotation}`; mark modified, optimistic concurrency, validate framework category.
- GET `/api/framework_manage`: `{frameworks:Framework[]}`
- POST `/api/framework_manage` `{name,description?,nodes,prompt?}` -> `{framework:Framework}`. JSON or XML file import is parsed in the browser into this payload, size/depth/node-count limits on server. Builtins are immutable; UI edits save as a new version/custom copy.
- POST `/api/auto_tag` `{textId,frameworkId,threshold?:number,mode:'llm'|'demo',llm?:{provider:'openai'|'deepseek'|'qwen'|'anthropic',apiKey?:string,model?:string}}` -> `{annotations:Annotation[],runId,warnings:string[]}`. Demo only works for the shipped teaching text and clearly labels source demo. Provider key in React memory only; do not log or persist. Fixed provider URLs; server env fallback. Avoid duplicate concurrent runs and never overwrite accepted/manual annotations.
- GET `/api/batch_review?projectId=...&category=...&status=pending&maxConfidence=...&textId=...`: `{annotations:Annotation[]}`. Filters optional except projectId.
- POST `/api/batch_review` `{projectId,items:{id,version}[],action:'accept'|'reject'|'reopen',note?:string}` -> `{updated:number}`; atomic ownership and optimistic version checks; 409 on stale edit.
- POST `/api/demo` `{}` -> `{project:Project,text:Text,frameworkId:string}`; idempotently create a per-user example project/text with explicitly constructed teaching fixtures, not corpus evidence.
- GET `/api/export?projectId=...&format=xlsx|json&textId=...`: downloadable workbook/JSON. Workbook includes stable IDs, annotation/text versions, annotations, source texts, metadata, and review fields. Export must prevent spreadsheet formula injection. JSON is lossless.
- POST `/api/import` multipart file + projectId -> `{updated:number,conflicts:{id,reason}[]}`; parse workbook, only accept review/category/note edits from exported IDs for same owned project/current version, reject stale content/version; transaction with explicit conflict reporting. Upload cap 5 MB. 

