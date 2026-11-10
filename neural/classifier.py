import asyncio
import math
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import pefile
except ImportError:  # pragma: no cover
    pefile = None

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None

try:
    from sklearn.ensemble import RandomForestClassifier
except ImportError:  # pragma: no cover
    RandomForestClassifier = None


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    # Single pass with Counter: the old {b: data.count(b) for b in set(data)}
    # re-scanned the whole buffer once per unique byte (O(256·n)).
    freq = Counter(data)
    ent = 0.0
    for count in freq.values():
        p = count / len(data)
        ent -= p * math.log2(p)
    return ent


def extract_strings(data: bytes, min_length: int = 4) -> List[str]:
    pattern = re.compile(rb"[ -~]{%d,}" % min_length)
    return [s.decode(errors="ignore") for s in pattern.findall(data)]


class MalwareClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or ".pentia_malware_classifier.model"
        self.model = self._load_model()

    def _load_model(self):
        if lgb is not None and Path(self.model_path).exists():
            try:
                return lgb.Booster(model_file=self.model_path)
            except Exception:
                pass
        if RandomForestClassifier is not None:
            return RandomForestClassifier(n_estimators=50, random_state=42)
        return None

    async def classify_sample(self, sample_path: str) -> Dict[str, Any]:
        if pefile is None:
            return {"status": "fallback", "reason": "pefile not installed"}

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=2) as executor:
            pe = await loop.run_in_executor(executor, pefile.PE, sample_path)

        features = self.extract_features(sample_path, pe)
        prediction = self.predict(features)
        return {
            "sample": Path(sample_path).name,
            "features": features,
            "prediction": prediction,
        }

    def extract_features(self, sample_path: str, pe) -> Dict[str, Any]:
        features: Dict[str, Any] = {}
        try:
            features["sections"] = len(pe.sections)
            features["imports"] = sum(len(entry.imports) for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []))
            features["entropy_avg"] = sum(getattr(section, "entropy", 0.0) for section in pe.sections) / max(1, len(pe.sections))
            features["has_dotnet"] = any(section.Name.rstrip(b"\x00").decode(errors="ignore").lower().startswith(".net") for section in pe.sections)
            features["size"] = Path(sample_path).stat().st_size
            features["is_packed"] = any(section.Name.rstrip(b"\x00").decode(errors="ignore").lower() in {"upx0", "aspack", "petite", "themida"} for section in pe.sections)
        except Exception:
            features["sections"] = 0
            features["imports"] = 0
            features["entropy_avg"] = 0.0
            features["has_dotnet"] = False
            features["size"] = 0
            features["is_packed"] = False

        try:
            data = pe.write()
            features["file_entropy"] = entropy(data)
            features["string_count"] = len(extract_strings(data))
        except Exception:
            features["file_entropy"] = 0.0
            features["string_count"] = 0

        try:
            features["import_names"] = [imp.name.decode(errors="ignore") for entry in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []) for imp in entry.imports]
        except Exception:
            features["import_names"] = []

        return features

    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        vector = [
            float(features.get("sections", 0)),
            float(features.get("imports", 0)),
            float(features.get("entropy_avg", 0.0)),
            float(features.get("file_entropy", 0.0)),
            float(features.get("string_count", 0)),
            float(features.get("is_packed", False)),
        ]

        if self.model is not None:
            try:
                if lgb is not None and hasattr(self.model, "predict"):
                    raw = self.model.predict([vector])
                    label = int(raw[0])
                    return {"label": str(label), "confidence": 0.75}
                if RandomForestClassifier is not None and hasattr(self.model, "predict_proba"):
                    probs = self.model.predict_proba([vector])[0]
                    label = int(probs.argmax())
                    return {"label": str(label), "confidence": float(max(probs))}
            except Exception:
                pass

        label = "unknown"
        if features.get("is_packed") or features.get("file_entropy", 0.0) > 7.5:
            label = "loader/crypter"
        elif features.get("imports", 0) > 50 and features.get("entropy_avg", 0.0) > 5.5:
            label = "ransomware/stealer"
        elif features.get("imports", 0) < 10:
            label = "dropper/loader"

        return {"label": label, "confidence": 0.55}

    def fit(self, feature_list: List[Dict[str, Any]], labels: List[int]):
        if self.model is None:
            return
        vectors = []
        for features in feature_list:
            vectors.append([
                float(features.get("sections", 0)),
                float(features.get("imports", 0)),
                float(features.get("entropy_avg", 0.0)),
                float(features.get("file_entropy", 0.0)),
                float(features.get("string_count", 0)),
                float(features.get("is_packed", False)),
            ])
        if lgb is not None and isinstance(self.model, lgb.Booster):
            # A LightGBM Booster has no .fit (AttributeError): train a new
            # Booster via the module-level lgb.train and persist it.
            dataset = lgb.Dataset(vectors, label=labels)
            self.model = lgb.train({}, dataset)
            self.model.save_model(self.model_path)
        elif hasattr(self.model, "fit"):
            self.model.fit(vectors, labels)
        else:
            raise RuntimeError(
                f"Cannot train model of type {type(self.model).__name__}: "
                "no .fit method and not a LightGBM Booster"
            )
