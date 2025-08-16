const API = "/api";

export async function getDefaults() {
  const r = await fetch(`${API}/jobs/defaults`);
  if (!r.ok) throw new Error("defaults failed");
  return r.json();
}

export async function listJobs() {
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
}) {
  const r = await fetch(`${API}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) throw new Error("start job failed");
  return r.json();
}

export async function getPairs(jobId: number) {
  const r = await fetch(`${API}/jobs/${jobId}/pairs`);
  if (!r.ok) throw new Error("pairs failed");
  return r.json();
}

export async function getGroups(jobId: number) {
  const r = await fetch(`${API}/jobs/${jobId}/groups`);
  if (!r.ok) throw new Error("groups failed");
  return r.json();
}

export async function getFramesBase64(path: string, count = 3, scale = 320) {
  const url = new URL(`${API}/files/frames`, window.location.origin);
  url.pathname = `${API}/files/frames`; // ensure proxy
  url.searchParams.set("path", path);
  url.searchParams.set("count", String(count));
  url.searchParams.set("scale", String(scale));
  const r = await fetch(url.toString().replace(window.location.origin, ""));
  if (!r.ok) throw new Error("frames failed");
  return r.json() as Promise<{ frames: string[] }>;
}

export async function deletePaths(paths: string[]) {
  const r = await fetch(`${API}/files/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete failed");
  return r.json() as Promise<{ bytes: number }>;
}

export async function deleteGroup(groupId: number, paths?: string[]) {
  const r = await fetch(`${API}/files/groups/${groupId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paths }),
  });
  if (!r.ok) throw new Error("delete group failed");
  return r.json() as Promise<{ bytes: number }>;
}
