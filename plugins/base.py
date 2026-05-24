import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class Plugin(ABC):
    name = "base"

    @abstractmethod
    async def run(self, target: str, **kwargs: Any) -> Dict[str, Any]:
        raise NotImplementedError


class PluginManager:
    def __init__(self, plugins: List[Plugin]):
        self.plugins = {plugin.name: plugin for plugin in plugins}

    async def run(self, name: str, target: str, **kwargs: Any) -> Dict[str, Any]:
        plugin = self.plugins.get(name)
        if plugin is None:
            raise ValueError(f"Plugin {name} not found")
        return await plugin.run(target, **kwargs)

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())
