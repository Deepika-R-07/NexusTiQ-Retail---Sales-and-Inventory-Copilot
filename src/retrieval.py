import json
import numpy as np
from pathlib import Path

class LocalRetriever:
    def __init__(self, index_path, embedder=None):
        self.index_path = Path(index_path)
        self.embedder = embedder
        self.items = []
        if self.index_path.exists():
            try:
                self.items = json.loads(self.index_path.read_text(encoding="utf-8"))
            except Exception:
                self.items = []

    def search(self, query, k=5):
        if not self.items:
            return []
        q = None
        if self.embedder:
            try:
                vals = self.embedder([query])
                if vals:
                    q = np.array(vals[0], dtype=float)
            except Exception:
                q = None
        if q is None:
            return self.keyword_search(query, k)
        scored = []
        for item in self.items:
            v = np.array(item.get("embedding", []), dtype=float)
            if len(v) != len(q):
                continue
            denom = np.linalg.norm(q) * np.linalg.norm(v)
            score = float(np.dot(q, v) / denom) if denom else 0
            scored.append((score, item))
        return [dict(item, score=round(score,4)) for score,item in sorted(scored, reverse=True, key=lambda x:x[0])[:k]]

    def keyword_search(self, query, k=5):
        tokens=set(query.lower().split())
        scored=[]
        for item in self.items:
            text=item.get("text","").lower()
            score=sum(1 for t in tokens if len(t)>2 and t in text)
            scored.append((score,item))
        return [dict(item, score=score) for score,item in sorted(scored, reverse=True, key=lambda x:x[0])[:k] if score>0]
