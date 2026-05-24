from abc import ABC, abstractmethod
from typing import List, Optional

from .memory import MemoryStore


class Agent(ABC):
    def __init__(self, name: str, system_prompt: str, tools: List[str], memory: Optional[MemoryStore] = None):
        self.name = name
        self.system_prompt = system_prompt
        self.tools = tools
        self.memory = memory or MemoryStore(collection_name=f"{name.lower()}_memory")

    @abstractmethod
    async def analyze(self, data: str) -> str:
        raise NotImplementedError


class ReconAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="ReconAgent",
            system_prompt="Specialist in external reconnaissance and service discovery.",
            tools=["nmap", "whatweb", "subfinder", "nuclei", "ffuf"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"ReconAgent analysis on {data[:200]}"


class WebAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="WebAgent",
            system_prompt="Web application assessment specialist with knowledge of WordPress, APIs and HTTP services.",
            tools=["wpscan", "ffuf", "whatweb"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"WebAgent analysis on {data[:200]}"


class ADAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="ADAgent",
            system_prompt="Active Directory and Windows domain enumeration expert.",
            tools=["bloodhound", "enum4linux", "ldapsearch"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"ADAgent analysis on {data[:200]}"


class MalwareAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="MalwareAgent",
            system_prompt="Static and behavioral malware analysis specialist.",
            tools=["pefile", "yara", "strings"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"MalwareAgent analysis on {data[:200]}"


class ExploitAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="ExploitAgent",
            system_prompt="Exploit prioritization expert focused on CVEs, PoCs y caminos de exposición.",
            tools=["exploit_ranker", "cve_search", "metasploit"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"ExploitAgent ranking on {data[:200]}"


class PersistenceAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="PersistenceAgent",
            system_prompt="Persistence and post-exploitation specialist, analiza técnicas de mantenimiento de acceso.",
            tools=["persistence detection", "loot tracking"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"PersistenceAgent analysis on {data[:200]}"


class ReportAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="ReportAgent",
            system_prompt="Report generation expert for executive summaries and threat findings.",
            tools=["markdown", "html", "json"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"ReportAgent generation on {data[:200]}"


class OpsecAgent(Agent):
    def __init__(self, memory: Optional[MemoryStore] = None):
        super().__init__(
            name="OpsecAgent",
            system_prompt="Operational security evaluator for safe tooling, persistence and cover tracks.",
            tools=["opsec review"],
            memory=memory,
        )

    async def analyze(self, data: str) -> str:
        return f"OpsecAgent analysis on {data[:200]}"
