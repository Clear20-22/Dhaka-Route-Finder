"""Cache করা GraphML থেকে graph load আর nearest node খোঁজা।"""
from pathlib import Path

import networkx as nx
import osmnx as ox

from app.config import GRAPH_PATH, HOTSPOT_FLAGS


def _to_bool(value) -> bool:
    # GraphML এ bool string হিসেবে save হয়
    return str(value).strip().lower() == "true"


EDGE_DTYPES = {
    "length_m": float,
    "v_free_kmh": float,
    **{flag: _to_bool for flag in HOTSPOT_FLAGS.values()},
}
GRAPH_DTYPES = {"v_max_kmh": float}


def load_graph(path: Path = GRAPH_PATH) -> nx.MultiDiGraph:
    if not path.exists():
        raise FileNotFoundError(f"{path} নেই। আগে scripts/prepare_graph.py চালাও।")
    return ox.load_graphml(path, edge_dtypes=EDGE_DTYPES, graph_dtypes=GRAPH_DTYPES)


def nearest_node(g: nx.MultiDiGraph, lat: float, lng: float) -> int:
    return int(ox.distance.nearest_nodes(g, X=lng, Y=lat))
