"""Phase 1: graph তৈরি আর hotspot mapping এর test।"""
import networkx as nx
import osmnx as ox
import pytest

from app.config import GRAPH_PATH, HOTSPOT_FLAGS, load_hotspots, load_weights
from app.geo import haversine_m
from app.graph_store import load_graph
from scripts.map_hotspots import apply_hotspots
from scripts.prepare_graph import annotate, normalize_highway

W = load_weights()
SPEEDS = W["road_speeds_kmh"]


def tiny_graph() -> nx.MultiDiGraph:
    """তিনটা node: A–B ~১১০ m, B–C ~১১০ m, পূর্ব দিকে।"""
    g = nx.MultiDiGraph(crs="epsg:4326")
    g.add_node(1, y=23.7500, x=90.4000)
    g.add_node(2, y=23.7500, x=90.4011)
    g.add_node(3, y=23.7500, x=90.4022)
    g.add_edge(1, 2, length=112.0, highway="primary")
    g.add_edge(2, 3, length=112.0, highway=["residential", "secondary_link"])
    g.add_edge(3, 2, length=112.0, highway="living_street")
    return g


class TestNormalizeHighway:
    def test_plain(self):
        assert normalize_highway("primary", SPEEDS) == "primary"

    def test_link_maps_to_parent(self):
        assert normalize_highway("trunk_link", SPEEDS) == "trunk"

    def test_list_takes_fastest(self):
        assert normalize_highway(["residential", "primary", "secondary"], SPEEDS) == "primary"

    def test_unknown_kept(self):
        assert normalize_highway("unclassified", SPEEDS) == "unclassified"


class TestAnnotate:
    def test_attributes(self):
        g = tiny_graph()
        annotate(g, W)
        e12, e23, e32 = g.edges[1, 2, 0], g.edges[2, 3, 0], g.edges[3, 2, 0]
        assert e12["v_free_kmh"] == SPEEDS["primary"] and e12["road_class"] == "main"
        assert e23["highway"] == "secondary" and e23["road_class"] == "main"
        assert e32["v_free_kmh"] == SPEEDS["default"] and e32["road_class"] == "local"
        assert e12["length_m"] == 112.0
        assert all(e12[f] is False for f in HOTSPOT_FLAGS.values())

    def test_v_max_is_fastest_edge(self):
        g = tiny_graph()
        annotate(g, W)
        assert g.graph["v_max_kmh"] == SPEEDS["primary"]

    def test_graphml_roundtrip_keeps_types(self, tmp_path):
        g = tiny_graph()
        annotate(g, W)
        apply_hotspots(g, [{"id": "x", "type": "crime", "lat": 23.75, "lng": 90.40055, "radius_m": 30}])
        path = tmp_path / "g.graphml"
        ox.save_graphml(g, path)
        g2 = load_graph(path)
        e = g2.edges[1, 2, 0]
        assert e["crime_hotspot"] is True and e["flood_hotspot"] is False
        assert isinstance(e["v_free_kmh"], float)
        assert isinstance(g2.graph["v_max_kmh"], float)


class TestApplyHotspots:
    def test_only_edges_with_midpoint_in_radius(self):
        g = tiny_graph()
        annotate(g, W)
        # edge 1→2 এর মাঝখান (90.40055) এর ঠিক উপর, ৩০ m radius
        matched = apply_hotspots(g, [{"id": "f", "type": "flood", "lat": 23.75, "lng": 90.40055, "radius_m": 30}])
        assert matched == {"f": 1}
        assert g.edges[1, 2, 0]["flood_hotspot"] is True
        assert g.edges[2, 3, 0]["flood_hotspot"] is False

    def test_rerun_resets_old_flags(self):
        g = tiny_graph()
        annotate(g, W)
        apply_hotspots(g, [{"id": "f", "type": "flood", "lat": 23.75, "lng": 90.40055, "radius_m": 30}])
        apply_hotspots(g, [])
        assert not any(d["flood_hotspot"] for _, _, d in g.edges(data=True))


def test_hotspots_json_is_valid():
    hotspots = load_hotspots()
    ids = [h["id"] for h in hotspots]
    assert len(ids) == len(set(ids)), "hotspot id duplicate"
    for h in hotspots:
        assert h["radius_m"] > 0
        assert h["source"].startswith("https://")
        b = W["graph_area"]["bbox"]
        assert b["south"] <= h["lat"] <= b["north"] and b["west"] <= h["lng"] <= b["east"], h["id"]


@pytest.fixture(scope="module")
def g():
    return load_graph()


@pytest.mark.skipif(not GRAPH_PATH.exists(), reason="dhaka_drive.graphml নেই; prepare_graph.py চালাও")
class TestRealGraph:
    def test_strongly_connected(self, g):
        assert nx.is_strongly_connected(g)

    def test_v_max_matches_edges(self, g):
        assert g.graph["v_max_kmh"] == max(d["v_free_kmh"] for _, _, d in g.edges(data=True))

    def test_speeds_and_lengths_positive(self, g):
        for _, _, d in g.edges(data=True):
            assert d["v_free_kmh"] > 0 and d["length_m"] > 0

    def test_length_not_shorter_than_straight_line(self, g):
        # A* এর heuristic admissible থাকার শর্ত: কোনো edge সরলরেখার চেয়ে ছোট না
        worst = 0.0
        for u, v, d in g.edges(data=True):
            straight = haversine_m(g.nodes[u]["y"], g.nodes[u]["x"], g.nodes[v]["y"], g.nodes[v]["x"])
            worst = max(worst, straight - d["length_m"])
        assert worst <= 0.01, f"একটা edge সরলরেখার চেয়ে {worst:.3f} m ছোট"

    def test_every_hotspot_type_flags_edges(self, g):
        for flag in HOTSPOT_FLAGS.values():
            assert any(d[flag] for _, _, d in g.edges(data=True)), f"{flag} কোনো edge এ নেই"
