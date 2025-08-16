import React, { useEffect, useState } from "react";
import { getFramesBase64 } from "../api";

type Props = {
  path: string | null;
  onClose: () => void;
};

export default function PreviewModal({ path, onClose }: Props) {
  const [frames, setFrames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!path) return;
    setLoading(true);
    getFramesBase64(path, 3, 320)
      .then(res => setFrames(res.frames || []))
      .finally(() => setLoading(false));
  }, [path]);

  if (!path) return null;

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 9999
    }}
      onClick={onClose}
    >
      <div onClick={e=>e.stopPropagation()} style={{
        background: "#111", color: "#fff", padding: 16, borderRadius: 12,
        minWidth: 480, maxWidth: "90vw"
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
          <div style={{ fontWeight: 700, overflow: "hidden", textOverflow: "ellipsis" }}>{path}</div>
          <button onClick={onClose} style={{ background: "#333", color: "#fff" }}>×</button>
        </div>
        {loading ? <div>Загрузка кадров…</div> : (
          frames.length ? (
            <div style={{ display: "flex", gap: 8 }}>
              {frames.map((b64, i) => (
                <img key={i} src={`data:image/jpeg;base64,${b64}`} style={{ height: 160, borderRadius: 8 }} />
              ))}
            </div>
          ) : <div>Кадры не получены</div>
        )}
      </div>
    </div>
  );
}
