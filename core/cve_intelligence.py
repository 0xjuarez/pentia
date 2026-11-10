import asyncio
import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .cve_engine import parse_nvd_item as _parse_nvd_item
from .memory import MemoryStore


class CVEIntelligence:
    def __init__(self, memory: Optional[MemoryStore] = None):
        self.memory = memory or MemoryStore(collection_name="cve_intel")

    @staticmethod
    def parse_nvd_item(item: Dict[str, Any]) -> Dict[str, Any]:
        # NVD 2.0 first (vulnerabilities[].cve.id/descriptions/metrics),
        # legacy 1.x schema as fallback. Shared with core.cve_engine.
        parsed = _parse_nvd_item(item)
        return {
            "id": parsed.get("id") or "unknown",
            "summary": parsed.get("description") or "",
            "cvss": parsed.get("cvss"),
            "references": parsed.get("references") or [],
            "source": "nvd",
        }

    async def ingest_nvd_file(self, path: str) -> int:
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"NVD file not found: {path}")

        with open(path_obj, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        # NVD 2.0 feeds use "vulnerabilities"; legacy 1.x feeds use "CVE_Items".
        items = payload.get("vulnerabilities") or payload.get("CVE_Items") or []
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
        # ExploitDB files_exploits.csv is comma-delimited with columns:
        # id,file,description,date,author,type,platform,port
        with open(path_obj, "r", encoding="utf-8", errors="ignore", newline="") as handle:
            for row in csv.reader(handle, delimiter=","):
                if len(row) < 4:
                    continue
                if row[0].strip().lower() == "id":
                    continue  # header row
                exploit_id, file_field, description, date = (
                    row[0].strip(), row[1].strip(), row[2].strip(), row[3].strip(),
                )
                if not exploit_id:
                    continue
                text = f"ExploitDB {exploit_id}: {description}"
                metadata = {"id": exploit_id, "source": "exploitdb", "url": file_field, "date": date}
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
