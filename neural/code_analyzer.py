from typing import Dict, List, Optional

try:
    import tree_sitter
except ImportError:  # pragma: no cover
    tree_sitter = None

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
except ImportError:  # pragma: no cover
    AutoTokenizer = None
    AutoModelForSequenceClassification = None


class CodeAnalyzer:
    def __init__(self, model_name: str = "microsoft/codebert-base"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        # Lazy load: constructing the model here downloads/loads hundreds
        # of MB on every import/instantiation. Load on first analyze().

    def _ensure_model(self) -> bool:
        """Load the CodeBERT model on first use; False if unavailable."""
        if self.tokenizer is not None and self.model is not None:
            return True
        if AutoTokenizer is None or AutoModelForSequenceClassification is None:
            return False
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            return True
        except Exception:
            self.tokenizer = None
            self.model = None
            return False

    def analyze(self, code: str) -> Dict[str, Optional[str]]:
        if not self._ensure_model():
            return {"summary": "Code analysis unavailable", "risk": None}

        inputs = self.tokenizer(code, return_tensors="pt", truncation=True, max_length=512)
        outputs = self.model(**inputs)
        scores = outputs.logits.softmax(dim=-1).tolist()[0]
        return {"summary": "Code analyzed", "risk": str(max(scores))}

    def find_sinks(self, code: str) -> List[str]:
        suspicious = []
        suspects = ["exec(", "eval(", "os.system", "subprocess.Popen", "pickle.load"]
        for item in suspects:
            if item in code:
                suspicious.append(item)
        return suspicious
