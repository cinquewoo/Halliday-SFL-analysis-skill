export type Project = { id: string; name: string; description: string; createdAt: string; textCount?: number; annotationCount?: number };
export type SourceText = { id: string; projectId: string; title: string; content: string; version: number; genre: string; context: string; createdAt: string; updatedAt: string };
export type FrameworkNode = { id: string; label: string; color: string; children?: FrameworkNode[] };
export type Framework = { id: string; name: string; description: string; version: number; nodes: FrameworkNode[]; prompt: string; builtin: boolean };
export type Annotation = {
  id: string; textId: string; start: number; end: number; surface: string; category: string; categoryLabel: string;
  confidence: number; rationale: string; congruent: string; evidence: string[]; counterEvidence: string[];
  reviewStatus: "pending" | "accepted" | "rejected" | "modified"; reviewNote: string; version: number;
  source: "demo" | "llm" | "manual"; record: Record<string, unknown>; createdAt: string; updatedAt: string;
};
export type Health = { ok: boolean; modelConfigured: boolean; providers: string[]; schemaVersion: string };
export type Provider = "openai" | "deepseek" | "qwen" | "anthropic";

export const STATUS_LABELS: Record<Annotation["reviewStatus"], string> = { pending: "待审核", accepted: "已确认", rejected: "已排除", modified: "已修订" };

export function flattenNodes(nodes: FrameworkNode[], path: string[] = []): { node: FrameworkNode; path: string[] }[] {
  return nodes.flatMap(node => [{ node, path: [...path, node.label] }, ...flattenNodes(node.children ?? [], [...path, node.label])]);
}

export function leafNodes(nodes: FrameworkNode[]): FrameworkNode[] {
  return nodes.flatMap(node => node.children?.length ? leafNodes(node.children) : [node]);
}

export function categoryColor(category: string, frameworks: Framework[]): string {
  for (const framework of frameworks) {
    const match = flattenNodes(framework.nodes).find(x => x.node.id === category);
    if (match) return match.node.color;
  }
  return "#75877b";
}

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export async function api<T>(url: string, data?: unknown, method = "POST"): Promise<T> {
  const response = await fetch(url, data === undefined ? { cache: "no-store" } : {
    method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
  });
  let result: Record<string, unknown>;
  try { result = await response.json(); } catch { throw new ApiError("服务暂时没有返回有效数据，请稍后重试。", response.status); }
  if (!response.ok) throw new ApiError(typeof result.error === "string" ? result.error : "请求未完成，请重试。", response.status);
  return result as T;
}
