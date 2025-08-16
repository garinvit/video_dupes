export type JobOut = {
  id: number;
  status: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
};

export type PairOut = {
  id: number;
  similarity: number;
  label: string;
  file_a: string;
  size_a: number;
  duration_a: number;
  res_a: string;
  file_b: string;
  size_b: number;
  duration_b: number;
  res_b: string;
};

export type GroupFileOut = {
  id: number;
  path: string;
  size: number;
  duration: number;
  res: string;
  is_representative: boolean;
};

export type GroupOut = {
  id: number;
  job_id: number;
  representative_path: string;
  count: number;
  total_size: number;
  files: GroupFileOut[];
};

export type Defaults = {
  roots: string[];
  frames: number;
  scale: number;
  threshold: number;
};
