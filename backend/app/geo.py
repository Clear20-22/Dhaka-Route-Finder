"""Haversine দূরত্ব। Heuristic আর hotspot mapping দুটোই এটা ব্যবহার করে।"""
import numpy as np

EARTH_RADIUS_M = 6_371_008.8


def haversine_m(lat1, lng1, lat2, lng2):
    """দুই বিন্দুর great-circle দূরত্ব মিটারে। Scalar বা numpy array দুটোই চলে।"""
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lng2 - lng1) / 2) ** 2)
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(a))
