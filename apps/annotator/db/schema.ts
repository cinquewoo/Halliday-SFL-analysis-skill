import { integer, sqliteTable, text, index, uniqueIndex } from "drizzle-orm/sqlite-core";

export const projects = sqliteTable("projects", {
  id: text("id").primaryKey(),
  ownerId: text("owner_id").notNull(),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  demoKey: text("demo_key"),
  createdAt: text("created_at").notNull(),
}, (table) => [index("projects_owner_idx").on(table.ownerId), uniqueIndex("projects_demo_idx").on(table.ownerId, table.demoKey)]);

export const texts = sqliteTable("texts", {
  id: text("id").primaryKey(),
  projectId: text("project_id").notNull().references(() => projects.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  content: text("content").notNull(),
  version: integer("version").notNull().default(1),
  genre: text("genre").notNull().default(""),
  context: text("context").notNull().default(""),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
}, (table) => [index("texts_project_idx").on(table.projectId)]);

export const textVersions = sqliteTable("text_versions", {
  id: text("id").primaryKey(),
  textId: text("text_id").notNull().references(() => texts.id, { onDelete: "cascade" }),
  version: integer("version").notNull(),
  title: text("title").notNull(),
  content: text("content").notNull(),
  genre: text("genre").notNull().default(""),
  context: text("context").notNull().default(""),
  createdAt: text("created_at").notNull(),
}, (table) => [uniqueIndex("text_versions_identity_idx").on(table.textId, table.version)]);

export const frameworks = sqliteTable("frameworks", {
  id: text("id").primaryKey(),
  ownerId: text("owner_id").notNull(),
  name: text("name").notNull(),
  description: text("description").notNull().default(""),
  version: integer("version").notNull().default(1),
  nodesJson: text("nodes_json").notNull(),
  prompt: text("prompt").notNull().default(""),
  createdAt: text("created_at").notNull(),
}, (table) => [index("frameworks_owner_idx").on(table.ownerId)]);

export const annotationRuns = sqliteTable("annotation_runs", {
  id: text("id").primaryKey(),
  textId: text("text_id").notNull().references(() => texts.id, { onDelete: "cascade" }),
  textVersion: integer("text_version").notNull(),
  frameworkId: text("framework_id").notNull(),
  frameworkVersion: integer("framework_version").notNull(),
  mode: text("mode").notNull(),
  status: text("status").notNull(),
  provider: text("provider"),
  model: text("model"),
  warningsJson: text("warnings_json").notNull().default("[]"),
  createdAt: text("created_at").notNull(),
  finishedAt: text("finished_at"),
}, (table) => [index("annotation_runs_text_idx").on(table.textId)]);

export const annotations = sqliteTable("annotations", {
  id: text("id").primaryKey(),
  textId: text("text_id").notNull().references(() => texts.id, { onDelete: "cascade" }),
  textVersion: integer("text_version").notNull(),
  frameworkId: text("framework_id").notNull(),
  frameworkVersion: integer("framework_version").notNull(),
  runId: text("run_id").notNull().references(() => annotationRuns.id),
  start: integer("start_offset").notNull(),
  end: integer("end_offset").notNull(),
  surface: text("surface").notNull(),
  category: text("category").notNull(),
  originalCategory: text("original_category").notNull(),
  categoryLabel: text("category_label").notNull(),
  confidence: integer("confidence_milli").notNull(),
  rationale: text("rationale").notNull(),
  congruent: text("congruent").notNull().default(""),
  evidenceJson: text("evidence_json").notNull(),
  counterEvidenceJson: text("counter_evidence_json").notNull(),
  reviewStatus: text("review_status").notNull().default("pending"),
  reviewNote: text("review_note").notNull().default(""),
  version: integer("version").notNull().default(1),
  source: text("source").notNull(),
  recordJson: text("record_json").notNull(),
  createdAt: text("created_at").notNull(),
  updatedAt: text("updated_at").notNull(),
}, (table) => [index("annotations_current_idx").on(table.textId, table.textVersion), index("annotations_review_idx").on(table.reviewStatus)]);

export const annotationHistory = sqliteTable("annotation_history", {
  id: text("id").primaryKey(),
  annotationId: text("annotation_id").notNull().references(() => annotations.id, { onDelete: "cascade" }),
  version: integer("version").notNull(),
  actorId: text("actor_id").notNull(),
  snapshotJson: text("snapshot_json").notNull(),
  createdAt: text("created_at").notNull(),
}, (table) => [index("annotation_history_annotation_idx").on(table.annotationId)]);

// Guards are inserted and removed within one D1 transaction. Each mutation's
// guard rechecks ownership and optimistic versions inside that same transaction.
export const mutationGuards = sqliteTable("mutation_guards", {
  id: text("id").primaryKey(),
  createdAt: text("created_at").notNull(),
});
