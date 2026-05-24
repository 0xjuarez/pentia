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
        if AutoTokenizer is not None and AutoModelForSequenceClassification is not None:
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            except Exception:
                self.tokenizer = None
                self.model = None

    def analyze(self, code: str) -> Dict[str, Optional[str]]:
        if self.tokenizer is None or self.model is None:
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
