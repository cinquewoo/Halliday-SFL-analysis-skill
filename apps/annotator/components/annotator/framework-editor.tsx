"use client";

import { useEffect, useRef, useState } from "react";
import { Plus, Trash2, GripVertical, Upload, Save, CornerDownRight, GitBranch, ChevronDown } from "lucide-react";
import { api, flattenNodes } from "./types";
import type { Framework, FrameworkNode } from "./types";

function clone<T>(value: T): T { return JSON.parse(JSON.stringify(value)); }
function updateNode(nodes: FrameworkNode[], id: string, update: (node: FrameworkNode) => FrameworkNode): FrameworkNode[] {
  return nodes.map(node => node.id === id ? update(node) : { ...node, children: updateNode(node.children ?? [], id, update) });
}
function removeNode(nodes: FrameworkNode[], id: string): FrameworkNode[] {
  return nodes.filter(node => node.id !== id).map(node => ({ ...node, children: removeNode(node.children ?? [], id) }));
}

export function moveFrameworkNode(nodes: FrameworkNode[], source: string, target: string | null): FrameworkNode[] {
  const found = flattenNodes(nodes).find(x => x.node.id === source)?.node;
  if (!found || source === target || (target && flattenNodes([found]).some(x => x.node.id === target))) return nodes;
  const remaining = removeNode(nodes, source);
  return target ? updateNode(remaining, target, parent => ({ ...parent, children: [...(parent.children ?? []), found] })) : [...remaining, found];
}

export function parseFrameworkFile(source: string, filename: string): Partial<Framework> & { nodes: FrameworkNode[] } {
  if (!filename.toLowerCase().endsWith(".xml")) {
    const parsed = JSON.parse(source);
    if (!parsed || !Array.isArray(parsed.nodes)) throw new Error("JSON 需要包含 nodes 数组。");
    return parsed;
  }
  if (/<!DOCTYPE|<!ENTITY/i.test(source)) throw new Error("XML 不能包含 DTD 或实体声明。");
  const document = new DOMParser().parseFromString(source, "text/xml");
  if (document.querySelector("parsererror")) throw new Error("XML 格式无效。");
  const root = document.documentElement;
  const parseNode = (element: Element, depth: number): FrameworkNode => {
    if (depth > 12) throw new Error("框架层级不能超过 12 层。");
    return {
      id: element.getAttribute("id") || `node-${crypto.randomUUID()}`,
      label: element.getAttribute("label") || element.getAttribute("name") || "未命名节点",
      color: element.getAttribute("color") || "#2d7166",
      children: Array.from(element.children).filter(child => child.tagName === "node").map(child => parseNode(child, depth + 1)),
    };
  };
  const nodes = Array.from(root.children).filter(child => child.tagName === "node").map(child => parseNode(child, 0));
  if (!nodes.length) throw new Error("XML 格式应为 <framework><node id=\"…\" label=\"…\" /></framework>。");
  return { name: root.getAttribute("name") || "导入的框架", description: root.getAttribute("description") || "", nodes, prompt: root.querySelector("prompt")?.textContent ?? "" };
}

export default function FrameworkEditor({ framework, onSaved, onError }: {
  framework?: Framework; onSaved: (framework: Framework) => void; onError: (error: unknown) => void;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [nodes, setNodes] = useState<FrameworkNode[]>([]);
  const [dragged, setDragged] = useState("");
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [moveId, setMoveId] = useState("");
  const [parentId, setParentId] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setName(framework?.name ?? "自定义分析框架"); setDescription(framework?.description ?? "");
    setPrompt(framework?.prompt ?? ""); setNodes(clone(framework?.nodes ?? [])); setDirty(false);
  }, [framework]);
  function editNodes(value: FrameworkNode[]) { setNodes(value); setDirty(true); }
  function addNode(parent?: string) {
    const node = { id: `custom-${crypto.randomUUID().slice(0, 12)}`, label: "新类别", color: "#2d7166", children: [] };
    editNodes(parent ? updateNode(nodes, parent, value => ({ ...value, children: [...(value.children ?? []), node] })) : [...nodes, node]);
  }
  async function importFile(file?: File) {
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error("框架文件应小于 1 MB。");
      const parsed = parseFrameworkFile(await file.text(), file.name);
      if (flattenNodes(parsed.nodes).length > 200) throw new Error("单个框架最多 200 个节点。");
      setName(parsed.name || file.name.replace(/\.(json|xml)$/i, "")); setDescription(parsed.description ?? "");
      setPrompt(parsed.prompt ?? ""); editNodes(parsed.nodes);
    } catch (error) { onError(error); }
    finally { if (fileInput.current) fileInput.current.value = ""; }
  }
  async function save() {
    setSaving(true);
    try {
      const { framework: saved } = await api<{ framework: Framework }>("/api/framework_manage", { name: name.trim(), description, nodes, prompt });
      setDirty(false); onSaved(saved);
    } catch (error) { onError(error); }
    finally { setSaving(false); }
  }
  function renderTree(values: FrameworkNode[], depth = 0): React.ReactNode {
    return values.map(node => <div className="framework-branch" key={node.id}>
      <div className={`tree-node ${dragged === node.id ? "is-dragging" : ""}`} style={{ marginLeft: depth * 15 }}
        draggable onDragStart={event => { event.stopPropagation(); setDragged(node.id); event.dataTransfer.setData("text/plain", node.id); }}
        onDragEnd={() => setDragged("")} onDragOver={event => { event.preventDefault(); event.stopPropagation(); }}
        onDrop={event => { event.preventDefault(); event.stopPropagation(); editNodes(moveFrameworkNode(nodes, event.dataTransfer.getData("text/plain"), node.id)); setDragged(""); }}>
        <GripVertical size={13} className="drag-handle" aria-hidden="true" />
        <input type="color" className="color-input" aria-label={`${node.label}的颜色`} value={/^#[a-f\d]{6}$/i.test(node.color) ? node.color : "#2d7166"} onChange={event => editNodes(updateNode(nodes, node.id, value => ({ ...value, color: event.target.value })))} />
        <input aria-label="节点名称" value={node.label} onChange={event => editNodes(updateNode(nodes, node.id, value => ({ ...value, label: event.target.value })))} />
        <button type="button" className="icon-button small" title="添加子节点" aria-label={`在${node.label}下添加子节点`} onClick={() => addNode(node.id)}><Plus size={13} /></button>
        <button type="button" className="icon-button small" title="删除节点及子节点" aria-label={`删除${node.label}及子节点`} onClick={() => editNodes(removeNode(nodes, node.id))}><Trash2 size={12} /></button>
      </div>
      {renderTree(node.children ?? [], depth + 1)}
    </div>);
  }
  return <div className="framework-editor">
    <div className="section-heading"><span className="eyebrow">THEORETICAL FRAMEWORK</span><GitBranch size={17} /></div>
    <h2>让理论成为可检验的框架。</h2>
    <p className="subtle">拖动节点可调整层级。内置框架的改动将另存为自定义版本。</p>
    <label className="field-label">框架名称<input value={name} maxLength={120} onChange={event => { setName(event.target.value); setDirty(true); }} /></label>
    <label className="field-label">说明<textarea rows={2} value={description} onChange={event => { setDescription(event.target.value); setDirty(true); }} /></label>
    <div className="tree-tools"><span>类别树 <b>{flattenNodes(nodes).length}</b></span><button type="button" className="text-button" onClick={() => addNode()}><Plus size={13} />添加类别</button></div>
    <div className="framework-tree" onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); editNodes(moveFrameworkNode(nodes, event.dataTransfer.getData("text/plain"), null)); setDragged(""); }}>
      {nodes.length ? renderTree(nodes) : <p className="subtle">添加首个类别，或导入 JSON / XML 框架。</p>}
      <div className="root-drop"><CornerDownRight size={12} />拖到此处移至根层级</div>
    </div>
    <details className="compact-details"><summary>使用键盘调整层级 <ChevronDown size={13} /></summary><div className="keyboard-move">
      <select aria-label="要移动的类别" value={moveId} onChange={event => setMoveId(event.target.value)}><option value="">选择类别</option>{flattenNodes(nodes).map(({ node }) => <option key={node.id} value={node.id}>{node.label}</option>)}</select>
      <select aria-label="目标父类别" value={parentId} onChange={event => setParentId(event.target.value)}><option value="">根层级</option>{flattenNodes(nodes).map(({ node }) => <option key={node.id} value={node.id}>{node.label}</option>)}</select>
      <button type="button" className="button secondary small" disabled={!moveId} onClick={() => editNodes(moveFrameworkNode(nodes, moveId, parentId || null))}>移动</button>
    </div></details>
    <details className="compact-details"><summary>标注指令 <ChevronDown size={13} /></summary><textarea aria-label="自定义框架标注指令" rows={6} value={prompt} onChange={event => { setPrompt(event.target.value); setDirty(true); }} placeholder="说明类别边界、判断依据和排除条件…" /><p className="subtle">另存的自定义框架使用通用标注格式；正式 Schema v3 编码请使用内置语法隐喻框架。</p></details>
    <input type="file" accept=".json,.xml,application/json,text/xml" ref={fileInput} hidden onChange={event => void importFile(event.target.files?.[0])} />
    <div className="framework-actions"><button className="button secondary" type="button" onClick={() => fileInput.current?.click()}><Upload size={14} />导入框架</button><button className="button primary" type="button" onClick={() => void save()} disabled={saving || !nodes.length || !name.trim() || !dirty}><Save size={14} />{saving ? "正在保存…" : "另存为新版本"}</button></div>
  </div>;
}
