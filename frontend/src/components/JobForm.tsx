import React, { useEffect, useState } from "react";
import { getDefaults, startJob } from "../api";
import type { Defaults, JobOut } from "../types";

type Props = { onJobStarted(job: JobOut): void; };

export default function JobForm({ onJobStarted }: Props) {
  const [d, setD] = useState<Defaults | null>(null);
  const [rootsStr, setRootsStr] = useState("");
  const [frames, setFrames] = useState(20);
  const [scale, setScale] = useState(320);
  const [threshold, setThreshold] = useState(0.88);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    getDefaults().then((res) => {
      setD(res);
      setRootsStr(res.roots.join(","));
      setFrames(res.frames);
      setScale(res.scale);
      setThreshold(res.threshold);
    }).catch(e => setErr(String(e)));
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setErr(null);
    try {
      const roots = rootsStr.split(",").map(s => s.trim()).filter(Boolean);
      const job = await startJob({ roots, frames, scale, threshold });
      onJobStarted(job);
    } catch (e: any) {
      setErr(e.message || String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <form onSubmit={onSubmit} style={{ display:"grid", gap: 8, gridTemplateColumns: "1fr 1fr 1fr 1fr auto", alignItems:"end" }}>
      <div>
        <label>Roots (comma)</label>
        <input value={rootsStr} onChange={e=>setRootsStr(e.target.value)} placeholder="/videos/dir1,/videos/dir2" />
      </div>
      <div>
        <label>Frames</label>
        <input type="number" min={4} max={80} value={frames} onChange={e=>setFrames(Number(e.target.value))} />
      </div>
      <div>
        <label>Scale</label>
        <input type="number" min={0} max={1920} value={scale} onChange={e=>setScale(Number(e.target.value))} />
      </div>
      <div>
        <label>Threshold</label>
        <input type="number" step="0.01" min={0.5} max={1.0} value={threshold} onChange={e=>setThreshold(Number(e.target.value))} />
      </div>
      <button disabled={loading}>{loading ? "Запуск..." : "Запустить"}</button>
      {err && <div style={{ gridColumn: "1 / -1", color: "crimson" }}>{err}</div>}
    </form>
  );
}
