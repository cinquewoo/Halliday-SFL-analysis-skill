import type { Annotation, AnnotationDraft, EditConflict, Framework, FrameworkNode, Project, ReviewEdit, ReviewStatus, TextDocument } from "./types";
import { BUILTIN_FRAMEWORKS, DEMO_TEXT } from "./frameworks";
import { validateRecord } from "./gm/validate";

export class StoreError extends Error {
  constructor(public status: number, message: string) { super(message); this.name = "StoreError"; }
}
type Row = Record<string, unknown>;
const now = () => new Date().toISOString();
const id = () => crypto.randomUUID();
function str(v: unknown) { return String(v ?? ""); }
function json<T>(v: unknown, fallback: T): T { try { return JSON.parse(str(v)) as T; } catch { return fallback; } }
export function boundedString(value: unknown, field: string, max: number, required = false): string {
  if (typeof value !== "string") throw new StoreError(400, `${field}必须为文本`);
  if (value.length > max || (required && !value.trim())) throw new StoreError(400, `${field}不能为空且长度不得超过 ${max} 个字符`);
  return value;
}
export function positiveVersion(value: unknown): number {
  if (!Number.isSafeInteger(value) || Number(value) < 1) throw new StoreError(400, "版本号无效，请刷新后重试");
  return Number(value);
}
function projectDto(r: Row): Project {
  return { id: str(r.id), name: str(r.name), description: str(r.description), createdAt: str(r.created_at), textCount: Number(r.text_count ?? 0), annotationCount: Number(r.annotation_count ?? 0) };
}
function textDto(r: Row): TextDocument {
  return { id: str(r.id), projectId: str(r.project_id), title: str(r.title), content: str(r.content), version: Number(r.version), genre: str(r.genre), context: str(r.context), createdAt: str(r.created_at), updatedAt: str(r.updated_at) };
}
function frameworkDto(r: Row): Framework {
  return { id: str(r.id), name: str(r.name), description: str(r.description), version: Number(r.version), nodes: json(r.nodes_json, []), prompt: str(r.prompt), builtin: false };
}
function annotationDto(r: Row): Annotation {
  return { id: str(r.id), textId: str(r.text_id), textVersion: Number(r.text_version), frameworkId: str(r.framework_id), frameworkVersion: Number(r.framework_version), runId: str(r.run_id), start: Number(r.start_offset), end: Number(r.end_offset), surface: str(r.surface), category: str(r.category), originalCategory: str(r.original_category), categoryLabel: str(r.category_label), confidence: Number(r.confidence_milli) / 1000, rationale: str(r.rationale), congruent: str(r.congruent), evidence: json(r.evidence_json, []), counterEvidence: json(r.counter_evidence_json, []), reviewStatus: str(r.review_status) as ReviewStatus, reviewNote: str(r.review_note), version: Number(r.version), source: str(r.source) as Annotation["source"], record: json(r.record_json, {}), createdAt: str(r.created_at), updatedAt: str(r.updated_at) };
}
export function leafNodes(nodes: FrameworkNode[]): FrameworkNode[] {
  return nodes.flatMap(node => node.children?.length ? leafNodes(node.children) : [node]);
}
export function validateFrameworkNodes(value: unknown): FrameworkNode[] {
  let count = 0;
  const ids = new Set<string>();
  function walk(nodes: unknown, depth: number): FrameworkNode[] {
    if (!Array.isArray(nodes) || !nodes.length || depth > 8) throw new StoreError(400, "框架须包含节点，最多 8 层");
    return nodes.map((raw: unknown) => {
      if (!raw || typeof raw !== "object") throw new StoreError(400, "框架节点无效");
      const n = raw as Record<string, unknown>;
      if (++count > 200) throw new StoreError(400, "框架最多 200 个节点");
      const nodeId = boundedString(n.id, "节点ID", 80, true);
      if (!/^[\w-]+$/.test(nodeId) || ids.has(nodeId)) throw new StoreError(400, "节点ID须唯一且只含字母、数字、下划线或连字符");
      ids.add(nodeId);
      const color = boundedString(n.color ?? "#236a62", "节点颜色", 7);
      if (!/^#[\da-f]{6}$/i.test(color)) throw new StoreError(400, "节点颜色须为六位十六进制颜色");
      const node: FrameworkNode = { id: nodeId, label: boundedString(n.label, "节点名称", 100, true), color };
      if (n.children !== undefined && !Array.isArray(n.children)) throw new StoreError(400, "子节点须为数组");
      if (Array.isArray(n.children) && n.children.length) node.children = walk(n.children, depth + 1);
      return node;
    });
  }
  return walk(value, 1);
}

export function createStore(db: D1Database, userId: string) {
  if (!userId) throw new StoreError(401, "请先登录");
  const stmt = (sql: string, values: unknown[] = []) => db.prepare(sql).bind(...values);
  const all = async (sql: string, values: unknown[] = []) => (await stmt(sql, values).all<Row>()).results;
  const one = (sql: string, values: unknown[] = []) => stmt(sql, values).first<Row>();
  const guardExists = "EXISTS (SELECT 1 FROM mutation_guards WHERE id = ?)";
  async function guarded(condition: string, values: unknown[], build: (guardId: string) => D1PreparedStatement[], message = "数据已更新，请刷新后重试") {
    const guardId = id();
    const results = await db.batch([
      stmt(`INSERT INTO mutation_guards (id,created_at) SELECT ?,? WHERE ${condition}`, [guardId, now(), ...values]),
      ...build(guardId),
      stmt("DELETE FROM mutation_guards WHERE id = ?", [guardId]),
    ]);
    if (results[0].meta.changes !== 1) throw new StoreError(409, message);
    return results;
  }
  async function getProject(projectId: string): Promise<Project> {
    const row = await one("SELECT * FROM projects WHERE id = ? AND owner_id = ?", [projectId, userId]);
    if (!row) throw new StoreError(404, "项目不存在或无权访问");
    return projectDto(row);
  }
  async function getText(textId: string): Promise<TextDocument> {
    const row = await one("SELECT t.* FROM texts t JOIN projects p ON p.id=t.project_id WHERE t.id=? AND p.owner_id=?", [textId, userId]);
    if (!row) throw new StoreError(404, "文本不存在或无权访问");
    return textDto(row);
  }
  async function getAnnotation(annotationId: string): Promise<Annotation> {
    const row = await one("SELECT a.* FROM annotations a JOIN texts t ON t.id=a.text_id JOIN projects p ON p.id=t.project_id WHERE a.id=? AND p.owner_id=?", [annotationId, userId]);
    if (!row) throw new StoreError(404, "标注不存在或无权访问");
    return annotationDto(row);
  }
  async function getFramework(frameworkId: string): Promise<Framework> {
    const builtin = BUILTIN_FRAMEWORKS.find(f => f.id === frameworkId);
    if (builtin) return structuredClone(builtin);
    const row = await one("SELECT * FROM frameworks WHERE id=? AND owner_id=?", [frameworkId, userId]);
    if (!row) throw new StoreError(404, "框架不存在或无权访问");
    return frameworkDto(row);
  }
  async function listAnnotations(textId: string): Promise<Annotation[]> {
    await getText(textId);
    return (await all("SELECT a.* FROM annotations a JOIN texts t ON t.id=a.text_id JOIN projects p ON p.id=t.project_id WHERE a.text_id=? AND a.text_version=t.version AND p.owner_id=? ORDER BY a.start_offset,a.end_offset,a.created_at", [textId, userId])).map(annotationDto);
  }
  async function listTexts(projectId: string): Promise<TextDocument[]> {
    await getProject(projectId);
    return (await all("SELECT t.* FROM texts t JOIN projects p ON p.id=t.project_id WHERE p.id=? AND p.owner_id=? ORDER BY t.created_at,t.id", [projectId, userId])).map(textDto);
  }
  async function listProjects(): Promise<Project[]> {
    return (await all(`SELECT p.*, (SELECT COUNT(*) FROM texts t WHERE t.project_id=p.id) text_count,
      (SELECT COUNT(*) FROM annotations a JOIN texts t ON t.id=a.text_id AND t.version=a.text_version WHERE t.project_id=p.id) annotation_count
      FROM projects p WHERE p.owner_id=? ORDER BY p.created_at DESC,p.id`, [userId])).map(projectDto);
  }
  async function createProject(input: { name: unknown; description?: unknown }): Promise<Project> {
    const name = boundedString(input.name, "项目名称", 120, true);
    const description = boundedString(input.description ?? "", "项目说明", 4000);
    const projectId = id();
    await stmt("INSERT INTO projects(id,owner_id,name,description,created_at) VALUES(?,?,?,?,?)", [projectId, userId, name, description, now()]).run();
    return getProject(projectId);
  }
  async function createText(input: { projectId: string; title: unknown; content: unknown; genre?: unknown; context?: unknown }): Promise<TextDocument> {
    await getProject(input.projectId);
    const title = boundedString(input.title, "文本标题", 200, true);
    const content = boundedString(input.content, "原文", 100_000, true);
    const genre = boundedString(input.genre ?? "", "语类", 200);
    const context = boundedString(input.context ?? "", "语境说明", 12_000);
    const textId = id();
    const date = now();
    await guarded("EXISTS(SELECT 1 FROM projects WHERE id=? AND owner_id=?)", [input.projectId, userId], guardId => [
      stmt(`INSERT INTO texts(id,project_id,title,content,version,genre,context,created_at,updated_at) SELECT ?,?,?,?,1,?,?,?,? WHERE ${guardExists}`, [textId,input.projectId,title,content,genre,context,date,date,guardId]),
      stmt(`INSERT INTO text_versions(id,text_id,version,title,content,genre,context,created_at) SELECT ?,?,1,?,?,?,?,? WHERE ${guardExists}`, [id(),textId,title,content,genre,context,date,guardId]),
    ]);
    return getText(textId);
  }
  async function updateText(input: { id: string; version: unknown; title?: unknown; content?: unknown; genre?: unknown; context?: unknown }): Promise<TextDocument> {
    const current = await getText(input.id);
    const version = positiveVersion(input.version);
    if (current.version !== version) throw new StoreError(409, "原文已更新，请刷新后编辑");
    const title = boundedString(input.title ?? current.title, "文本标题", 200, true);
    const content = boundedString(input.content ?? current.content, "原文", 100_000, true);
    const genre = boundedString(input.genre ?? current.genre, "语类", 200);
    const context = boundedString(input.context ?? current.context, "语境说明", 12_000);
    if (title === current.title && content === current.content && genre === current.genre && context === current.context) return current;
    const date = now();
    await guarded("EXISTS(SELECT 1 FROM texts t JOIN projects p ON p.id=t.project_id WHERE t.id=? AND t.version=? AND p.owner_id=?)", [input.id,version,userId], guardId => [
      stmt(`UPDATE texts SET title=?,content=?,genre=?,context=?,version=version+1,updated_at=? WHERE id=? AND ${guardExists}`, [title,content,genre,context,date,input.id,guardId]),
      stmt(`INSERT INTO text_versions(id,text_id,version,title,content,genre,context,created_at) SELECT ?,?,?,?,?,?,?,? WHERE ${guardExists}`, [id(),input.id,version+1,title,content,genre,context,date,guardId]),
      stmt(`UPDATE annotation_runs SET status='stale',finished_at=? WHERE text_id=? AND status='running' AND ${guardExists}`, [date,input.id,guardId]),
    ]);
    return getText(input.id);
  }
  async function listFrameworks(): Promise<Framework[]> {
    const rows = await all("SELECT * FROM frameworks WHERE owner_id=? ORDER BY created_at DESC,id", [userId]);
    return [...structuredClone(BUILTIN_FRAMEWORKS), ...rows.map(frameworkDto)];
  }
  async function createFramework(input: { name: unknown; description?: unknown; nodes: unknown; prompt?: unknown }): Promise<Framework> {
    const name = boundedString(input.name, "框架名称", 120, true);
    const description = boundedString(input.description ?? "", "框架说明", 4000);
    const nodes = validateFrameworkNodes(input.nodes);
    const prompt = boundedString(input.prompt ?? "", "框架提示词", 20_000);
    const frameworkId = id();
    // A new immutable snapshot gets its own ID. Version records lineage by name.
    const prior = await one("SELECT MAX(version) v FROM frameworks WHERE owner_id=? AND name=?", [userId,name]);
    const version = Number(prior?.v ?? 0) + 1;
    await stmt("INSERT INTO frameworks(id,owner_id,name,description,version,nodes_json,prompt,created_at) VALUES(?,?,?,?,?,?,?,?)", [frameworkId,userId,name,description,version,JSON.stringify(nodes),prompt,now()]).run();
    return getFramework(frameworkId);
  }
  async function reviewQueue(projectId: string, filters: { category?: string; status?: string; maxConfidence?: number; textId?: string } = {}): Promise<Annotation[]> {
    await getProject(projectId);
    let sql = "SELECT a.* FROM annotations a JOIN texts t ON t.id=a.text_id AND a.text_version=t.version JOIN projects p ON p.id=t.project_id WHERE p.id=? AND p.owner_id=?";
    const values: unknown[] = [projectId,userId];
    if (filters.category) { sql += " AND a.category=?"; values.push(filters.category); }
    if (filters.status) { if (!["pending","accepted","rejected","modified"].includes(filters.status)) throw new StoreError(400,"审核状态无效"); sql += " AND a.review_status=?"; values.push(filters.status); }
    if (filters.maxConfidence !== undefined) { if (!Number.isFinite(filters.maxConfidence) || filters.maxConfidence < 0 || filters.maxConfidence > 1) throw new StoreError(400,"置信度须在 0 到 1 之间"); sql += " AND a.confidence_milli <= ?"; values.push(Math.round(filters.maxConfidence*1000)); }
    if (filters.textId) { sql += " AND t.id=?"; values.push(filters.textId); }
    sql += " ORDER BY a.confidence_milli,a.start_offset,a.id LIMIT 1000";
    return (await all(sql,values)).map(annotationDto);
  }
  async function applyReviewEdits(projectId: string, edits: ReviewEdit[]): Promise<{updated:number;conflicts:EditConflict[]}> {
    await getProject(projectId);
    if (!Array.isArray(edits) || edits.length > 250) throw new StoreError(400,"一次最多审核 250 条标注");
    if (!edits.length) return {updated:0,conflicts:[]};
    const conflicts: EditConflict[] = [];
    const current: Annotation[] = [];
    const seen = new Set<string>();
    const labels = new Map<string,Map<string,string>>();
    for (const edit of edits) {
      if (!edit || typeof edit !== "object" || typeof edit.id !== "string" || seen.has(edit.id)) { conflicts.push({id:edit?.id ?? "",reason:"重复或无效的标注ID"}); continue; }
      seen.add(edit.id);
      let a: Annotation;
      try { a = await getAnnotation(edit.id); } catch { conflicts.push({id:edit.id,reason:"标注不存在或不属于当前用户"}); continue; }
      const t = await getText(a.textId);
      if (t.projectId !== projectId) { conflicts.push({id:edit.id,reason:"标注不属于所选项目"}); continue; }
      if (a.version !== edit.version || a.textVersion !== edit.textVersion || t.version !== edit.textVersion) { conflicts.push({id:edit.id,reason:"原文或标注版本已变化，请重新导出或刷新"}); continue; }
      if (!["pending","accepted","rejected","modified"].includes(edit.reviewStatus)) { conflicts.push({id:edit.id,reason:"审核状态无效"}); continue; }
      if (!labels.has(a.frameworkId)) labels.set(a.frameworkId,new Map(leafNodes((await getFramework(a.frameworkId)).nodes).map(n => [n.id,n.label])));
      if (!labels.get(a.frameworkId)!.has(edit.category)) { conflicts.push({id:edit.id,reason:"类别不是此标注框架的叶节点"}); continue; }
      try {
        boundedString(edit.reviewNote,"审核备注",4000);
        if (edit.congruent !== undefined) boundedString(edit.congruent,"一致式改写",4000);
        if (edit.rationale !== undefined) boundedString(edit.rationale,"判定依据",8000);
      } catch (e) { conflicts.push({id:edit.id,reason:(e as Error).message}); continue; }
      current.push(a);
    }
    if (conflicts.length) return {updated:0,conflicts};
    const data = JSON.stringify(edits.map(e => ({id:e.id,version:e.version,textVersion:e.textVersion})));
    const date = now();
    try {
      await guarded(`(SELECT COUNT(*) FROM json_each(?) e JOIN annotations a ON a.id=json_extract(e.value,'$.id') JOIN texts t ON t.id=a.text_id JOIN projects p ON p.id=t.project_id WHERE a.version=json_extract(e.value,'$.version') AND a.text_version=json_extract(e.value,'$.textVersion') AND t.version=a.text_version AND p.id=? AND p.owner_id=?) = ?`, [data,projectId,userId,edits.length], guardId => edits.flatMap((edit,i) => {
        const a = current[i];
        const categoryLabel = labels.get(a.frameworkId)!.get(edit.category)!;
        return [
          stmt(`INSERT INTO annotation_history(id,annotation_id,version,actor_id,snapshot_json,created_at) SELECT ?,?,?,?,?,? WHERE ${guardExists}`, [id(),a.id,a.version,userId,JSON.stringify(a),date,guardId]),
          stmt(`UPDATE annotations SET category=?,category_label=?,review_status=?,review_note=?,congruent=?,rationale=?,version=version+1,updated_at=? WHERE id=? AND ${guardExists}`, [edit.category,categoryLabel,edit.reviewStatus,edit.reviewNote,edit.congruent ?? a.congruent,edit.rationale ?? a.rationale,date,a.id,guardId]),
        ];
      }));
    } catch (e) {
      if (e instanceof StoreError && e.status===409) return {updated:0,conflicts:edits.map(edit=>({id:edit.id,reason:"保存期间版本已变化，请刷新后重试"}))};
      throw e;
    }
    return {updated:edits.length,conflicts:[]};
  }
  async function updateAnnotation(input: {id:string;version:unknown;category?:unknown;reviewNote?:unknown;congruent?:unknown;rationale?:unknown}):Promise<Annotation> {
    const a = await getAnnotation(input.id);
    const t = await getText(a.textId);
    const result = await applyReviewEdits(t.projectId,[{id:a.id,version:positiveVersion(input.version),textVersion:a.textVersion,category:input.category === undefined ? a.category : boundedString(input.category,"类别",80,true),reviewStatus:"modified",reviewNote:boundedString(input.reviewNote ?? a.reviewNote,"审核备注",4000),congruent:input.congruent === undefined ? undefined : boundedString(input.congruent,"一致式改写",4000),rationale:input.rationale === undefined ? undefined : boundedString(input.rationale,"判定依据",8000)}]);
    if (result.conflicts.length) throw new StoreError(409,result.conflicts[0].reason);
    return getAnnotation(a.id);
  }
  async function batchReview(input: { projectId:string; items:{id:string;version:number}[]; action:string; note?:unknown }):Promise<{updated:number}> {
    await getProject(input.projectId);
    if (!Array.isArray(input.items) || input.items.length > 250 || !input.items.length) throw new StoreError(400,"请选择 1 到 250 条标注");
    const status: Record<string,ReviewStatus> = {accept:"accepted",reject:"rejected",reopen:"pending"};
    if (!status[input.action]) throw new StoreError(400,"审核操作无效");
    const edits: ReviewEdit[] = [];
    for (const item of input.items) {
      if (!item || typeof item.id!=="string") throw new StoreError(400,"标注ID无效");
      const a=await getAnnotation(item.id);
      edits.push({id:a.id,version:positiveVersion(item.version),textVersion:a.textVersion,category:a.category,reviewStatus:status[input.action],reviewNote:boundedString(input.note ?? a.reviewNote,"审核备注",4000)});
    }
    const result=await applyReviewEdits(input.projectId,edits);
    if(result.conflicts.length) throw new StoreError(409,result.conflicts.map(c=>c.reason).join("；"));
    return {updated:result.updated};
  }
  async function beginRun(textId:string,framework:Framework,mode:"llm"|"demo",provider?:string,model?:string) {
    const t = await getText(textId);
    const runId = id();
    const date = now();
    const staleBefore = new Date(Date.now()-180_000).toISOString();
    await guarded(`EXISTS(SELECT 1 FROM texts t JOIN projects p ON p.id=t.project_id WHERE t.id=? AND t.version=? AND p.owner_id=?) AND NOT EXISTS(SELECT 1 FROM annotation_runs WHERE text_id=? AND text_version=? AND status='running' AND created_at>?)`, [textId,t.version,userId,textId,t.version,staleBefore], guardId => [
      stmt(`UPDATE annotation_runs SET status='expired',finished_at=? WHERE text_id=? AND status='running' AND created_at<=? AND ${guardExists}`, [date,textId,staleBefore,guardId]),
      stmt(`INSERT INTO annotation_runs(id,text_id,text_version,framework_id,framework_version,mode,status,provider,model,warnings_json,created_at) SELECT ?,?,?,?,?,?,'running',?,?,'[]',? WHERE ${guardExists}`, [runId,textId,t.version,framework.id,framework.version,mode,provider ?? null,model ?? null,date,guardId]),
    ],"文本已更新或已有标注任务正在运行，请稍后重试");
    return {runId,text:t};
  }
  async function failRun(runId:string) {
    await stmt("UPDATE annotation_runs SET status='failed',finished_at=? WHERE id=? AND status='running' AND text_id IN (SELECT t.id FROM texts t JOIN projects p ON p.id=t.project_id WHERE p.owner_id=?)",[now(),runId,userId]).run();
  }
  async function finishRun(runId:string,drafts:AnnotationDraft[],warnings:string[]):Promise<Annotation[]> {
    const run = await one("SELECT r.* FROM annotation_runs r JOIN texts t ON t.id=r.text_id JOIN projects p ON p.id=t.project_id WHERE r.id=? AND p.owner_id=?",[runId,userId]);
    if(!run) throw new StoreError(404,"任务不存在");
    const t=await getText(str(run.text_id));
    const framework=await getFramework(str(run.framework_id));
    const leaves = new Map(leafNodes(framework.nodes).map(n=>[n.id,n]));
    if(!Array.isArray(drafts) || drafts.length>250) throw new StoreError(502,"模型输出过多标注，请缩短文本后重试");
    for(const d of drafts) {
      if(!Number.isInteger(d.start)||!Number.isInteger(d.end)||d.start<0||d.end<=d.start||d.end>t.content.length||t.content.slice(d.start,d.end)!==d.surface) throw new StoreError(502,"模型输出位置与原文不匹配，未保存任何标注");
      if(!leaves.has(d.category)||!Number.isFinite(d.confidence)||d.confidence<0||d.confidence>1) throw new StoreError(502,"模型输出类别或评分无效");
      if(d.source!==(str(run.mode)==="demo"?"demo":"llm")) throw new StoreError(502,"模型输出来源无效");
      if(framework.id==="halliday-gm-v3") {
        const errors=validateRecord(d.record);
        if(errors.length) throw new StoreError(502,`Schema v3 校验未通过：${errors.slice(0,2).join("；")}`);
      }
    }
    const date=now();
    await guarded(`EXISTS(SELECT 1 FROM annotation_runs r JOIN texts t ON t.id=r.text_id JOIN projects p ON p.id=t.project_id WHERE r.id=? AND r.status='running' AND r.text_version=t.version AND p.owner_id=?)`,[runId,userId], guardId => [
      ...drafts.map(d=>stmt(`INSERT INTO annotations(id,text_id,text_version,framework_id,framework_version,run_id,start_offset,end_offset,surface,category,original_category,category_label,confidence_milli,rationale,congruent,evidence_json,counter_evidence_json,review_status,review_note,version,source,record_json,created_at,updated_at)
        SELECT ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'pending','',1,?,?,?,? WHERE ${guardExists}
        AND NOT EXISTS(SELECT 1 FROM annotations a WHERE a.text_id=? AND a.text_version=? AND a.framework_id=? AND a.start_offset=? AND a.end_offset=? AND a.original_category=?)`,
        [id(),t.id,t.version,framework.id,framework.version,runId,d.start,d.end,d.surface,d.category,d.category,leaves.get(d.category)!.label,Math.round(d.confidence*1000),d.rationale,d.congruent,JSON.stringify(d.evidence),JSON.stringify(d.counterEvidence),d.source,JSON.stringify(d.record),date,date,guardId,t.id,t.version,framework.id,d.start,d.end,d.category])),
      stmt(`UPDATE annotation_runs SET status='completed',finished_at=?,warnings_json=? WHERE id=? AND ${guardExists}`,[date,JSON.stringify(warnings),runId,guardId]),
    ],"任务期间原文发生变化或任务已失效，未写入标注");
    return listAnnotations(t.id);
  }
  async function createDemo():Promise<{project:Project;text:TextDocument;frameworkId:string}> {
    const projectId=`demo-${await ownerHash(userId)}`;
    const textId=`${projectId}-text`;
    const date=now();
    const demoContent=typeof DEMO_TEXT === "string" ? DEMO_TEXT : String((DEMO_TEXT as {content:string}).content);
    await db.batch([
      stmt("INSERT OR IGNORE INTO projects(id,owner_id,name,description,demo_key,created_at) VALUES(?,?,?,?,?,?)",[projectId,userId,"语法隐喻 · 教学示例","人工构造的教学文本与演示标注，不是语料库证据。","gm-v3-demo",date]),
      stmt("INSERT OR IGNORE INTO texts(id,project_id,title,content,version,genre,context,created_at,updated_at) VALUES(?,?,?,?,1,?,?,?,?)",[textId,projectId,"学术表达中的意义重构",demoContent,"教学示例","这是人工构造的说明性短文，用于演示标注与审核。分析结果不是实证语料，不可当作已核实的理论证据。",date,date]),
      stmt("INSERT OR IGNORE INTO text_versions(id,text_id,version,title,content,genre,context,created_at) SELECT ?,id,version,title,content,genre,context,created_at FROM texts WHERE id=? AND project_id=?",[`${textId}-v1`,textId,projectId]),
    ]);
    return {project:await getProject(projectId),text:await getText(textId),frameworkId:"halliday-gm-v3"};
  }
  async function listTextVersions(textId:string) {
    await getText(textId);
    return all("SELECT * FROM text_versions WHERE text_id=? ORDER BY version",[textId]);
  }
  async function listAnnotationHistory(annotationId:string) {
    await getAnnotation(annotationId);
    return (await all("SELECT * FROM annotation_history WHERE annotation_id=? ORDER BY created_at,id",[annotationId])).map(r=>({id:str(r.id),annotationId:str(r.annotation_id),version:Number(r.version),actorId:str(r.actor_id),snapshot:json(r.snapshot_json,{}),createdAt:str(r.created_at)}));
  }
  return {getProject,listProjects,createProject,getText,listTexts,createText,updateText,getFramework,listFrameworks,createFramework,getAnnotation,listAnnotations,updateAnnotation,reviewQueue,batchReview,applyReviewEdits,beginRun,finishRun,failRun,createDemo,listTextVersions,listAnnotationHistory};
}
export type Store = ReturnType<typeof createStore>;
async function ownerHash(owner:string):Promise<string> {
  const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(owner));
  return [...new Uint8Array(digest)].slice(0,16).map(b=>b.toString(16).padStart(2,"0")).join("");
}
