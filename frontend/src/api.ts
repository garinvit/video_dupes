import type { JobOut, PairOut, GroupOut, Defaults } from "./types";

const API = "/api";

export async function getDefaults(): Promise<Defaults> {
  const r = await fetch(`${API}/jobs/defaults`);
  if (!r.ok) throw new Error("defaults failed");
  return r.json();
}

export async function listJobs(): Promise<JobOut[]> {
  const r = await fetch(`${API}/jobs`);
  if (!r.ok) throw new Error("jobs failed");
  return r.json();
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
  return r.json();
}

export async function getPairs(jobId: number, limit = 100, offset = 0): Promise<{ data: PairOut[]; total: number; }> {
  const url = new URL(`${API}/jobs/${jobId}/pairs`, window.location.origin);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  const r = await fetch(url.toString().replace(window.location.origin, ""));
  if (!r.ok) throw new Error("pairs failed");
  const total = Number(r.headers.get("X-Total-Count") || "0");
  const data = await r.json() as PairOut[];
  return { data, total };
}

export async function getGroups(jobId: number, limit = 100, offset = 0): Promise<{ data: GroupOut[]; total: number; }> {
  const url = new URL(`${API}/jobs/${jobId}/groups`, window.location.origin);
  url.searchParams.set("limit", String(limit));
  url.searchParams.set("offset", String(offset));
  const r = await fetch(url.toString().replace(window.location.origin, ""));
  if (!r.ok) throw new Error("groups failed");
  const total = Number(r.headers.get("X-Total-Count") || "0");
  const data = await r.json() as GroupOut[];
  return { data, total };
}

export async function getFramesBase64(path: string, count = 3, scale = 320): Promise<{ frames: string[] }> {
  const url = new URL(`${API}/files/frames`, window.location.origin);
  url.pathname = `${API}/files/frames`;
  url.searchParams.set("path", path);
  url.searchParams.set("count", String(count));
  url.searchParams.set("scale", String(scale));
  const r = await fetch(url.toString().replace(window.location.origin, ""));
  if (!r.ok) throw new Error("frames failed");
  return r.json() as Promise<{ frames: string[] }>;
}

export async function deletePaths(paths: string[]): Promise<{ bytes: number }> {
  const r = await fetch(`${API}/files/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete failed");
  return r.json() as Promise<{ bytes: number }>;
}

export async function deleteGroup(groupId: number, paths?: string[]): Promise<{ bytes: number }> {
  const r = await fetch(`${API}/files/groups/${groupId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete group failed");
  return r.json() as Promise<{ bytes: number }>;
}
