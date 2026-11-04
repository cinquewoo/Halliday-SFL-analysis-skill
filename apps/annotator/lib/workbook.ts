import ExcelJS from "exceljs";
import type { Annotation, Project, ReviewEdit, TextDocument } from "./types";

export interface ExportSnapshot {
  project: Project;
  texts: TextDocument[];
  annotations: Annotation[];
}
export const MAX_WORKBOOK_BYTES = 5 * 1024 * 1024;
const MAX_ROWS = 250;
const CHUNK_SIZE = 12000;
export const REVIEW_HEADERS = [
  "id", "version", "textId", "textVersion", "start_utf16", "end_utf16", "surface",
  "category", "reviewStatus", "reviewNote", "congruent", "rationale", "confidence",
  "source", "frameworkId", "frameworkVersion", "originalCategory",
] as const;
const EDITABLE = new Set(["category", "reviewStatus", "reviewNote", "congruent", "rationale"]);

/** String-typed XLSX cells cannot execute formulas; prefix control characters too. */
export function safeCell(value: unknown): string {
  const text = value == null ? "" : String(value);
  return text.startsWith("'") || /^[\s\u0000-\u001f]*[=+@-]/u.test(text) ? `'${text}` : text;
}
function unsanitize(text: string): string {
  return /^''|^'[\s\u0000-\u001f]*[=+@-]/u.test(text) ? text.slice(1) : text;
}
function splitChunks(text: string): string[] {
  const chunks: string[] = [];
  for (let i = 0; i < text.length; i += CHUNK_SIZE) chunks.push(text.slice(i, i + CHUNK_SIZE));
  return chunks.length ? chunks : [""];
}
export async function snapshotRevision(snapshot: ExportSnapshot): Promise<string> {
  const fingerprint = JSON.stringify({
    projectId: snapshot.project.id,
    texts: snapshot.texts.map(t => [t.id, t.version, t.updatedAt]).sort(),
    annotations: snapshot.annotations.map(a => [a.id, a.version]).sort(),
  });
  const hash = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(fingerprint));
  return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, "0")).join("");
}
function readonlyValue(a: Annotation, header: string): unknown {
  if (header === "start_utf16") return a.start;
  if (header === "end_utf16") return a.end;
  return a[header as keyof Annotation];
}
export async function encodeWorkbook(snapshot: ExportSnapshot): Promise<Uint8Array> {
  if (snapshot.annotations.length > MAX_ROWS) throw new Error("单个工作簿最多导出 250 条标注，请按文本导出或使用 JSON。");
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "Halliday Lab";
  const meta = workbook.addWorksheet("Metadata");
  meta.addRows([
    ["format", "halliday-lab-review-v1"], ["projectId", snapshot.project.id],
    ["revision", await snapshotRevision(snapshot)], ["schemaVersion", "3.0"],
    ["offsets", "Annotation: UTF-16 in document; Schema v3 record: Unicode code points in sentence"],
    ["editable", Array.from(EDITABLE).join(", ")],
    ["confidence", "Uncalibrated model self-rating; not empirical accuracy"],
    ["review", "All generated results require human review; machine records remain immutable"],
    ["synchronization", "Import is atomic. Conflicts require a fresh export. Keep ID/version columns unchanged."],
  ]);
  meta.columns = [{ width: 22 }, { width: 95 }];
  const sheet = workbook.addWorksheet("Annotations");
  sheet.addRow([...REVIEW_HEADERS]);
  for (const annotation of snapshot.annotations) {
    const row = REVIEW_HEADERS.map(key => {
      const value = readonlyValue(annotation, key);
      if (typeof value === "number") return value;
      const text = value == null ? "" : String(value);
      if (text.length > 32000) throw new Error("标注字段超过 Excel 单元格长度限制，请使用 JSON 无损导出。");
      return safeCell(text);
    });
    sheet.addRow(row);
  }
  sheet.views = [{ state: "frozen", ySplit: 1 }];
  sheet.autoFilter = `A1:Q${Math.max(sheet.rowCount, 1)}`;
  sheet.getRow(1).font = { bold: true, color: { argb: "FFFFFFFF" } };
  sheet.getRow(1).fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FF174E4B" } };
  REVIEW_HEADERS.forEach((header, i) => {
    sheet.getColumn(i + 1).width = ["reviewNote", "congruent", "rationale", "surface"].includes(header) ? 40 : 22;
    if (EDITABLE.has(header)) {
      sheet.getColumn(i + 1).fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFEAF5EF" } };
    }
  });
  for (let i = 2; i <= sheet.rowCount; i++) {
    sheet.getCell(i, 9).dataValidation = { type: "list", allowBlank: false, formulae: ['"pending,accepted,rejected,modified"'] };
  }
  const texts = workbook.addWorksheet("Texts");
  texts.addRow(["textId", "textVersion", "title", "genre", "context", "chunk", "content"]);
  for (const text of snapshot.texts) {
    splitChunks(text.content).forEach((chunk, i) => texts.addRow([
      text.id, text.version, safeCell(text.title), safeCell(text.genre), safeCell(text.context), i, safeCell(chunk),
    ]));
  }
  texts.getColumn(7).width = 100;
  const records = workbook.addWorksheet("MachineRecords");
  records.addRow(["annotationId", "chunk", "schema_v3_original_json"]);
  for (const annotation of snapshot.annotations) {
    splitChunks(JSON.stringify(annotation.record)).forEach((chunk, i) => records.addRow([annotation.id, i, safeCell(chunk)]));
  }
  return new Uint8Array(await workbook.xlsx.writeBuffer());
}

/** Bound declared expanded ZIP size before the XLSX parser allocates memory. */
export function validateZipLimits(bytes: Uint8Array): void {
  if (bytes.byteLength > MAX_WORKBOOK_BYTES) throw new Error("Excel 文件不得超过 5 MB。");
  if (bytes.byteLength < 22) throw new Error("不是有效的 XLSX 文件。");
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  let eocd = -1;
  for (let i = bytes.length - 22; i >= Math.max(0, bytes.length - 65557); i--) {
    if (view.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0 || view.getUint16(eocd + 4, true) !== 0 || view.getUint16(eocd + 6, true) !== 0) throw new Error("不支持分卷或损坏的 XLSX 文件。");
  const count = view.getUint16(eocd + 10, true);
  let offset = view.getUint32(eocd + 16, true);
  if (count > 300 || count === 65535) throw new Error("工作簿包含过多压缩条目。");
  let total = 0;
  for (let i = 0; i < count; i++) {
    if (offset + 46 > eocd || view.getUint32(offset, true) !== 0x02014b50) throw new Error("XLSX 压缩目录无效。");
    if (view.getUint16(offset + 8, true) & 1) throw new Error("不支持加密工作簿。");
    const expanded = view.getUint32(offset + 24, true);
    total += expanded;
    if (expanded > 12 * 1024 * 1024 || total > 20 * 1024 * 1024) throw new Error("工作簿解压后过大，请分批导入。");
    offset += 46 + view.getUint16(offset + 28, true) + view.getUint16(offset + 30, true) + view.getUint16(offset + 32, true);
  }
}
function scalar(value: ExcelJS.CellValue): string {
  if (value == null) return "";
  if (typeof value === "object") throw new Error("审核表仅允许纯文本或数字单元格，不允许公式、链接或富文本。");
  return unsanitize(String(value));
}
export async function decodeWorkbook(bytes: Uint8Array): Promise<{ projectId: string; revision: string; edits: ReviewEdit[]; originals: Record<string, string>[] }> {
  validateZipLimits(bytes);
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(bytes as unknown as ExcelJS.Buffer);
  const metaSheet = workbook.getWorksheet("Metadata");
  const sheet = workbook.getWorksheet("Annotations");
  if (!metaSheet || !sheet) throw new Error("请导入本平台导出的工作簿，保留 Metadata 和 Annotations 工作表。");
  const metadata = new Map<string, string>();
  metaSheet.eachRow(row => metadata.set(scalar(row.getCell(1).value), scalar(row.getCell(2).value)));
  if (metadata.get("format") !== "halliday-lab-review-v1") throw new Error("工作簿格式或版本不受支持。");
  for (let i = 0; i < REVIEW_HEADERS.length; i++) {
    if (scalar(sheet.getRow(1).getCell(i + 1).value) !== REVIEW_HEADERS[i]) throw new Error("审核表的列名或顺序已改变，请重新导出。");
  }
  if (sheet.rowCount > MAX_ROWS + 1) throw new Error("单次最多导入 250 条标注。");
  const edits: ReviewEdit[] = [];
  const originals: Record<string, string>[] = [];
  const ids = new Set<string>();
  for (let i = 2; i <= sheet.rowCount; i++) {
    const row = sheet.getRow(i);
    if (!row.getCell(1).value) continue;
    const values = Object.fromEntries(REVIEW_HEADERS.map((key, j) => [key, scalar(row.getCell(j + 1).value)]));
    if (ids.has(values.id)) throw new Error("工作簿中出现重复标注 ID。");
    ids.add(values.id);
    const version = Number(values.version), textVersion = Number(values.textVersion);
    if (!Number.isSafeInteger(version) || version < 1 || !Number.isSafeInteger(textVersion) || textVersion < 1) throw new Error("版本列无效，请重新导出。");
    if (!["pending", "accepted", "rejected", "modified"].includes(values.reviewStatus)) throw new Error("审核状态只能是 pending / accepted / rejected / modified。");
    for (const key of EDITABLE) if (values[key].length > 12000) throw new Error("审核字段过长。");
    edits.push({ id: values.id, version, textVersion, category: values.category,
      reviewStatus: values.reviewStatus as ReviewEdit["reviewStatus"], reviewNote: values.reviewNote,
      congruent: values.congruent, rationale: values.rationale });
    originals.push(values);
  }
  return { projectId: metadata.get("projectId") ?? "", revision: metadata.get("revision") ?? "", edits, originals };
}
export function immutableRowConflicts(rows: Record<string, string>[], current: Annotation[]): { id: string; reason: string }[] {
  const byId = new Map(current.map(a => [a.id, a]));
  const conflicts: { id: string; reason: string }[] = [];
  for (const row of rows) {
    const annotation = byId.get(row.id);
    if (!annotation) { conflicts.push({ id: row.id, reason: "标注不存在、属于其他项目或已不在当前文本版本中。" }); continue; }
    for (const key of REVIEW_HEADERS) {
      if (EDITABLE.has(key)) continue;
      if (String(readonlyValue(annotation, key) ?? "") !== row[key]) {
        conflicts.push({ id: row.id, reason: `只读列 ${key} 已改变，或服务器版本已更新。` }); break;
      }
    }
  }
  return conflicts;
}
