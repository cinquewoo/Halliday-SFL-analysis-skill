#!/usr/bin/env node
// Synthetic parser tests for cuc_newword_lookup.mjs; performs no network requests.

import assert from "node:assert/strict";
import {
  extractHiddenFields,
  parseWordResult,
  queryTerm,
} from "./cuc_newword_lookup.mjs";

const initialHtml = `
<form>
  <input value="abc&amp;123" type="hidden" name="__VIEWSTATE">
  <input id="__EVENTVALIDATION" type="hidden" value="validation">
</form>`;
const hidden = extractHiddenFields(initialHtml);
assert.equal(hidden.__VIEWSTATE, "abc&123");
assert.equal(hidden.__EVENTVALIDATION, "validation");

const resultHtml = `
<span id="ContentPlaceHolder1_lbParam">词条：低头族；精确匹配</span>
<span id="ContentPlaceHolder1_lbStatus1">本次共检索出1个词条</span>
<span id="ContentPlaceHolder1_lbStatus2">共 1 页</span>
<table id="ContentPlaceHolder1_tbWord">
  <tr><td>【低头族】</td><td>dītóuzú</td></tr>
  <tr><td>[释义]</td><td>合成测试释义。</td></tr>
  <tr><td>[例句1]</td><td>合成测试例句。</td></tr>
  <tr><td>[出处]</td><td>《合成测试词典》</td></tr>
</table>`;
const parsed = parseWordResult(resultHtml, "低头族");
assert.equal(parsed.result_count, 1);
assert.equal(parsed.page_count, 1);
assert.equal(parsed.entries.length, 1);
assert.equal(parsed.entries[0].headword, "低头族");
assert.equal(parsed.entries[0].definition, "合成测试释义。");
assert.equal(parsed.entries[0].exact_match, true);

const missingHtml = `
<span id="ContentPlaceHolder1_lbParam">词条：未收录；精确匹配</span>
<span id="ContentPlaceHolder1_lbStatus1">本次没有检索到记录</span>
<span id="ContentPlaceHolder1_lbStatus2">共 1 页</span>`;
const missing = parseWordResult(missingHtml, "未收录");
assert.equal(missing.result_count, 0);
assert.deepEqual(missing.entries, []);

const oversizedHtml = `
<span id="ContentPlaceHolder1_lbParam">词条：边界；精确匹配</span>
<span id="ContentPlaceHolder1_lbStatus1">本次共检索出1个词条</span>
<span id="ContentPlaceHolder1_lbStatus2">共 1 页</span>
<table id="ContentPlaceHolder1_tbWord">
  <tr><td>【边界】</td><td>${"p".repeat(180)}</td></tr>
  <tr><td>[释义]</td><td>${"释".repeat(1300)}</td></tr>
  ${Array.from(
    { length: 7 },
    (_, index) => `<tr><td>[例句${index + 1}]</td><td>${"例".repeat(900)}</td></tr>`,
  ).join("")}
</table>`;
const oversized = parseWordResult(oversizedHtml, "边界");
assert.equal(oversized.entries[0].pronunciation.length, 121);
assert.equal(oversized.entries[0].definition.length, 1201);
assert.equal(oversized.entries[0].examples.length, 5);
assert.equal(oversized.entries[0].examples[0].length, 801);

await assert.rejects(
  queryTerm("词".repeat(81)),
  /exceeds 80 characters/,
);
await assert.rejects(
  queryTerm("边界", { maxPages: 0 }),
  /positive integer/,
);

console.log("CUC new-word parser regression tests passed");
