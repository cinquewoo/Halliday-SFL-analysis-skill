export type ReviewStatus = "pending" | "accepted" | "rejected" | "modified";
export type AnnotationSource = "demo" | "llm" | "manual";
export type Provider = "openai" | "deepseek" | "qwen" | "anthropic";

export interface Project {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  textCount?: number;
  annotationCount?: number;
}
export interface TextDocument {
  id: string;
  projectId: string;
  title: string;
  content: string;
  version: number;
  genre: string;
  context: string;
  createdAt: string;
  updatedAt: string;
}
export interface FrameworkNode {
  id: string;
  label: string;
  color: string;
  children?: FrameworkNode[];
}
export interface Framework {
  id: string;
  name: string;
  description: string;
  version: number;
  nodes: FrameworkNode[];
  prompt: string;
  builtin: boolean;
}
export interface AnnotationDraft {
  start: number;
  end: number;
  surface: string;
  category: string;
  categoryLabel: string;
  confidence: number;
  rationale: string;
  congruent: string;
  evidence: string[];
  counterEvidence: string[];
  source: AnnotationSource;
  record: Record<string, unknown>;
}
export interface Annotation extends AnnotationDraft {
  id: string;
  textId: string;
  textVersion: number;
  frameworkId: string;
  frameworkVersion: number;
  runId: string;
  reviewStatus: ReviewStatus;
  reviewNote: string;
  version: number;
  createdAt: string;
  updatedAt: string;
  /** The machine category is retained when a human edits the review projection. */
  originalCategory: string;
}
export interface LlmSettings {
  provider: Provider;
  apiKey?: string;
  model?: string;
}
export interface ReviewEdit {
  id: string;
  version: number;
  textVersion: number;
  category: string;
  reviewStatus: ReviewStatus;
  reviewNote: string;
  congruent?: string;
  rationale?: string;
}
export interface EditConflict { id: string; reason: string }
