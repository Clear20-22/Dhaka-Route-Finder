"""OSMnx দিয়ে ঢাকার drive network নামানো, edge attribute যোগ করা, GraphML এ save।

চালানো: backend/ থেকে `.venv/bin/python -m scripts.prepare_graph`
"""
import time
from collections import Counter

import networkx as nx
import osmnx as ox

from app.config import GRAPH_PATH, HOTSPOT_FLAGS, OSM_CACHE_DIR, load_weights


def normalize_highway(value, speeds: dict) -> str:
    """OSM highway tag থেকে একটা road type। List হলে সবচেয়ে দ্রুত type, `_link` হলে মূল type।"""
    types = value if isinstance(value, list) else [value]
    types = [str(t).removesuffix("_link") for t in types]
    return max(types, key=lambda t: speeds.get(t, speeds["default"]))


def annotate(g: nx.MultiDiGraph, w: dict) -> None:
    """প্রতিটা edge এ length_m, highway, v_free_kmh, road_class আর false hotspot flag; graph এ v_max_kmh।"""
    speeds = w["road_speeds_kmh"]
    main_types = set(w["main_road_types"])
    for _, _, data in g.edges(data=True):
        road_type = normalize_highway(data.get("highway", "default"), speeds)
        data["length_m"] = float(data["length"])
        data["highway"] = road_type
        data["v_free_kmh"] = float(speeds.get(road_type, speeds["default"]))
        data["road_class"] = "main" if road_type in main_types else "local"
        for flag in HOTSPOT_FLAGS.values():
            data[flag] = False                       # map_hotspots.py বসাবে
    g.graph["v_max_kmh"] = max(d["v_free_kmh"] for _, _, d in g.edges(data=True))


def download(w: dict) -> nx.MultiDiGraph:
    area = w["graph_area"]
    b = area["bbox"]
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(OSM_CACHE_DIR)
    # OSMnx 2.x: bbox = (west, south, east, north)
    g = ox.graph_from_bbox((b["west"], b["south"], b["east"], b["north"]),
                           network_type=area["network_type"])
    # One-way রাস্তা bbox এর কিনারায় কাটা পড়লে এমন node থাকে যেখান থেকে ফেরা যায় না;
    # শুধু largest strongly connected component রাখলে যেকোনো দুই node এর মধ্যে পথ থাকে।
    return ox.truncate.largest_component(g, strongly=True)


def report(g: nx.MultiDiGraph) -> None:
    print(f"Nodes: {g.number_of_nodes():,}  Edges: {g.number_of_edges():,}")
    print(f"v_max_kmh: {g.graph['v_max_kmh']}")
    counts = Counter(d["highway"] for _, _, d in g.edges(data=True))
    print("Road types:", ", ".join(f"{t}={n}" for t, n in counts.most_common()))
    classes = Counter(d["road_class"] for _, _, d in g.edges(data=True))
    print("Road class:", dict(classes))
    # Elevated Expressway OSM এ কোন tag পেয়েছে, তা দেখার জন্য
    expressway = Counter(
        d["highway"] for _, _, d in g.edges(data=True)
        if any(k in str(d.get("name", "")).lower() for k in ("expressway", "এক্সপ্রেসওয়ে"))
    )
    print("Edges named Expressway (English or Bangla) by road type:", dict(expressway) or "none")


def main() -> None:
    w = load_weights()
    t0 = time.perf_counter()
    print("OpenStreetMap থেকে নামানো হচ্ছে (প্রথমবার কয়েক মিনিট লাগতে পারে)...")
    g = download(w)
    annotate(g, w)
    GRAPH_PATH.parent.mkdir(parents=True, exist_ok=True)
    ox.save_graphml(g, GRAPH_PATH)
    report(g)
    print(f"Saved {GRAPH_PATH} in {time.perf_counter() - t0:.0f}s")


if __name__ == "__main__":
    main()
