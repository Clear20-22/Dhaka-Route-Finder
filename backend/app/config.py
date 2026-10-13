"""weights.yaml ও hotspots.json load করা। সব সংখ্যা এই file গুলো থেকে আসে, code এ না।"""
import json
from pathlib import Path

import yaml

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
WEIGHTS_PATH = DATA_DIR / "weights.yaml"
HOTSPOTS_PATH = DATA_DIR / "hotspots.json"
GRAPH_PATH = DATA_DIR / "dhaka_drive.graphml"
OSM_CACHE_DIR = DATA_DIR / "osm_cache"

# hotspots.json এর type → edge এর bool attribute
HOTSPOT_FLAGS = {
    "flood": "flood_hotspot",
    "blockade": "blockade_prone",
    "crime": "crime_hotspot",
    "accident": "accident_hotspot",
    "terminal": "terminal_zone",
}


def load_weights(path: Path = WEIGHTS_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_hotspots(path: Path = HOTSPOTS_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    hotspots = data["hotspots"]
    for h in hotspots:
        if h["type"] not in HOTSPOT_FLAGS:
            raise ValueError(f"{h['id']}: অজানা hotspot type '{h['type']}'")
    return hotspots
