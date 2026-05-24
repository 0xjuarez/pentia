from typing import Dict, List, Optional

try:
    import numpy as np
    from sklearn.cluster import DBSCAN, KMeans
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:  # pragma: no cover
    np = None
    DBSCAN = None
    KMeans = None
    TfidfVectorizer = None


class IOCClusterer:
    def __init__(self, method: str = "dbscan", eps: float = 0.5, min_samples: int = 2):
        self.method = method
        self.eps = eps
        self.min_samples = min_samples

    def _vectorize(self, items: List[str]):
        if TfidfVectorizer is None:
            raise RuntimeError("Scikit-learn is required for IOC clustering")
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5))
        return vectorizer.fit_transform(items)

    def cluster(self, iocs: List[str]) -> Dict[str, Optional[List[int]]]:
        if self.method == "kmeans" and KMeans is not None:
            matrix = self._vectorize(iocs)
            model = KMeans(n_clusters=min(5, len(iocs)))
            labels = model.fit_predict(matrix)
        elif DBSCAN is not None:
            matrix = self._vectorize(iocs)
            model = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric="cosine")
            labels = model.fit_predict(matrix)
        else:
            labels = [-1] * len(iocs)

        clusters = {}
        for item, label in zip(iocs, labels):
            clusters.setdefault(str(label), []).append(item)
        return {"labels": labels, "clusters": clusters}
