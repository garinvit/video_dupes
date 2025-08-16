// frontend/src/api.ts
import type { JobOut, PairOut, GroupOut, Defaults } from "./types";

const API = "/api";

export async function getDefaults(): Promise<Defaults> {
  const r = await fetch(`${API}/jobs/defaults`);
  if (!r.ok) throw new Error("defaults failed");
  return (await r.json()) as Defaults;
}

export async function listJobs(): Promise<JobOut[]> {
  const r = await fetch(`${API}/jobs`);
  if (!r.ok) throw new Error("jobs failed");
  return (await r.json()) as JobOut[];
}

export async function startJob(payload: {
  roots: string[];
  frames: number;
  scale: number;
  threshold: number;
  exts?: string[];
}): Promise<JobOut> {
  const r = await fetch(`${API}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("start job failed");
  return (await r.json()) as JobOut;
}

export async function getPairs(jobId: number): Promise<PairOut[]> {
  const r = await fetch(`${API}/jobs/${jobId}/pairs`);
  if (!r.ok) throw new Error("pairs failed");
  return (await r.json()) as PairOut[];
}

export async function getGroups(jobId: number): Promise<GroupOut[]> {
  const r = await fetch(`${API}/jobs/${jobId}/groups`);
  if (!r.ok) throw new Error("groups failed");
  return (await r.json()) as GroupOut[];
}

export async function getFramesBase64(path: string, count = 3, scale = 320): Promise<{ frames: string[] }> {
  const url = new URL(`${API}/files/frames`, window.location.origin);
  url.pathname = `${API}/files/frames`;
  url.searchParams.set("path", path);
  url.searchParams.set("count", String(count));
  url.searchParams.set("scale", String(scale));
  const r = await fetch(url.toString().replace(window.location.origin, ""));
  if (!r.ok) throw new Error("frames failed");
  return (await r.json()) as { frames: string[] };
}

export async function deletePaths(paths: string[]): Promise<{ bytes: number }> {
  const r = await fetch(`${API}/files/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete failed");
  return (await r.json()) as { bytes: number };
}

export async function deleteGroup(groupId: number, paths?: string[]): Promise<{ bytes: number }> {
  const r = await fetch(`${API}/files/groups/${groupId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete group failed");
  return (await r.json()) as { bytes: number };
}
