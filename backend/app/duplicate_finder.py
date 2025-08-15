import os
import io
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict
import subprocess

from PIL import Image
import imagehash

VIDEO_EXTS = {".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm", ".ts", ".mts", ".m2ts", ".wmv", ".flv"}

# ---- ffprobe

def ffprobe(path: Path):
    cmd = [
        "ffprobe","-v","error",
        "-select_streams","v:0",
        "-show_entries","format=duration",
        "-show_entries","stream=width,height",
        "-of","json",
        str(path)
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        data = json.loads(out.decode("utf-8", errors="ignore"))
        duration = float(data.get("format",{}).get("duration", 0) or 0)
        width = height = None
        for st in data.get("streams", []):
            if st.get("width") and st.get("height"):
                width = int(st["width"]) ; height = int(st["height"]) ; break
        return duration, width, height
    except subprocess.CalledProcessError:
        return 0.0, None, None

# ---- hashing frames

def phash_image_bytes(jpeg_bytes: bytes) -> int:
    img = Image.open(io.BytesIO(jpeg_bytes))
    return int(str(imagehash.phash(img)), 16)


def grab_frame_phash(path: Path, timestamp: float, scale_width: Optional[int]) -> Optional[int]:
    vf = f"scale={scale_width}:-2" if scale_width and scale_width > 0 else "null"
    cmd = [
        "ffmpeg","-ss",f"{timestamp:.3f}","-i",str(path),
        "-frames:v","1","-vf",vf,"-f","image2pipe","-vcodec","mjpeg","-loglevel","error","pipe:1"
    ]
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return phash_image_bytes(out)
    except subprocess.CalledProcessError:
        return None


def linspace(start: float, stop: float, num: int, endpoint: bool=False) -> List[float]:
    if num <= 0: return []
    if num == 1: return [start]
    step = (stop - start) / (num -  (1 if endpoint else 0) )
    return [start + i*step for i in range(num - (0 if endpoint else 1))]


def hamming64(a:int,b:int)->int:
    return (a ^ b).bit_count()


def seq_similarity(sig_a: List[int], sig_b: List[int]) -> float:
    if not sig_a or not sig_b: return 0.0
    if len(sig_a) > len(sig_b):
        sig_a, sig_b = sig_b, sig_a
    la, lb = len(sig_a), len(sig_b)
    best = 0.0
    denom = 64.0 * la
    for offset in range(0, lb - la + 1):
        dist_sum = 0
        for i in range(la):
            dist_sum += hamming64(sig_a[i], sig_b[offset+i])
        sim = 1.0 - (dist_sum/denom)
        if sim > best: best = sim
        if best > 0.999: break
    return best


def gather_videos(roots: List[Path], exts: List[str]) -> List[Path]:
    exts_set = {e.lower() if e.startswith('.') else '.'+e.lower() for e in exts}
    vids = []
    for r in roots:
        r = r.expanduser()
        if r.is_file():
            if r.suffix.lower() in exts_set: vids.append(r)
        elif r.is_dir():
            for root, _, files in os.walk(r):
                for name in files:
                    if Path(name).suffix.lower() in exts_set:
                        vids.append(Path(root)/name)
    return vids


def signature_for(path: Path, frames: int, scale: int):
    duration, width, height = ffprobe(path)
    horizon = duration if duration > 0.1 else 600.0
    times = linspace(0.0, horizon, frames, endpoint=False)
    hashes = []
    for t in times:
        h = grab_frame_phash(path, t, scale)
        if h is not None: hashes.append(h)
    st = path.stat()
    res = f"{width}x{height}" if width and height else ""
    return {
        "path": str(path),
        "size": st.st_size,
        "duration": float(duration or 0.0),
        "res": res,
        "hashes": hashes,
    }


def compare_all(signs: List[dict], threshold: float):
    pairs = []
    def central(hs):
        return hs[len(hs)//2] if hs else None
    for i in range(len(signs)):
        for j in range(i+1, len(signs)):
            a, b = signs[i], signs[j]
            if not a["hashes"] or not b["hashes"]: continue
            ca, cb = central(a["hashes"]), central(b["hashes"])
            if ca is not None and cb is not None and hamming64(ca,cb) > 20:
                continue
            sim = seq_similarity(a["hashes"], b["hashes"])
            if sim >= threshold:
                da, db = a["duration"], b["duration"]
                full_like = (min(da,db)>0 and (min(da,db)/max(da,db))>0.95 and sim>0.98)
                label = "full-duplicate" if full_like else "near/partial-duplicate"
                pairs.append({
                    "similarity": float(sim),
                    "label": label,
                    "a": a,
                    "b": b,
                })
    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs

# --- Кластеризация дублей в группы ---

def build_groups(signs: List[dict], pairs: List[dict], choose_best=True):
    """
    На вход: сигнатуры и список пар (как из compare_all).
    Возвращает список групп: { 'files': [filedict,...], 'representative': path, 'total_size': int }
    """
    # Индексация по пути
    idx_by_path: Dict[str, int] = {s['path']: i for i, s in enumerate(signs)}
    parent = list(range(len(signs)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for p in pairs:
        a = idx_by_path.get(p['a']['path'])
        b = idx_by_path.get(p['b']['path'])
        if a is not None and b is not None:
            union(a,b)

    comps: Dict[int, List[int]] = {}
    for i in range(len(signs)):
        r = find(i)
        comps.setdefault(r, []).append(i)

    groups = []
    for comp in comps.values():
        if len(comp) < 2:
            continue  # одиночки не интересны
        files = [signs[i] for i in comp]
        # выбрать эталон: максимальная длительность, далее разрешение (площадь), далее размер
        def parse_res(r: str):
            try:
                w,h = r.lower().split('x')
                return int(w)*int(h)
            except Exception:
                return 0
        best = max(files, key=lambda f: (f.get('duration',0.0), parse_res(f.get('res','')), f.get('size',0)))
        total = sum(int(f.get('size',0)) for f in files)
        groups.append({
            'files': files,
            'representative': best['path'],
            'total_size': total,
        })
    return groups