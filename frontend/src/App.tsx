import React, { useEffect, useMemo, useState } from "react";
import JobForm from "./components/JobForm";
import { deletePaths, getGroups, getPairs, listJobs } from "./api";
import type { JobOut, PairOut, GroupOut } from "./types";
import PairsTable from "./components/PairsTable";
import GroupsView from "./components/GroupsView";
import SizeBar from "./components/SizeBar";

export default function App() {
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [current, setCurrent] = useState<JobOut | null>(null);

  // pairs tab
  const [pairs, setPairs] = useState<PairOut[]>([]);
  const [pairsTotal, setPairsTotal] = useState(0);
  const [limit, setLimit] = useState(100);
  const [offset, setOffset] = useState(0);
  const pages = useMemo(()=>Math.ceil(pairsTotal/limit), [pairsTotal, limit]);
  const page = useMemo(()=>Math.floor(offset/limit)+1, [offset, limit]);

  // groups tab (просто список для быстрой навигации/удаления)
  const [groups, setGroups] = useState<GroupOut[]>([]);

  // selection & freed
  const [selectedPaths, setSelectedPaths] = useState<string[]>([]);
  const [selectedBytes, setSelectedBytes] = useState(0);
  const [freedBytes, setFreedBytes] = useState(0);

  const [tab, setTab] = useState<"pairs"|"groups">("pairs");

  async function refreshJobs() {
    const js = await listJobs();
    setJobs(js);
    if (!current && js.length) setCurrent(js[0]);
  }

  // авто-обновление списка jobs
  useEffect(() => {
    refreshJobs();
    const t = window.setInterval(refreshJobs, 3000);
    return () => window.clearInterval(t);
  }, []);

  // загрузка данных по текущему job
  useEffect(() => {
    if (!current) return;
    const fetchData = async () => {
      const me = (await listJobs()).find((j: JobOut) => j.id === current.id);
      if (me) {
        setCurrent(me);
        if (me.status === "done") {
          const { data, total } = await getPairs(me.id, limit, offset);
          setPairs(data);
          setPairsTotal(total);
          const g = await getGroups(me.id, 50, 0);
          setGroups(g.data);
        }
      }
    };
    fetchData();
  }, [current?.id, limit, offset]);

  async function onDeleteSelected() {
    if (!selectedPaths.length) return;
    const res = await deletePaths(selectedPaths);
    setFreedBytes(freedBytes + res.bytes);
    setSelectedPaths([]);
    setSelectedBytes(0);
    // reload pairs
    if (current) {
      const { data, total } = await getPairs(current.id, limit, offset);
      setPairs(data);
      setPairsTotal(total);
    }
  }

  const jobStatusText = current ? (current.status + (current.error ? ` — ${current.error}` : "")) : "—";

  return (
    <div style={{ padding: 16, fontFamily: "ui-sans-serif, system-ui" }}>
      <h1>Video Dupes</h1>

      <JobForm onJobStarted={(j)=>{ setCurrent(j); refreshJobs(); setTab("pairs"); }} />

      <div style={{ marginTop: 12 }}>
        <h3>Jobs</h3>
        <ul>
          {jobs.map((j: JobOut) => (
            <li key={j.id}
                style={{ cursor:"pointer", fontWeight: j.id===current?.id ? 700 : 400 }}
                onClick={()=>{ setCurrent(j); setOffset(0); }}>
              #{j.id} — {j.status}{j.error ? ` (err: ${j.error})` : ""}{j.finished_at ? `, finished: ${j.finished_at}` : ""}
            </li>
          ))}
        </ul>
      </div>

      {/* Прогресс-индикатор по статусу */}
      <div style={{ marginTop: 8 }}>
        <div style={{ marginBottom: 4 }}>Текущий статус: <b>{jobStatusText}</b></div>
        <div style={{ width: 320, height: 10, background: "#eee", borderRadius: 6, overflow: "hidden" }}>
          <div style={{
            height: "100%",
            width: current?.status === "done" ? "100%" : current?.status === "running" ? "66%" :
                   current?.status === "queued" ? "33%" : "0%",
            background: "#6aa84f",
            transition: "width .3s"
          }} />
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <div style={{ display:"flex", gap:12, alignItems:"center" }}>
          <button onClick={()=>setTab("pairs")} disabled={tab==="pairs"}>Pairs</button>
          <button onClick={()=>setTab("groups")} disabled={tab==="groups"}>Groups</button>

          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12 }}>
            {selectedBytes > 0 && <SizeBar bytes={selectedBytes} />}
            {freedBytes > 0 && <div style={{ opacity: 0.8 }}>Всего удалено: <b>{(freedBytes/(1024**3)).toFixed(2)} GB</b></div>}
            {selectedPaths.length > 0 && <button onClick={onDeleteSelected}>Удалить выбранные</button>}
          </div>
        </div>

        {tab==="pairs" && (
          <div style={{ marginTop: 12, display:"grid", gap: 8 }}>
            <div style={{ display:"flex", gap:8, alignItems:"center" }}>
              <span>Total: {pairsTotal}</span>
              <label>Page size:
                <select value={limit} onChange={e=>{ setOffset(0); setLimit(Number(e.target.value)); }}>
                  {[50,100,200,500].map(n=> <option key={n} value={n}>{n}</option>)}
                </select>
              </label>
              <div style={{ marginLeft: "auto" }}>
                <button disabled={offset===0} onClick={()=>setOffset(Math.max(0, offset-limit))}>← Prev</button>
                <span style={{ margin: "0 8px" }}>Page {page} / {Math.max(1, Math.ceil(pairsTotal/limit))}</span>
                <button disabled={(offset+limit)>=pairsTotal} onClick={()=>setOffset(offset+limit)}>Next →</button>
              </div>
            </div>

            <PairsTable
              pairs={pairs}
              onSelectionChange={(paths, bytes)=>{ setSelectedPaths(paths); setSelectedBytes(bytes); }}
            />
          </div>
        )}

        {tab==="groups" && current && <div style={{ marginTop: 12 }}><GroupsView jobId={current.id} /></div>}
      </div>
    </div>
  );
}
