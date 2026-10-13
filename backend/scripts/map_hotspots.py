"""hotspots.json এর প্রতিটা hotspot এর radius এর ভেতরে যেসব edge এর মাঝখান পড়ে, সেগুলোতে flag বসানো।

চালানো: backend/ থেকে `.venv/bin/python -m scripts.map_hotspots`
প্রতিবার সব flag আগে false করে আবার বসায়, তাই hotspots.json বদলে আবার চালানো যায়।
"""
import networkx as nx
import numpy as np
import osmnx as ox

from app.config import GRAPH_PATH, HOTSPOT_FLAGS, load_hotspots
from app.geo import haversine_m
from app.graph_store import load_graph


def edge_midpoints(g: nx.MultiDiGraph) -> tuple[list, np.ndarray, np.ndarray]:
    """প্রতিটা edge এর key আর রাস্তার geometry বরাবর মাঝখানের lat/lng।"""
    keys, lats, lngs = [], [], []
    for u, v, k, data in g.edges(keys=True, data=True):
        geom = data.get("geometry")
        if geom is not None:
            mid = geom.interpolate(0.5, normalized=True)
            lng, lat = mid.x, mid.y
        else:
            lng = (g.nodes[u]["x"] + g.nodes[v]["x"]) / 2
            lat = (g.nodes[u]["y"] + g.nodes[v]["y"]) / 2
        keys.append((u, v, k))
        lats.append(lat)
        lngs.append(lng)
    return keys, np.array(lats), np.array(lngs)


def apply_hotspots(g: nx.MultiDiGraph, hotspots: list[dict]) -> dict[str, int]:
    """Flag বসায়, আর প্রতিটা hotspot কয়টা edge এ পড়লো তা ফেরত দেয়।"""
    for _, _, data in g.edges(data=True):
        for flag in HOTSPOT_FLAGS.values():
            data[flag] = False
    keys, lats, lngs = edge_midpoints(g)
    matched = {}
    for h in hotspots:
        flag = HOTSPOT_FLAGS[h["type"]]
        inside = np.flatnonzero(haversine_m(lats, lngs, h["lat"], h["lng"]) <= h["radius_m"])
        for i in inside:
            u, v, k = keys[i]
            g.edges[u, v, k][flag] = True
        matched[h["id"]] = len(inside)
    return matched


def main() -> None:
    g = load_graph()
    hotspots = load_hotspots()
    matched = apply_hotspots(g, hotspots)
    ox.save_graphml(g, GRAPH_PATH)

    for h in hotspots:
        n = matched[h["id"]]
        warn = "   <-- কোনো edge পড়েনি, coordinate যাচাই করো" if n == 0 else ""
        print(f"{h['id']:<32} {n:>5} edges{warn}")
    for flag in HOTSPOT_FLAGS.values():
        total = sum(1 for _, _, d in g.edges(data=True) if d[flag])
        print(f"{flag:<18} {total:>6} edges")
    print(f"Saved {GRAPH_PATH}")


if __name__ == "__main__":
    main()
