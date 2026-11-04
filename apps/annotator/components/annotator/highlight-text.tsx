"use client";

import { useMemo } from "react";
import type { Annotation, Framework } from "./types";
import { categoryColor } from "./types";

// Splitting at every boundary makes intersecting spans selectable without nesting
// or changing the original UTF-16 offsets. Source characters are never normalized.
export function HighlightText({ content, annotations, frameworks, selectedId, onSelect, threshold }: {
  content: string; annotations: Annotation[]; frameworks: Framework[]; selectedId: string;
  onSelect: (id: string) => void; threshold: number;
}) {
  const paragraphs = useMemo(() => {
    let offset = 0;
    return content.split("\n").map(line => {
      const start = offset;
      offset += line.length + 1;
      return { line, start, end: start + line.length };
    });
  }, [content]);

  return <div className="source-lines" aria-label="带标注的原始文本">
    {paragraphs.map(({ line, start, end }, index) => {
      const visible = annotations.filter(a => a.reviewStatus !== "rejected" && a.start < end && a.end > start && a.start >= 0 && a.end <= content.length && a.end > a.start);
      const points = [...new Set([start, end, ...visible.flatMap(a => [Math.max(start, a.start), Math.min(end, a.end)])])].sort((a, b) => a - b);
      return <div className="source-line" key={`${index}-${start}`}>
        <span className="line-number" aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
        <p>{!line ? <br /> : points.slice(0, -1).map((from, segmentIndex) => {
          const to = points[segmentIndex + 1];
          const covering = visible.filter(a => a.start <= from && a.end >= to);
          const text = content.slice(from, to);
          if (!covering.length) return <span key={from}>{text}</span>;
          const active = covering.find(a => a.id === selectedId) ?? covering[0];
          const color = categoryColor(active.category, frameworks);
          return <button key={from} type="button"
            className={`annotation-mark ${covering.some(a => a.id === selectedId) ? "is-selected" : ""} ${active.confidence < threshold ? "is-low" : ""}`}
            style={{ "--mark-color": color } as React.CSSProperties}
            title={`${active.categoryLabel} · ${Math.round(active.confidence * 100)}%${covering.length > 1 ? ` · ${covering.length} 条重叠标注，点击依次切换` : ""}`}
            aria-label={`${text}，${active.categoryLabel}，模型自评分 ${Math.round(active.confidence * 100)}%${covering.length > 1 ? `，${covering.length} 条重叠标注` : ""}`}
            onClick={() => { const current = covering.findIndex(a => a.id === selectedId); onSelect(covering[(current + 1) % covering.length].id); }}
          >{text}{covering.length > 1 && <sup className="overlap-count">{covering.length}</sup>}</button>;
        })}</p>
      </div>;
    })}
  </div>;
}
