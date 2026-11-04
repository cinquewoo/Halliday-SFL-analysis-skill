"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDownToLine, ArrowRight, BookOpen, Check, CheckCheck, ChevronDown, ChevronRight,
  CircleHelp, ClipboardCheck, FilePlus2, FileText, FlaskConical, FolderClosed, FolderPlus,
  GitBranch, LayoutPanelLeft, LoaderCircle, Menu, MoreHorizontal, PanelRightClose,
  PencilLine, Play, Plus, RotateCcw, Search, Settings2, ShieldCheck, SlidersHorizontal,
  Sparkles, Upload, X, AlertCircle, Download, Info, Link2, FileSpreadsheet,
} from "lucide-react";
import type { Annotation, Framework, Health, Project, Provider, SourceText } from "./types";
import { api, ApiError, categoryColor, flattenNodes, leafNodes, STATUS_LABELS } from "./types";
import { HighlightText } from "./highlight-text";
import FrameworkEditor from "./framework-editor";
import ExcelSync from "@/components/ExcelSync";

type Notice = { kind: "success" | "error" | "info"; message: string };
type Tab = "details" | "review" | "framework";
type ModalName = "project" | "text" | "model" | "export" | "guide" | null;
type EditorDraft = { title: string; content: string; genre: string; context: string; id?: string; version?: number };
const EMPTY_EDITOR: EditorDraft = { title: "", content: "", genre: "", context: "" };
const PROVIDERS: { id: Provider; name: string; model: string }[] = [
  { id: "openai", name: "OpenAI", model: "例如 gpt-4.1" }, { id: "deepseek", name: "DeepSeek", model: "例如 deepseek-chat" },
  { id: "qwen", name: "通义千问", model: "例如 qwen-plus" }, { id: "anthropic", name: "Anthropic Claude", model: "填写可用的 Claude 模型 ID" },
];

function Modal({ title, subtitle, children, onClose, wide = false }: { title: string; subtitle?: string; children: React.ReactNode; onClose: () => void; wide?: boolean }) {
  const panel = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const elements = () => Array.from(panel.current?.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),textarea:not(:disabled),select:not(:disabled),a[href]') ?? []);
    elements()[0]?.focus();
    function keyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab") {
        const controls = elements(); const first = controls[0]; const last = controls.at(-1);
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    }
    document.addEventListener("keydown", keyDown);
    return () => { document.removeEventListener("keydown", keyDown); previous?.focus(); };
  }, [onClose]);
  return <div className="modal-backdrop" onMouseDown={event => { if (event.target === event.currentTarget) onClose(); }}>
    <div className={`modal ${wide ? "wide" : ""}`} ref={panel} role="dialog" aria-modal="true" aria-labelledby="modal-title">
      <div className="modal-heading"><div><span className="eyebrow">HALLIDAY LAB / WORKSPACE</span><h2 id="modal-title">{title}</h2>{subtitle && <p>{subtitle}</p>}</div><button className="icon-button" aria-label="关闭弹窗" onClick={onClose}><X size={19} /></button></div>
      {children}
    </div>
  </div>;
}

export default function Workspace() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState("");
  const [texts, setTexts] = useState<SourceText[]>([]);
  const [textId, setTextId] = useState("");
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [frameworks, setFrameworks] = useState<Framework[]>([]);
  const [frameworkId, setFrameworkId] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [tab, setTab] = useState<Tab>("details");
  const [modal, setModal] = useState<ModalName>(null);
  const [busy, setBusy] = useState("");
  const [initializing, setInitializing] = useState(true);
  const [loadingText, setLoadingText] = useState(false);
  const [needSignIn, setNeedSignIn] = useState(false);
  const [notice, setNotice] = useState<Notice | null>(null);
  const [projectQuery, setProjectQuery] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [editor, setEditor] = useState<EditorDraft>(EMPTY_EDITOR);
  const [provider, setProvider] = useState<Provider>("openai");
  const [model, setModel] = useState("");
  // Secrets live in component memory only. Never persist in web storage, URLs or logs.
  const [apiKey, setApiKey] = useState("");
  const [threshold, setThreshold] = useState(0.8);
  const [mode, setMode] = useState<"llm" | "demo">("llm");
  const [mobileView, setMobileView] = useState<"projects" | "text" | "panel">("text");
  const [showHighlight, setShowHighlight] = useState(true);
  const [reviewItems, setReviewItems] = useState<Annotation[]>([]);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewStatus, setReviewStatus] = useState("pending");
  const [reviewCategory, setReviewCategory] = useState("");
  const [reviewLowOnly, setReviewLowOnly] = useState(false);
  const [reviewScope, setReviewScope] = useState<"text" | "project">("text");
  const [checkedIds, setCheckedIds] = useState<string[]>([]);
  const [reviewNote, setReviewNote] = useState("");
  const [refreshTick, setRefreshTick] = useState(0);
  const [detailDraft, setDetailDraft] = useState({ category: "", congruent: "", rationale: "", reviewNote: "" });
  const [detailEditing, setDetailEditing] = useState(false);
  const [importConflicts, setImportConflicts] = useState<{ id: string; reason: string }[]>([]);
  const fileInput = useRef<HTMLInputElement>(null);
  const excelInput = useRef<HTMLInputElement>(null);
  const preferredText = useRef("");
  const preferredAnnotation = useRef("");

  const project = projects.find(item => item.id === projectId);
  const text = texts.find(item => item.id === textId);
  const framework = frameworks.find(item => item.id === frameworkId);
  const selected = annotations.find(item => item.id === selectedId);
  const leaves = useMemo(() => leafNodes(framework?.nodes ?? []), [framework]);
  const counters = useMemo(() => ({
    total: annotations.length,
    pending: annotations.filter(item => item.reviewStatus === "pending" || item.reviewStatus === "modified").length,
    accepted: annotations.filter(item => item.reviewStatus === "accepted").length,
    low: annotations.filter(item => item.confidence < threshold && item.reviewStatus !== "rejected").length,
  }), [annotations, threshold]);

  function fail(error: unknown) {
    if (error instanceof ApiError && error.status === 401) setNeedSignIn(true);
    setNotice({ kind: "error", message: error instanceof Error ? error.message : "操作未完成，请重试。" });
  }

  async function initialize() {
    setInitializing(true);
    try {
      const [projectResult, frameworkResult, healthResult] = await Promise.all([
        api<{ projects: Project[] }>("/api/projects"), api<{ frameworks: Framework[] }>("/api/framework_manage"), api<Health>("/api/health"),
      ]);
      setProjects(projectResult.projects); setFrameworks(frameworkResult.frameworks); setHealth(healthResult);
      setProjectId(current => projectResult.projects.some(item => item.id === current) ? current : projectResult.projects[0]?.id ?? "");
      setFrameworkId(current => frameworkResult.frameworks.some(item => item.id === current) ? current : frameworkResult.frameworks[0]?.id ?? "");
      setNeedSignIn(false);
    } catch (error) { fail(error); }
    finally { setInitializing(false); }
  }
  useEffect(() => { void initialize(); }, []);

  useEffect(() => {
    if (!projectId) { setTexts([]); setTextId(""); setAnnotations([]); return; }
    let current = true; setLoadingText(true); setTexts([]); setTextId(""); setAnnotations([]); setCheckedIds([]);
    api<{ texts: SourceText[] }>(`/api/texts?projectId=${encodeURIComponent(projectId)}`).then(result => {
      if (!current) return;
      setTexts(result.texts);
      const desired = preferredText.current;
      setTextId(result.texts.some(item => item.id === desired) ? desired : result.texts[0]?.id ?? "");
      preferredText.current = "";
    }).catch(error => { if (current) fail(error); }).finally(() => { if (current) setLoadingText(false); });
    return () => { current = false; };
  }, [projectId]);

  useEffect(() => {
    setAnnotations([]); setSelectedId(""); setCheckedIds([]); setDetailEditing(false);
    if (!textId) return;
    let current = true; setLoadingText(true);
    api<{ annotations: Annotation[] }>(`/api/annotations?textId=${encodeURIComponent(textId)}`).then(result => {
      if (!current) return;
      setAnnotations(result.annotations);
      const desired = preferredAnnotation.current;
      setSelectedId(result.annotations.some(item => item.id === desired) ? desired : result.annotations[0]?.id ?? "");
      preferredAnnotation.current = "";
    }).catch(error => { if (current) fail(error); }).finally(() => { if (current) setLoadingText(false); });
    return () => { current = false; };
  }, [textId]);

  async function refreshAnnotations() {
    if (!textId) return;
    const result = await api<{ annotations: Annotation[] }>(`/api/annotations?textId=${encodeURIComponent(textId)}`);
    setAnnotations(result.annotations);
    setSelectedId(current => result.annotations.some(item => item.id === current) ? current : result.annotations[0]?.id ?? "");
    setRefreshTick(tick => tick + 1);
  }

  useEffect(() => {
    if (tab !== "review" || !projectId) return;
    let current = true; setReviewLoading(true); setCheckedIds([]);
    const query = new URLSearchParams({ projectId });
    if (reviewStatus) query.set("status", reviewStatus);
    if (reviewCategory) query.set("category", reviewCategory);
    if (reviewLowOnly) query.set("maxConfidence", String(threshold));
    if (reviewScope === "text") {
      if (!textId) { setReviewItems([]); setReviewLoading(false); return; }
      query.set("textId", textId);
    }
    api<{ annotations: Annotation[] }>(`/api/batch_review?${query}`).then(result => { if (current) setReviewItems(result.annotations); })
      .catch(error => { if (current) fail(error); }).finally(() => { if (current) setReviewLoading(false); });
    return () => { current = false; };
  }, [projectId, textId, tab, reviewStatus, reviewCategory, reviewLowOnly, reviewScope, threshold, refreshTick]);

  useEffect(() => {
    if (!selected) return;
    setDetailDraft({ category: selected.category, congruent: selected.congruent, rationale: selected.rationale, reviewNote: selected.reviewNote ?? "" });
    setDetailEditing(false);
  }, [selected?.id, selected?.version]);

  async function createProject(event: React.FormEvent) {
    event.preventDefault(); setBusy("project");
    try {
      const result = await api<{ project: Project }>("/api/projects", { name: projectName.trim(), description: projectDescription.trim() });
      setProjects(current => [result.project, ...current]); setProjectId(result.project.id); setProjectName(""); setProjectDescription("");
      setModal(null); setNotice({ kind: "success", message: "项目已创建，可以导入第一份文本。" }); setMobileView("text");
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function saveText(event: React.FormEvent) {
    event.preventDefault(); if (!projectId) return; setBusy("text");
    try {
      const payload = { ...editor, projectId, title: editor.title.trim() };
      const result = await api<{ text: SourceText }>("/api/texts", payload, editor.id ? "PATCH" : "POST");
      setTexts(current => editor.id ? current.map(item => item.id === result.text.id ? result.text : item) : [...current, result.text]);
      if (textId === result.text.id) { setAnnotations([]); setSelectedId(""); }
      setTextId(result.text.id); setModal(null); setNotice({ kind: "success", message: editor.id ? "文本已保存为新版本。请为当前版本重新标注。" : "文本已导入。补充语境可以帮助后续判断。" }); setMobileView("text");
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function loadTextFile(file?: File) {
    if (!file) return;
    try {
      if (file.size > 500_000) throw new Error("单份文本请控制在 500 KB 以内；较长语料可按篇章分批导入。");
      const content = await file.text();
      setEditor({ ...EMPTY_EDITOR, title: file.name.replace(/\.txt$/i, ""), content }); setModal("text");
    } catch (error) { fail(error); }
    finally { if (fileInput.current) fileInput.current.value = ""; }
  }
  async function loadDemo() {
    setBusy("demo");
    try {
      const result = await api<{ project: Project; text: SourceText; frameworkId: string }>("/api/demo", {});
      setProjects(current => [result.project, ...current.filter(item => item.id !== result.project.id)]);
      setMode("demo"); setFrameworkId(result.frameworkId); preferredText.current = result.text.id;
      if (projectId === result.project.id) { setTexts(current => [result.text, ...current.filter(item => item.id !== result.text.id)]); setTextId(result.text.id); await refreshAnnotations(); }
      else setProjectId(result.project.id);
      setNotice({ kind: "info", message: "已载入教学文本。点击“载入示例标注”查看预设案例；这些数据不属于真实语料或模型推理结果。" }); setMobileView("text");
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function autoTag() {
    if (!textId || !frameworkId) return;
    if (mode === "llm" && !apiKey && !health?.modelConfigured) { setModal("model"); return; }
    setBusy("tag"); setNotice(null);
    try {
      const result = await api<{ annotations: Annotation[]; runId: string; warnings: string[] }>("/api/auto_tag", {
        textId, frameworkId, threshold, mode, llm: mode === "llm" ? { provider, ...(apiKey ? { apiKey } : {}), ...(model.trim() ? { model: model.trim() } : {}) } : undefined,
      });
      await refreshAnnotations();
      setSelectedId(result.annotations[0]?.id ?? ""); setTab("details");
      setNotice({ kind: result.warnings?.length ? "info" : "success", message: `${mode === "demo" ? "教学示例已载入" : "自动标注已完成"}，返回 ${result.annotations.length} 条记录。${result.warnings?.length ? ` ${result.warnings.join("；")}` : "所有新记录均等待人工核验。"}` });
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function batchReview(action: "accept" | "reject" | "reopen", single?: Annotation) {
    const chosen = single ? [single] : reviewItems.filter(item => checkedIds.includes(item.id));
    if (!projectId || !chosen.length) return;
    setBusy("review");
    try {
      const result = await api<{ updated: number }>("/api/batch_review", { projectId, items: chosen.map(item => ({ id: item.id, version: item.version })), action, note: single ? detailDraft.reviewNote : reviewNote });
      await refreshAnnotations(); setCheckedIds([]);
      setNotice({ kind: "success", message: `已${action === "accept" ? "确认" : action === "reject" ? "排除" : "重新开放"} ${result.updated} 条记录。` });
    } catch (error) { fail(error); if (error instanceof ApiError && error.status === 409) { await refreshAnnotations(); } }
    finally { setBusy(""); }
  }
  async function saveDetail() {
    if (!selected) return; setBusy("detail");
    try {
      const result = await api<{ annotation: Annotation }>("/api/annotations", { id: selected.id, version: selected.version, ...detailDraft }, "PATCH");
      setAnnotations(current => current.map(item => item.id === result.annotation.id ? result.annotation : item)); setDetailEditing(false); setRefreshTick(value => value + 1);
      setNotice({ kind: "success", message: "修订已保存，并保留机器标注来源及审核记录。" });
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function exportData(format: "xlsx" | "json", currentText: boolean) {
    if (!projectId) return; setBusy("export");
    try {
      const query = new URLSearchParams({ projectId, format }); if (currentText && textId) query.set("textId", textId);
      const response = await fetch(`/api/export?${query}`);
      if (!response.ok) { const data = await response.json() as {error?:string}; throw new Error(data.error || "导出未完成。"); }
      const blob = await response.blob(); const url = URL.createObjectURL(blob);
      const link = document.createElement("a"); link.href = url; link.download = `${(currentText ? text?.title : project?.name) || "halliday-annotations"}.${format}`;
      link.click(); setTimeout(() => URL.revokeObjectURL(url), 10_000);
      setNotice({ kind: "success", message: "数据文件已准备好，浏览器将开始下载。" });
    } catch (error) { fail(error); } finally { setBusy(""); }
  }
  async function importExcel(file?: File) {
    if (!file || !projectId) return; setBusy("import"); setImportConflicts([]);
    try {
      if (file.size > 5 * 1024 * 1024) throw new Error("Excel 文件请控制在 5 MB 以内。");
      const form = new FormData(); form.append("file", file); form.append("projectId", projectId);
      const response = await fetch("/api/import", { method: "POST", body: form });
      const result = await response.json() as {error?:string;updated:number;conflicts?:{id:string;reason:string}[]};
      if (!response.ok) throw new Error(result.error || "Excel 导入未完成。");
      setImportConflicts(result.conflicts ?? []); await refreshAnnotations();
      setNotice({ kind: result.conflicts?.length ? "info" : "success", message: `已导入 ${result.updated} 条修订。${result.conflicts?.length ? ` ${result.conflicts.length} 条记录存在冲突，请在导出面板中查看。` : "版本检查已通过。"}` });
    } catch (error) { fail(error); } finally { setBusy(""); if (excelInput.current) excelInput.current.value = ""; }
  }
  function chooseAnnotation(item: Annotation) {
    if (item.textId !== textId) { preferredAnnotation.current = item.id; setTextId(item.textId); }
    else setSelectedId(item.id);
    setTab("details"); setMobileView("panel");
  }
  const closeModal = useMemo(() => () => setModal(null), []);
  const percent = (value: number) => `${Math.round(value * 100)}%`;
  const allChecked = reviewItems.length > 0 && reviewItems.every(item => checkedIds.includes(item.id));
  const annotationPath = selected ? frameworks.flatMap(item => flattenNodes(item.nodes)).find(item => item.node.id === selected.category)?.path : [];
  const filteredProjects = projects.filter(item => item.name.toLowerCase().includes(projectQuery.toLowerCase()));

  return <main className={`app-shell mobile-${mobileView}`}>
    <header className="app-header">
      <a className="brand" href="/" aria-label="Halliday Lab 首页"><span className="brand-monogram">H<span>·</span></span><span className="brand-wordmark">Halliday <b>Lab</b><small>语言与意义的研究工作台</small></span></a>
      <div className="header-center"><span className="header-separator" /><span className="header-workspace">研究工作空间</span><ChevronRight size={13} /><span>语法隐喻标注</span></div>
      <div className="header-actions"><span className={`connection-state ${initializing ? "checking" : health?.ok ? "connected" : ""}`}><i />{initializing ? "正在连接" : health?.ok ? "工作台已连接" : "等待连接"}</span><button className="icon-button" title="使用指南" aria-label="使用指南" onClick={() => setModal("guide")}><CircleHelp size={18} /></button><a className="github-link" href="https://github.com/cinquewoo/Halliday-SFL-analysis-skill" target="_blank" rel="noreferrer">GitHub <ArrowRight size={13} /></a><span className="avatar" title="私有研究工作空间">研</span></div>
    </header>

    <nav className="mobile-navigation" aria-label="工作区切换"><button className={mobileView === "projects" ? "active" : ""} onClick={() => setMobileView("projects")}><FolderClosed size={15} />项目</button><button className={mobileView === "text" ? "active" : ""} onClick={() => setMobileView("text")}><FileText size={15} />文本</button><button className={mobileView === "panel" ? "active" : ""} onClick={() => setMobileView("panel")}><SlidersHorizontal size={15} />标注与审核</button></nav>

    <div className="workspace-grid">
      <aside className="project-sidebar" aria-label="项目和文本导航">
        <div className="sidebar-head"><div className="section-heading"><span className="eyebrow">MY WORKSPACE</span><LayoutPanelLeft size={15} /></div><h2>我的项目<span>{projects.length.toString().padStart(2, "0")}</span></h2><button className="button primary new-project" disabled={!!busy || needSignIn} onClick={() => setModal("project")}><Plus size={16} />新建研究项目</button></div>
        <label className="sidebar-search"><Search size={14} /><input value={projectQuery} onChange={event => setProjectQuery(event.target.value)} placeholder="查找项目…" aria-label="查找项目" /><span>⌕</span></label>
        <div className="project-list">
          {initializing ? <div className="sidebar-empty"><LoaderCircle size={17} className="spinning" />正在载入项目…</div> : filteredProjects.length ? filteredProjects.map(item => <div className="project-group" key={item.id}>
            <button className={`project-item ${projectId === item.id ? "active" : ""}`} onClick={() => { setProjectId(item.id); setMobileView("text"); }}><FolderClosed size={16} /><span>{item.name}</span>{projectId === item.id ? <ChevronDown size={13} /> : <ChevronRight size={13} />}</button>
            {projectId === item.id && <div className="text-list">{texts.map(document => <button key={document.id} className={`text-item ${textId === document.id ? "active" : ""}`} onClick={() => { setTextId(document.id); setMobileView("text"); }}><FileText size={13} /><span>{document.title}</span></button>)}<button className="text-item add-text" disabled={!!busy} onClick={() => { setEditor(EMPTY_EDITOR); setModal("text"); }}><Plus size={13} />添加文本</button></div>}
          </div>) : <div className="sidebar-empty">{projectQuery ? "未找到匹配的项目" : "还没有研究项目\n从一份文本开始探索。"}</div>}
        </div>
        <div className="sidebar-bottom"><button className="sample-card" disabled={!!busy || needSignIn} onClick={() => void loadDemo()}><span className="sample-icon"><FlaskConical size={18} /></span><span><b>先试试一个例子</b><small>载入语法隐喻教学示例</small></span>{busy === "demo" ? <LoaderCircle size={15} className="spinning" /> : <ArrowRight size={15} />}</button><div className="sidebar-footnote"><ShieldCheck size={13} /><span>项目数据按登录身份隔离</span></div></div>
      </aside>

      <section className="main-workspace" aria-label="文本标注工作区">
        <div className="workspace-topline"><div className="breadcrumbs"><span>工作空间</span><ChevronRight size={12} /><b>{project?.name || "开始你的研究"}</b></div><button className="text-button" disabled={!projectId} onClick={() => setModal("export")}><ArrowDownToLine size={14} />导出数据</button></div>
        <div className="document-heading"><div><span className="eyebrow">GRAMMATICAL METAPHOR ANNOTATION</span><h1>{text?.title || "从文本中，发现意义的另一种表达。"}</h1><p>{text ? <><span>{text.genre || "未指定语类"}</span><i />文本版本 v{text.version}<i />{Array.from(text.content).length.toLocaleString()} 字符</> : "将自动分析与人工判断，放在同一张研究桌上。"}</p></div><button className="icon-button document-menu" title="编辑当前文本" aria-label="编辑当前文本" disabled={!text} onClick={() => { if (text) { setEditor({ id: text.id, version: text.version, title: text.title, content: text.content, genre: text.genre, context: text.context }); setModal("text"); } }}><PencilLine size={18} /></button></div>

        {notice && <div className={`notice ${notice.kind}`} role={notice.kind === "error" ? "alert" : "status"}>{notice.kind === "error" ? <AlertCircle size={16} /> : notice.kind === "success" ? <Check size={16} /> : <Info size={16} />}<span>{notice.message}</span><button className="icon-button small" aria-label="关闭提示" onClick={() => setNotice(null)}><X size={14} /></button></div>}

        {needSignIn && <div className="signin-banner"><ShieldCheck size={19} /><div><b>登录后开始研究</b><p>你的项目、文本和审核记录将保存在个人工作空间。</p></div><a className="button primary" href="/signin-with-chatgpt?return_to=%2F" target="_top">登录 ChatGPT <ArrowRight size={14} /></a></div>}

        <div className="annotation-toolbar"><div className="framework-select-wrap"><GitBranch size={15} /><select aria-label="选择理论框架" value={frameworkId} onChange={event => setFrameworkId(event.target.value)} disabled={!!busy || !frameworks.length}>{!frameworks.length && <option value="">载入理论框架…</option>}{frameworks.map(item => <option key={item.id} value={item.id}>{item.name} · v{item.version}</option>)}</select><ChevronDown size={12} /></div><button className="icon-button settings-button" title="模型与阈值设置" aria-label="模型与阈值设置" onClick={() => setModal("model")}><Settings2 size={17} /></button><div className="toolbar-divider" /><button className="button primary tag-button" disabled={!textId || !frameworkId || !!busy} onClick={() => void autoTag()}>{busy === "tag" ? <LoaderCircle size={15} className="spinning" /> : <Sparkles size={15} />}{busy === "tag" ? "正在分析文本…" : mode === "demo" ? "载入示例标注" : "自动标注"}</button></div>

        <div className="stats-row"><div className="stat-block"><span className="stat-icon"><GitBranch size={16} /></span><div><b>{counters.total.toString().padStart(2, "0")}</b><span>标注总数</span></div></div><div className="stat-block"><span className="stat-icon amber"><ClipboardCheck size={16} /></span><div><b>{counters.pending.toString().padStart(2, "0")}</b><span>待核验记录</span></div></div><div className="stat-block"><span className="stat-icon green"><CheckCheck size={16} /></span><div><b>{counters.accepted.toString().padStart(2, "0")}</b><span>人工已确认</span></div></div></div>

        <div className="text-canvas"><div className="canvas-toolbar"><div><FileText size={15} /><b>文本工作区</b>{text && <span className="version-chip">v{text.version}</span>}</div><div><label className="toggle-label"><input type="checkbox" checked={showHighlight} onChange={event => setShowHighlight(event.target.checked)} /><span className="toggle-switch" />显示标注</label><span className="canvas-saved"><span />{loadingText ? "正在载入" : text ? "已保存" : "等待文本"}</span></div></div>
          {text && <div className={`text-provenance ${mode === "demo" || annotations.some(item => item.source === "demo") ? "demo" : ""}`}>{mode === "demo" || annotations.some(item => item.source === "demo") ? <><FlaskConical size={13} /><span>教学示例 · 人工构造案例，仅用于体验工作流程</span></> : <><BookOpen size={13} /><span>{text.context || "尚未补充语境。点击右上角编辑，填写文本来源、场景与研究目标。"}</span></>}</div>}
          {loadingText ? <div className="canvas-loading"><LoaderCircle size={24} className="spinning" /><span>正在载入文本与标注…</span></div> : text ? <div className="paper-document"><div className="paper-top"><span>原始文本 / SOURCE TEXT</span><span>{showHighlight ? "点击高亮查看证据" : "原文阅读模式"}</span></div><HighlightText content={text.content} annotations={showHighlight ? annotations : []} frameworks={frameworks} selectedId={selectedId} onSelect={id => { setSelectedId(id); setTab("details"); setMobileView("panel"); }} threshold={threshold} /><div className="paper-end"><span />END OF TEXT<span /></div></div> : <div className="canvas-empty"><div className="empty-illustration"><div className="illustration-sheet"><span /><span /><span className="highlighted" /><span /><span className="short" /></div><span className="illustration-badge"><Sparkles size={22} /></span><span className="illustration-dot one" /><span className="illustration-dot two" /></div><span className="eyebrow">A NEW WAY TO READ MEANING</span><h2>每一处标注，都有据可循。</h2><p>导入文本，选择理论框架，开始自动分析。<br />在语境、映射与一致式之间，逐条核验你的发现。</p><div className="empty-actions"><button className="button primary" disabled={!!busy || needSignIn} onClick={() => { if (!projectId) setModal("project"); else fileInput.current?.click(); }}><Upload size={15} />{projectId ? "导入文本" : "创建首个项目"}</button><button className="button secondary" disabled={!!busy || needSignIn} onClick={() => void loadDemo()}><Play size={14} />体验教学示例</button></div><div className="empty-capabilities"><span><Check size={12} />保留原始文本</span><span><Check size={12} />支持中英文</span><span><Check size={12} />全过程可复核</span></div></div>}
          <div className="canvas-footer"><div className="legend">{leaves.slice(0, 4).map(node => <span key={node.id}><i style={{ background: node.color }} />{node.label}</span>)}</div><button className="text-button" disabled={!projectId} onClick={() => { setEditor(EMPTY_EDITOR); setModal("text"); }}><FilePlus2 size={13} />添加文本</button></div>
        </div>
        <div className="workspace-note"><ShieldCheck size={13} /><span>模型自评分用于安排复核优先级，不代表准确率。所有自动标注均保留人工审核环节。</span><span className="schema-label">SCHEMA v3</span></div>
      </section>

      <aside className="inspector" aria-label="标注控制面板"><div className="inspector-tabs" role="tablist" aria-label="标注面板"><button role="tab" aria-selected={tab === "details"} className={tab === "details" ? "active" : ""} onClick={() => setTab("details")}><Search size={14} />标注详情</button><button role="tab" aria-selected={tab === "review"} className={tab === "review" ? "active" : ""} onClick={() => setTab("review")}><ClipboardCheck size={14} />批量审核{counters.pending > 0 && <span>{counters.pending}</span>}</button><button role="tab" aria-selected={tab === "framework"} className={tab === "framework" ? "active" : ""} onClick={() => setTab("framework")}><GitBranch size={14} />框架</button></div>
        <div className="inspector-scroll" role="tabpanel">
          {tab === "details" && <>{selected ? <div className="annotation-detail">
            <div className="detail-top"><span className="eyebrow">ANNOTATION INSIGHT</span><span className={`status-chip ${selected.reviewStatus}`}>{STATUS_LABELS[selected.reviewStatus]}</span></div>
            <div className="selected-quote" style={{ "--mark-color": categoryColor(selected.category, frameworks) } as React.CSSProperties}><span className="quote-mark">“</span><h2>{selected.surface}</h2><div className="quote-meta"><span>{selected.source === "demo" ? "教学预设" : selected.source === "manual" ? "人工录入" : "模型标注"}</span><span>字符 {selected.start}–{selected.end}</span></div></div>
            <div className="detail-category"><span style={{ background: categoryColor(selected.category, frameworks) }} /><b>{selected.categoryLabel}</b><span className="record-number">#{String(annotations.indexOf(selected) + 1).padStart(3, "0")}</span></div>
            <div className="theory-path"><span>理论路径</span><p>{annotationPath?.join(" / ") || selected.category}</p></div>
            <div className="confidence-card"><div><span>模型自评分</span><b className={selected.confidence < threshold ? "low-score" : ""}>{percent(selected.confidence)}</b></div><div className="confidence-track"><span style={{ width: percent(Math.max(0, Math.min(1, selected.confidence))), background: selected.confidence < threshold ? "#b68045" : "#326e5f" }} /></div><p>{selected.confidence < threshold ? `低于 ${percent(threshold)} 提醒阈值，建议优先核验。` : "达到提醒阈值，仍需人工核验。"}</p></div>
            {detailEditing ? <div className="detail-edit-fields"><label className="field-label">类别<select value={detailDraft.category} onChange={event => setDetailDraft(current => ({ ...current, category: event.target.value }))}>{!leaves.some(node => node.id === detailDraft.category) && <option value={detailDraft.category}>{selected.categoryLabel}</option>}{leaves.map(node => <option key={node.id} value={node.id}>{node.label}</option>)}</select></label><label className="field-label">一致式改写<textarea rows={3} value={detailDraft.congruent} onChange={event => setDetailDraft(current => ({ ...current, congruent: event.target.value }))} /></label><label className="field-label">判定依据<textarea rows={4} value={detailDraft.rationale} onChange={event => setDetailDraft(current => ({ ...current, rationale: event.target.value }))} /></label></div> : <><div className="evidence-section"><h3><span className="detail-step">01</span>一致式改写</h3><div className="congruent-box">{selected.congruent || "未提供稳定的一致式改写；请补充语境后复核。"}</div></div><div className="evidence-section"><h3><span className="detail-step">02</span>判定依据</h3><p>{selected.rationale || "未提供判定说明。"}</p></div></>}
            <div className="evidence-section"><h3><span className="detail-step">03</span>支持证据</h3>{selected.evidence?.length ? <ul className="evidence-list">{selected.evidence.map((item, index) => <li key={index}><Check size={12} /><span>{item}</span></li>)}</ul> : <p className="subtle">暂无可核验的支持证据。</p>}</div>
            <div className="evidence-section counter"><h3><span className="detail-step">04</span>反向检验</h3>{selected.counterEvidence?.length ? <ul className="evidence-list">{selected.counterEvidence.map((item, index) => <li key={index}><Info size={12} /><span>{item}</span></li>)}</ul> : <p className="subtle">请考虑词汇隐喻、常规用法或语境不足等替代解释。</p>}</div>
            <label className="field-label review-note">人工复核备注<textarea rows={2} value={detailDraft.reviewNote} onChange={event => setDetailDraft(current => ({ ...current, reviewNote: event.target.value }))} placeholder="记录你接受、修订或排除的依据…" /></label>
            <div className="detail-actions">{detailEditing ? <><button className="button secondary" onClick={() => setDetailEditing(false)}>取消修订</button><button className="button primary" disabled={!!busy} onClick={() => void saveDetail()}><Check size={14} />保存修订</button></> : <><button className="button secondary" onClick={() => setDetailEditing(true)}><PencilLine size={14} />修订</button><button className="button primary" disabled={!!busy || selected.reviewStatus === "accepted"} onClick={() => void batchReview("accept", selected)}><Check size={14} />确认标注</button></>}</div>
            <div className="detail-secondary-actions"><button className="text-button danger" disabled={!!busy || selected.reviewStatus === "rejected"} onClick={() => void batchReview("reject", selected)}>排除此记录</button><button className="text-button" disabled={!!busy || selected.reviewStatus === "pending"} onClick={() => void batchReview("reopen", selected)}><RotateCcw size={12} />重新审核</button></div>
            <details className="compact-details record-json"><summary>完整结构化记录 <ChevronDown size={13} /></summary><pre>{JSON.stringify(selected.record, null, 2)}</pre><button className="text-button" onClick={() => { void navigator.clipboard?.writeText(JSON.stringify(selected.record, null, 2)).then(() => setNotice({ kind: "success", message: "结构化记录已复制。" })).catch(fail); }}>复制 JSON</button></details>
          </div> : <div className="detail-empty"><div className="empty-panel-icon"><Search size={24} /></div><span className="eyebrow">LOOK CLOSER</span><h2>让每个判断<br />都有一条证据链。</h2><p>点击文本中的高亮片段，查看理论路径、一致式改写与判定依据。</p><div className="empty-workflow"><span><b>01</b>载入文本与语境</span><span><b>02</b>运行自动标注</span><span><b>03</b>逐条核验与导出</span></div><button className="text-button" onClick={() => setModal("guide")}>了解标注流程 <ArrowRight size={13} /></button></div>}
            {annotations.length > 1 && <div className="annotation-pagination"><button className="text-button" disabled={annotations.indexOf(selected!) <= 0} onClick={() => setSelectedId(annotations[annotations.indexOf(selected!) - 1]?.id ?? "")}><ChevronRight size={12} className="rotate-180" />上一条</button><span>{selected ? annotations.indexOf(selected) + 1 : 0} / {annotations.length}</span><button className="text-button" disabled={annotations.indexOf(selected!) >= annotations.length - 1} onClick={() => setSelectedId(annotations[annotations.indexOf(selected!) + 1]?.id ?? "")}>下一条<ChevronRight size={12} /></button></div>}
          </>}

          {tab === "review" && <div className="batch-review"><div className="section-heading"><span className="eyebrow">HUMAN IN THE LOOP</span><ClipboardCheck size={17} /></div><h2>把判断，交回研究者。</h2><p className="subtle">按类别与自评分筛选，逐条核验后批量提交。</p><div className="review-filters"><select aria-label="审核范围" value={reviewScope} onChange={event => setReviewScope(event.target.value as "text" | "project")}><option value="text">当前文本</option><option value="project">整个项目</option></select><select aria-label="审核状态" value={reviewStatus} onChange={event => setReviewStatus(event.target.value)}><option value="pending">待审核</option><option value="modified">已修订</option><option value="accepted">已确认</option><option value="rejected">已排除</option><option value="">所有状态</option></select><select className="full-width" aria-label="类别筛选" value={reviewCategory} onChange={event => setReviewCategory(event.target.value)}><option value="">所有类别</option>{frameworks.flatMap(item => leafNodes(item.nodes)).filter((node, index, all) => all.findIndex(item => item.id === node.id) === index).map(node => <option key={node.id} value={node.id}>{node.label}</option>)}</select><label className="checkbox-label full-width"><input type="checkbox" checked={reviewLowOnly} onChange={event => setReviewLowOnly(event.target.checked)} />仅看低于 {percent(threshold)} 的记录<span className="filter-badge">优先核验</span></label></div><div className="review-list-head"><label className="checkbox-label"><input type="checkbox" checked={allChecked} onChange={event => setCheckedIds(event.target.checked ? reviewItems.map(item => item.id) : [])} disabled={!reviewItems.length} />全选当前结果</label><span>{reviewItems.length} 条</span></div>
            <div className="review-list">{reviewLoading ? <div className="review-empty"><LoaderCircle size={20} className="spinning" />正在筛选记录…</div> : reviewItems.length ? reviewItems.map(item => <div className={`review-item ${checkedIds.includes(item.id) ? "checked" : ""}`} key={item.id}><input type="checkbox" aria-label={`选择标注：${item.surface}`} checked={checkedIds.includes(item.id)} onChange={event => setCheckedIds(current => event.target.checked ? [...current, item.id] : current.filter(id => id !== item.id))} /><button onClick={() => chooseAnnotation(item)}><span className="review-surface">{item.surface}</span><span className="review-item-meta"><i style={{ background: categoryColor(item.category, frameworks) }} />{item.categoryLabel}<span className={item.confidence < threshold ? "low-score" : ""}>{percent(item.confidence)}</span></span></button><ChevronRight size={14} /></div>) : <div className="review-empty"><CheckCheck size={23} /><b>当前筛选下没有记录</b><span>调整筛选条件，或先运行自动标注。</span></div>}</div>
            <label className="field-label">批量复核备注<textarea rows={2} value={reviewNote} onChange={event => setReviewNote(event.target.value)} placeholder="本次审核的共同依据（可选）" /></label><div className="review-selection"><span>已选择 <b>{checkedIds.length}</b> 条</span><button className="text-button" onClick={() => setCheckedIds([])}>清空选择</button></div><div className="detail-actions"><button className="button secondary" disabled={!checkedIds.length || !!busy} onClick={() => void batchReview("reject")}><X size={14} />批量排除</button><button className="button primary" disabled={!checkedIds.length || !!busy} onClick={() => void batchReview("accept")}><CheckCheck size={14} />批量确认</button></div><button className="text-button reopen-batch" disabled={!checkedIds.length || !!busy} onClick={() => void batchReview("reopen")}><RotateCcw size={12} />将所选记录重新置为待审核</button><p className="review-footnote"><ShieldCheck size={12} />提交前会检查记录版本；发生冲突时不会覆盖他人的更新。</p>
          </div>}
          {tab === "framework" && <FrameworkEditor framework={framework} onSaved={saved => { setFrameworks(current => [...current, saved]); setFrameworkId(saved.id); setNotice({ kind: "success", message: "自定义框架已保存，可以用于新的标注任务。" }); }} onError={fail} />}
        </div><div className="inspector-footer"><span className="footer-dot" />证据优先 · 人工核验<span>HALLIDAY LAB</span></div>
      </aside>
    </div>

    <input type="file" ref={fileInput} accept=".txt,text/plain" hidden onChange={event => void loadTextFile(event.target.files?.[0])} />
    <input type="file" ref={excelInput} accept=".xlsx" hidden onChange={event => void importExcel(event.target.files?.[0])} />

    {modal === "project" && <Modal title="创建研究项目" subtitle="为一组文本、理论框架与审核记录建立共同空间。" onClose={closeModal}><form onSubmit={event => void createProject(event)}><label className="field-label">项目名称<input required autoFocus maxLength={120} value={projectName} onChange={event => setProjectName(event.target.value)} placeholder="例如：学术语篇中的语法隐喻" /></label><label className="field-label">研究说明<textarea rows={3} maxLength={2000} value={projectDescription} onChange={event => setProjectDescription(event.target.value)} placeholder="研究问题、语料来源或标注范围（可选）" /></label><div className="modal-actions"><button type="button" className="button secondary" onClick={closeModal}>取消</button><button className="button primary" type="submit" disabled={!!busy || !projectName.trim()}>{busy === "project" ? <LoaderCircle size={15} className="spinning" /> : <FolderPlus size={15} />}创建项目</button></div></form></Modal>}

    {modal === "text" && <Modal title={editor.id ? "编辑文本与语境" : "导入研究文本"} subtitle={editor.id ? "编辑内容将生成文本新版本；旧版标注保留在历史中。" : "保留原文，补充足够的语境，获得可复核的分析。"} onClose={closeModal} wide><form onSubmit={event => void saveText(event)}><div className="form-two-columns"><label className="field-label">文本标题<input required maxLength={200} value={editor.title} onChange={event => setEditor(current => ({ ...current, title: event.target.value }))} placeholder="为这份文本命名" /></label><label className="field-label">语类 / 文本类型<input value={editor.genre} onChange={event => setEditor(current => ({ ...current, genre: event.target.value }))} placeholder="例如：学术论文、新闻、对话" /></label></div><label className="field-label">语境与来源<textarea rows={2} value={editor.context} onChange={event => setEditor(current => ({ ...current, context: event.target.value }))} placeholder="作者与对象、活动场景、出处、前后文等。不要只输入孤立词语。" /></label><label className="field-label text-editor-label"><span>原始文本 <button type="button" className="text-button" onClick={() => fileInput.current?.click()}><Upload size={13} />选择 TXT 文件</button></span><textarea className="source-editor" required rows={10} value={editor.content} onChange={event => setEditor(current => ({ ...current, content: event.target.value }))} placeholder="粘贴需要分析的完整文本…" /></label><div className="editor-footer"><span>{Array.from(editor.content).length.toLocaleString()} 字符 · UTF-8 文本</span><span>中英文均可</span></div><div className="modal-actions"><button type="button" className="button secondary" onClick={closeModal}>取消</button><button type="submit" className="button primary" disabled={!!busy || !editor.content.trim() || !editor.title.trim()}>{busy === "text" ? <LoaderCircle size={15} className="spinning" /> : <Check size={15} />}{editor.id ? "保存新版本" : "保存文本"}</button></div></form></Modal>}

    {modal === "model" && <Modal title="模型与标注设置" subtitle="选择推理服务，并设定人工核验的优先级。" onClose={closeModal}><label className="field-label">运行方式<select value={mode} onChange={event => setMode(event.target.value as "llm" | "demo")}><option value="llm">调用 LLM 自动标注</option><option value="demo">教学示例（仅支持内置示例文本）</option></select></label>{mode === "llm" ? <><div className="form-two-columns"><label className="field-label">模型服务<select value={provider} onChange={event => { setProvider(event.target.value as Provider); setModel(""); }}>{PROVIDERS.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select></label><label className="field-label">模型 ID<input value={model} onChange={event => setModel(event.target.value)} placeholder={PROVIDERS.find(item => item.id === provider)?.model} /></label></div><label className="field-label">API Key<input type="password" autoComplete="off" value={apiKey} onChange={event => setApiKey(event.target.value)} placeholder={health?.modelConfigured ? "可留空，使用服务端已配置的密钥" : "填写你自己的 API Key"} /></label><div className="key-notice"><ShieldCheck size={14} /><p>密钥仅保留在当前页面内存中，刷新后清除。文本会发送给你选择的模型服务，可能产生 API 费用。</p></div><button className="text-button" disabled={!apiKey} onClick={() => setApiKey("")}>清除本次会话密钥</button></> : <div className="mode-notice"><FlaskConical size={18} /><p>教学模式使用预设案例，不调用模型。请先从左侧“先试试一个例子”载入配套文本。</p></div>}<div className="threshold-control"><div><label htmlFor="confidence-threshold">低自评分提醒阈值</label><b>{percent(threshold)}</b></div><input id="confidence-threshold" type="range" min="0.1" max="1" step="0.05" value={threshold} onChange={event => setThreshold(Number(event.target.value))} /><div className="range-labels"><span>10%</span><span>100%</span></div><p>低于阈值的记录优先提示复核。该分数是模型自评分，尚未经标注金标准校准。</p></div><div className="modal-actions"><button className="button primary" onClick={closeModal}><Check size={15} />应用设置</button></div></Modal>}

    {modal === "export" && <Modal title="把研究带到下一步" subtitle="导出可复核的记录，或将 Excel 中的人工修订带回工作台。" onClose={closeModal}><div className="export-options"><button disabled={!!busy || !projectId} onClick={() => void exportData("xlsx", false)}><span className="export-icon"><FileSpreadsheet size={22} /></span><span><b>导出项目 Excel</b><small>稳定 ID、版本、原文与审核字段</small></span><Download size={16} /></button><button disabled={!!busy || !textId} onClick={() => void exportData("xlsx", true)}><span className="export-icon"><FileText size={21} /></span><span><b>导出当前文本 Excel</b><small>仅包含当前文本与对应标注</small></span><Download size={16} /></button><button disabled={!!busy || !projectId} onClick={() => void exportData("json", false)}><span className="export-icon code-icon">{ "{}" }</span><span><b>导出完整 JSON</b><small>保留结构化证据与数据溯源</small></span><Download size={16} /></button><button disabled={!!busy || !projectId} onClick={() => excelInput.current?.click()}><span className="export-icon"><Upload size={21} /></span><span><b>导回 Excel 修订</b><small>校验 ID 与版本，冲突记录单独报告</small></span><ArrowRight size={16} /></button></div><div className="roundtrip-note"><Info size={14} /><p>请在导出的工作簿中修改类别、审核状态或备注。不要更改记录 ID、原文与版本字段。</p></div><div id="excel-sync-target" />{importConflicts.length > 0 && <div className="import-conflicts"><h3>{importConflicts.length} 条导入冲突</h3><ul>{importConflicts.map((conflict, index) => <li key={index}><code>{conflict.id}</code><span>{conflict.reason}</span></li>)}</ul></div>}</Modal>}

    {modal === "guide" && <Modal title="在文本、理论与证据之间" subtitle="Halliday Lab · 语法隐喻研究工作流程" onClose={closeModal}><div className="guide-steps"><div><b>01</b><span><h3>准备有语境的文本</h3><p>创建项目，导入完整文本，填写来源、语类与活动场景。</p></span></div><div><b>02</b><span><h3>选择框架，运行标注</h3><p>使用内置语法隐喻框架，或导入自定义 JSON / XML 理论树。在设置中配置模型后运行。</p></span></div><div><b>03</b><span><h3>核验映射与替代解释</h3><p>点击高亮，查看一致式、支持证据与反向检验。模型自评分仅用于安排复核顺序。</p></span></div><div><b>04</b><span><h3>复核、修订与导出</h3><p>按类别筛选并批量审核，导出 Excel / JSON。Excel 修订导回时会检查记录版本。</p></span></div></div><div className="guide-footer"><ShieldCheck size={16} /><p>教学案例会明确标记。自动标注属于候选分析，不能直接替代经过人工核验的研究数据。</p></div><div className="modal-actions"><button className="button primary" onClick={closeModal}>开始探索 <ArrowRight size={14} /></button></div></Modal>}
    <ExcelSync projectId={projectId} visible={modal === "export"} onSynced={() => refreshAnnotations()} />
  </main>;
}
