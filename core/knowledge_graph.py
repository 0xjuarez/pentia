from typing import Any, Dict, List, Optional

try:
    import networkx as nx
except ImportError:  # pragma: no cover
    nx = None


class KnowledgeGraph:
    def __init__(self):
        if nx is not None:
            self.graph = nx.Graph()
        else:
            # Fallback sin networkx: los nodos van en un dict id -> (tipo,
            # atributos) y las aristas en una lista de tuplas. Un dict de
            # atributos NO puede vivir dentro de un set (dict no es hashable).
            self.graph = {"nodes": {}, "edges": []}

    def add_entity(self, entity_id: str, entity_type: str, **attributes: Any):
        if nx is not None:
            self.graph.add_node(entity_id, type=entity_type, **attributes)
        else:
            self.graph["nodes"][entity_id] = (entity_type, attributes)

    def relate(self, source: str, target: str, relation: str, **attributes: Any):
        if nx is not None:
            self.graph.add_edge(source, target, relation=relation, **attributes)
        else:
            self.graph["edges"].append((source, target, relation, attributes))

    def neighbors(self, entity_id: str) -> List[str]:
        if nx is not None:
            return list(self.graph.neighbors(entity_id))
        return [edge[1] for edge in self.graph["edges"] if edge[0] == entity_id]

    def path(self, source: str, target: str) -> Optional[List[str]]:
        if nx is None:
            return None
        try:
            return list(nx.shortest_path(self.graph, source, target))
        except Exception:
            return None

    def summary(self) -> str:
        if nx is not None:
            return f"Nodes: {self.graph.number_of_nodes()}, Edges: {self.graph.number_of_edges()}"
        return f"Nodes: {len(self.graph['nodes'])}, Edges: {len(self.graph['edges'])}"
