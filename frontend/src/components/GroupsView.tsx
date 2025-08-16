import React, { useEffect, useMemo, useState } from "react";
import type { GroupOut } from "../types";
import { deleteGroup } from "../api";
import SizeBar from "./SizeBar";

type Props = { jobId: number };

export default function GroupsView({ jobId }: Props) {
  const [groups, setGroups] = useState<GroupOut[]>([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [freed, setFreed] = useState(0);
  const pages = useMemo(() => Math.ceil(total / limit), [total, limit]);
  const page = useMemo(() => Math.floor(offset / limit) + 1, [offset, limit]);

  async function load() {
    setLoading(true);
    const url = new URL(`/api/jobs/${jobId}/groups`, window.location.origin);
    url.searchParams.set("limit", String(limit));
    url.searchParams.set("offset", String(offset));
    const r = await fetch(url.toString().replace(window.location.origin, ""));
    if (!r.ok) throw new Error("groups failed");
    const totalCount = Number(r.headers.get("X-Total-Count") || "0");
    setTotal(totalCount);
    const data = await r.json() as GroupOut[];
    setGroups(data);
    setLoading(false);
  }
  useEffect(() => { load(); }, [jobId, limit, offset]);

  async function deleteAllButRep(groupId: number) {
    const res = await deleteGroup(groupId);
    setFreed(freed + res.bytes);
    await load();
  }

  return (
    <div style={{ display: "grid", gap: 12 }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <span>Всего групп: {total}</span>
        <label>Page size:
          <select value={limit} onChange={e=>{ setOffset(0); setLimit(Number(e.target.value)); }}>
            {[25,50,100,200].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <div style={{ marginLeft: "auto" }}>
          {freed > 0 && <SizeBar bytes={freed} />}
        </div>
      </div>
      {loading && <div>Загрузка…</div>}
      {!loading && groups.map(g => (
        <details key={g.id}>
          <summary>
            <b>Группа #{g.id}</b> — {g.count} файлов; суммарно {(g.total_size/(1024**3)).toFixed(2)} GB;
            эталон: <code>{g.representative_path}</code>
            <button style={{ marginLeft: 12 }} onClick={()=>deleteAllButRep(g.id)}>Удалить всё кроме эталона</button>
          </summary>
          <ul style={{ marginLeft: 16 }}>
            {g.files.map(f => (
              <li key={f.id}>
                {f.is_representative ? "⭐ " : ""}{f.path} — {f.res}, {(f.size/(1024**2)).toFixed(1)} MB
              </li>
            ))}
          </ul>
        </details>
      ))}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button disabled={offset===0} onClick={()=>setOffset(Math.max(0, offset-limit))}>← Prev</button>
        <span>Page {page} / {Math.max(1,pages)}</span>
        <button disabled={(offset+limit)>=total} onClick={()=>setOffset(offset+limit)}>Next →</button>
      </div>
    </div>
  );
}
