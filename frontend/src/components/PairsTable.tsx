import React, { useMemo, useState } from "react";
import type { PairOut } from "../types";
import PreviewModal from "./PreviewModal";

type SelKey = string; // уникальный ключ для выбранного файла

function keyFor(path: string) { return path; }

export default function PairsTable({ pairs, onSelectionChange }: {
  pairs: PairOut[];
  onSelectionChange?: (selectedPaths: string[], bytes: number) => void;
}) {
  const [selected, setSelected] = useState<Record<SelKey, boolean>>({});
  const [previewPath, setPreviewPath] = useState<string|null>(null);

  const selectedList = useMemo(() => Object.keys(selected).filter(k => selected[k]), [selected]);

  const totalBytes = useMemo(() => {
    const sizes: Record<string, number> = {};
    for (const p of pairs) {
      sizes[p.file_a] = p.size_a;
      sizes[p.file_b] = p.size_b;
    }
    return selectedList.reduce((sum, path) => sum + (sizes[path] || 0), 0);
  }, [selectedList, pairs]);

  function toggle(path: string) {
    setSelected(prev => {
      const next = { ...prev, [path]: !prev[path] };
      onSelectionChange?.(Object.keys(next).filter(k => next[k]), Object.keys(next).filter(k => next[k]).reduce((s, p) => {
        const found = pairs.find(pp => pp.file_a === p || pp.file_b === p);
        if (!found) return s;
        const size = (found.file_a === p) ? found.size_a : found.size_b;
        return s + (size || 0);
      }, 0));
      return next;
    });
  }

  function row(filePath: string, size: number, duration: number, res: string) {
    const k = keyFor(filePath);
    const checked = !!selected[k];
    return (
      <div style={{ display: "grid", gridTemplateColumns: "24px 1fr auto", gap: 6, alignItems: "center" }}>
        <input type="checkbox" checked={checked} onChange={()=>toggle(filePath)} />
        <div style={{ overflow: "hidden", textOverflow: "ellipsis" }} title={`${filePath}\n${size} bytes, ${duration.toFixed(1)}s, ${res}`}>
          {filePath}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={()=>setPreviewPath(filePath)}>Preview</button>
        </div>
      </div>
    );
  }

  return (
    <>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Similarity</th>
            <th style={{ textAlign: "left" }}>Label</th>
            <th style={{ textAlign: "left" }}>File A</th>
            <th style={{ textAlign: "left" }}>File B</th>
          </tr>
        </thead>
        <tbody>
          {pairs.map(p => (
            <tr key={p.id}>
              <td>{(p.similarity*100).toFixed(2)}%</td>
              <td>{p.label}</td>
              <td>{row(p.file_a, p.size_a, p.duration_a, p.res_a)}</td>
              <td>{row(p.file_b, p.size_b, p.duration_b, p.res_b)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <PreviewModal path={previewPath} onClose={()=>setPreviewPath(null)} />
    </>
  );
}
