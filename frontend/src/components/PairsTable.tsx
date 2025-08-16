import React, { useState } from "react";
import type { PairOut } from "../types";
import { getFramesBase64 } from "../api";

type PreviewMap = Record<string, string[]>;

export default function PairsTable({ pairs }: { pairs: PairOut[] }) {
  const [previews, setPreviews] = useState<PreviewMap>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  async function loadPreview(path: string) {
    if (previews[path] || loading[path]) return;
    setLoading((m) => ({ ...m, [path]: true }));
    try {
      const { frames } = await getFramesBase64(path, 3, 320);
      setPreviews((m) => ({ ...m, [path]: frames }));
    } catch (e) {
      setPreviews((m) => ({ ...m, [path]: [] }));
    } finally {
      setLoading((m) => ({ ...m, [path]: false }));
    }
  }

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th>Similarity</th>
          <th>Label</th>
          <th>File A</th>
          <th>File B</th>
        </tr>
      </thead>
      <tbody>
        {pairs.map(p => (
          <tr key={p.id}>
            <td>{(p.similarity*100).toFixed(2)}%</td>
            <td>{p.label}</td>
            <td>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span title={`${p.size_a} bytes, ${p.duration_a}s, ${p.res_a}`}>{p.file_a}</span>
                <button onClick={()=>loadPreview(p.file_a)} disabled={loading[p.file_a]}>Preview</button>
                <div style={{ display:"flex", gap: 4 }}>
                  {(previews[p.file_a] || []).map((b64, i) => (
                    <img key={i} src={`data:image/jpeg;base64,${b64}`} style={{ height: 64 }} />
                  ))}
                </div>
              </div>
            </td>
            <td>
              <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                <span title={`${p.size_b} bytes, ${p.duration_b}s, ${p.res_b}`}>{p.file_b}</span>
                <button onClick={()=>loadPreview(p.file_b)} disabled={loading[p.file_b]}>Preview</button>
                <div style={{ display:"flex", gap: 4 }}>
                  {(previews[p.file_b] || []).map((b64, i) => (
                    <img key={i} src={`data:image/jpeg;base64,${b64}`} style={{ height: 64 }} />
                  ))}
                </div>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
