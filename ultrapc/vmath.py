"""Batched vector math with the best available backend.

Backend priority: **GPU torch (CUDA) > numpy (CPU SIMD) > pure Python**, detected
once at import. Every retrieval path calls `cosine_all()` / `Index.search()`
without caring which backend runs — so the same code accelerates automatically
when a CUDA build of torch is present, and still works on a bare machine.

The old per-element Python cosine loop (`ai._cosine` in a comprehension) is the
thing this replaces: numpy alone is ~10-50x faster on it, and the GPU path turns
million-vector search (the vault semantic index) from minutes into milliseconds.
"""

from __future__ import annotations

import math

_np = None
_torch = None
_DEVICE = "cpu"
_BACKEND = "python"

try:
    import numpy as _np
    _BACKEND = "numpy"
except Exception:
    _np = None

try:
    import torch as _torch
    if _torch.cuda.is_available():
        _DEVICE = "cuda"
        _BACKEND = "torch-gpu"
    # torch present but CPU-only: numpy is lighter than CPU-torch for our sizes,
    # so we keep numpy as the CPU backend and only use torch when it's on GPU.
except Exception:
    _torch = None


def backend() -> str:
    """'torch-gpu' | 'numpy' | 'python' — what cosine ops actually run on."""
    return _BACKEND


def device() -> str:
    return _DEVICE


def gpu() -> bool:
    return _BACKEND == "torch-gpu"


# --------------------------------------------------------------------------- #
#  Stateless helpers (drop-in for the old cosine loops)
# --------------------------------------------------------------------------- #

def _py_cosine(a, b) -> float:
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def cosine(a, b) -> float:
    """Single cosine similarity (kept for the few pairwise call sites)."""
    return _py_cosine(list(a), list(b))


def cosine_all(query, vectors) -> list[float]:
    """Cosine similarity of `query` (1-D) against every row of `vectors`
    (2-D / list-of-lists). Returns a plain Python list aligned with `vectors`.
    A dimension mismatch yields zeros rather than crashing (mirrors the old
    `_cosine`, which returned 0 on mismatched dims when swapping embed models)."""
    n = len(vectors) if vectors is not None else 0
    if not n:
        return []
    if _BACKEND == "torch-gpu":
        try:
            with _torch.no_grad():
                m = _torch.as_tensor(vectors, dtype=_torch.float32, device=_DEVICE)
                q = _torch.as_tensor(query, dtype=_torch.float32, device=_DEVICE)
                if m.ndim != 2 or q.shape[0] != m.shape[1]:
                    return [0.0] * n
                m = _torch.nn.functional.normalize(m, dim=1)
                q = _torch.nn.functional.normalize(q, dim=0)
                return (m @ q).detach().cpu().tolist()
        except Exception:
            pass          # fall through to numpy/python on any GPU hiccup
    if _np is not None:
        m = _np.asarray(vectors, dtype=_np.float32)
        q = _np.asarray(query, dtype=_np.float32)
        if m.ndim != 2 or q.ndim != 1 or q.shape[0] != m.shape[1]:
            return [0.0] * n
        norms = _np.linalg.norm(m, axis=1)
        norms[norms == 0] = 1.0
        nq = float(_np.linalg.norm(q)) or 1.0
        return ((m @ q) / (norms * nq)).astype(float).tolist()
    return [_py_cosine(list(query), list(v)) for v in vectors]


def topk(query, vectors, k: int) -> list[tuple[int, float]]:
    """(index, score) for the k rows most similar to `query`, best first."""
    sims = cosine_all(query, vectors)
    order = sorted(range(len(sims)), key=lambda i: -sims[i])[:max(0, k)]
    return [(i, sims[i]) for i in order]


# --------------------------------------------------------------------------- #
#  Stateful index — keeps a pre-normalized matrix on the device for reuse, so
#  repeated searches over a big corpus don't re-upload/re-normalize each query.
#  This is what the vault semantic index (vindex) searches against.
# --------------------------------------------------------------------------- #

class Index:
    def __init__(self, vectors):
        self._n = len(vectors)
        self._backend = _BACKEND
        if not self._n:
            self._m = None
            return
        if _BACKEND == "torch-gpu":
            with _torch.no_grad():
                m = _torch.as_tensor(vectors, dtype=_torch.float32, device=_DEVICE)
                self._m = _torch.nn.functional.normalize(m, dim=1)
        elif _np is not None:
            m = _np.asarray(vectors, dtype=_np.float32)
            norms = _np.linalg.norm(m, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._m = m / norms
        else:
            self._m = [list(v) for v in vectors]

    def __len__(self) -> int:
        return self._n

    def search(self, query, k: int = 10) -> list[tuple[int, float]]:
        if not self._n:
            return []
        if self._backend == "torch-gpu":
            with _torch.no_grad():
                q = _torch.as_tensor(query, dtype=_torch.float32, device=_DEVICE)
                q = _torch.nn.functional.normalize(q, dim=0)
                sims = self._m @ q
                kk = min(max(1, k), self._n)
                vals, idx = _torch.topk(sims, kk)
                return list(zip(idx.cpu().tolist(), vals.cpu().tolist()))
        if _np is not None:
            q = _np.asarray(query, dtype=_np.float32)
            nq = float(_np.linalg.norm(q)) or 1.0
            sims = self._m @ (q / nq)
            kk = min(max(1, k), self._n)
            idx = _np.argpartition(-sims, kk - 1)[:kk]
            idx = idx[_np.argsort(-sims[idx])]
            return [(int(i), float(sims[i])) for i in idx]
        return topk(query, self._m, k)


# --------------------------------------------------------------------------- #
#  Chunked search over an on-disk memmap — for indexes too big to fit in VRAM
#  (or RAM) at once.  Streams row-blocks through the device, keeping a running
#  global top-k, so a query over 8M+ vectors uses a bounded amount of memory
#  regardless of how large the matrix is.  This is what the whole-Wikipedia
#  image index searches against (8.2M×512 float16 = 8.4GB on disk, > 12GB VRAM
#  as float32, so it can't be loaded whole).
# --------------------------------------------------------------------------- #

def topk_memmap(matrix, query, k: int = 12,
                chunk: int = 500_000) -> list[tuple[int, float]]:
    """(index, score) for the k rows of `matrix` (a numpy array/memmap, rows
    stored ~unit-norm) most similar to `query`, streaming `chunk` rows at a
    time so peak memory stays ~chunk×dim regardless of len(matrix)."""
    n = len(matrix)
    if n == 0:
        return []
    k = min(max(1, k), n)

    if _BACKEND == "torch-gpu":
        with _torch.no_grad():
            q = _torch.as_tensor(query, dtype=_torch.float32, device=_DEVICE)
            q = _torch.nn.functional.normalize(q, dim=0)
            top_v = _torch.full((k,), -1e30, device=_DEVICE)
            top_i = _torch.full((k,), -1, dtype=_torch.long, device=_DEVICE)
            for s in range(0, n, chunk):
                blk = _np.ascontiguousarray(matrix[s:s + chunk], dtype=_np.float32)
                t = _torch.from_numpy(blk).to(_DEVICE, non_blocking=True)
                t = _torch.nn.functional.normalize(t, dim=1)   # float16 drift-safe
                sims = t @ q
                idx = _torch.arange(s, s + t.shape[0], device=_DEVICE)
                top_v = _torch.cat([top_v, sims])
                top_i = _torch.cat([top_i, idx])
                top_v, order = _torch.topk(top_v, k)
                top_i = top_i[order]
                del t, sims
            return list(zip(top_i.cpu().tolist(), top_v.cpu().tolist()))

    if _np is not None:
        best_i = _np.full(k, -1, dtype=_np.int64)
        best_v = _np.full(k, -1e30, dtype=_np.float32)
        q = _np.asarray(query, dtype=_np.float32)
        q = q / (float(_np.linalg.norm(q)) or 1.0)
        for s in range(0, n, chunk):
            blk = _np.asarray(matrix[s:s + chunk], dtype=_np.float32)
            norms = _np.linalg.norm(blk, axis=1)
            norms[norms == 0] = 1.0
            sims = (blk @ q) / norms
            idx = _np.arange(s, s + blk.shape[0])
            cat_v = _np.concatenate([best_v, sims])
            cat_i = _np.concatenate([best_i, idx])
            top = _np.argpartition(-cat_v, k - 1)[:k]
            top = top[_np.argsort(-cat_v[top])]
            best_v, best_i = cat_v[top], cat_i[top]
        return [(int(i), float(v)) for i, v in zip(best_i, best_v) if i >= 0]

    return topk(query, [list(r) for r in matrix], k)


class MemmapIndex:
    """Same .search() shape as Index, but backed by an on-disk memmap and
    searched in chunks — for corpora too large to hold on the device."""

    def __init__(self, matrix, chunk: int = 500_000):
        self._m = matrix
        self._chunk = chunk

    def __len__(self) -> int:
        return len(self._m)

    def search(self, query, k: int = 12) -> list[tuple[int, float]]:
        return topk_memmap(self._m, query, k, self._chunk)
