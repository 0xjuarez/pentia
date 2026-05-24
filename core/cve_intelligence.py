import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .memory import MemoryStore


class CVEIntelligence:
    def __init__(self, memory: Optional[MemoryStore] = None):
        self.memory = memory or MemoryStore(collection_name="cve_intel")

    @staticmethod
    def parse_nvd_item(item: Dict[str, Any]) -> Dict[str, Any]:
        cve_meta = item.get("cve", {})
        cve_id = cve_meta.get("CVE_data_meta", {}).get("ID", "unknown")
        description = ""
        for desc in cve_meta.get("description", {}).get("description_data", []):
            if desc.get("lang") == "en":
                description = desc.get("value", "")
                break
        metrics = item.get("impact", {})
        base_metric = metrics.get("baseMetricV3", metrics.get("baseMetricV2", {}))
        cvss = base_metric.get("cvssV3", {}).get("baseScore") if isinstance(base_metric, dict) else None
        references = [ref.get("url") for ref in cve_meta.get("references", {}).get("reference_data", []) if ref.get("url")]
        return {
            "id": cve_id,
            "summary": description,
            "cvss": cvss,
            "references": references,
            "source": "nvd",
        }

    async def ingest_nvd_file(self, path: str) -> int:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"NVD file not found: {path}")

        with open(path_obj, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        items = payload.get("CVE_Items", [])
        documents = []
        for item in items:
            metadata = self.parse_nvd_item(item)
            text = f"{metadata['id']}: {metadata['summary']}"
            documents.append({"text": text, "metadata": metadata})

        await self.memory.ingest_documents(documents)
        return len(documents)

    async def ingest_exploitdb_file(self, path: str) -> int:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"ExploitDB file not found: {path}")

        documents = []
        with open(path_obj, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                parts = line.strip().split("\t")
                if len(parts) >= 4:
                    exploit_id, description, date, url = parts[0], parts[1], parts[2], parts[3]
                    text = f"ExploitDB {exploit_id}: {description}"
                    metadata = {"id": exploit_id, "source": "exploitdb", "url": url, "date": date}
                    documents.append({"text": text, "metadata": metadata})

        await self.memory.ingest_documents(documents)
        return len(documents)

    async def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        return await self.memory.retrieve(query, k=k)

    async def summarize(self, query: str) -> str:
        results = await self.search(query, k=5)
        lines = []
        for item in results:
            metadata = item.get("metadata", {})
            lines.append(f"{metadata.get('id', 'unknown')} - {item.get('text')} ({metadata.get('source')})")
        return "\n".join(lines)
