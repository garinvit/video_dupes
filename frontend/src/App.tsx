import React, { useEffect, useState } from "react";
import JobForm from "./components/JobForm";
import { getPairs, getGroups, listJobs } from "./api";
import type { JobOut, PairOut, GroupOut } from "./types";
import PairsTable from "./components/PairsTable";

export default function App() {
  const [jobs, setJobs] = useState<JobOut[]>([]);
  const [current, setCurrent] = useState<JobOut | null>(null);
  const [pairs, setPairs] = useState<PairOut[]>([]);
  const [groups, setGroups] = useState<GroupOut[]>([]);
  const [polling, setPolling] = useState<number | null>(null);

  async function refreshJobs() {
    const js: JobOut[] = await listJobs();
    setJobs(js);
    if (!current && js.length) setCurrent(js[0]);
  }

  useEffect(() => {
    refreshJobs();
    const t = window.setInterval(refreshJobs, 3000);
    return () => window.clearInterval(t);
  }, []);

  useEffect(() => {
    if (!current) return;
    const tick = async () => {
      const js = await listJobs();
      const me = js.find(j => j.id === current.id);
      if (me) {
        setCurrent(me);
        if (me.status === "done") {
          const [ps, gs] = await Promise.all([getPairs(me.id), getGroups(me.id)]);
          setPairs(ps);
          setGroups(gs);
          if (polling) { window.clearInterval(polling); setPolling(null); }
        } else if (!polling) {
          const id = window.setInterval(tick, 2000);
          setPolling(id);
        }
      }
    };
    tick();
    return () => { if (polling) window.clearInterval(polling); };
  }, [current?.id]);

  return (
    <div style={{ padding: 16, fontFamily: "ui-sans-serif, system-ui" }}>
      <h1>Video Dupes</h1>
      <JobForm onJobStarted={(j)=>{ setCurrent(j); refreshJobs(); }} />

      <div style={{ marginTop: 16 }}>
        <h3>Jobs</h3>
        <ul>
          {jobs.map(j => (
            <li key={j.id} style={{ cursor:"pointer", fontWeight: j.id===current?.id ? 700 : 400 }}
                onClick={()=>setCurrent(j)}>
              #{j.id} — {j.status}{j.error ? ` (err: ${j.error})` : ""}{j.finished_at ? `, finished: ${j.finished_at}` : ""}
            </li>
          ))}
        </ul>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Pairs ({pairs.length})</h3>
        <PairsTable pairs={pairs}/>
      </div>

      <div style={{ marginTop: 16 }}>
        <h3>Groups ({groups.length})</h3>
        {groups.map(g => (
          <details key={g.id} style={{ marginBottom: 8 }}>
            <summary>{g.count} files, total { (g.total_size/(1024**3)).toFixed(2) } GB — representative: {g.representative_path}</summary>
            <ul>
              {g.files.map(f => (
                <li key={f.id}>{f.is_representative ? "⭐ " : ""}{f.path} ({f.res}, {(f.size/(1024**2)).toFixed(1)} MB)</li>
              ))}
            </ul>
          </details>
        ))}
      </div>
    </div>
  );
}
