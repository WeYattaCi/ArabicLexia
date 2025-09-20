# fonts/metrics/utils.py
import numpy as np

def calculate_mean(arr):
    return np.mean(arr) if arr and len(arr) > 1 else 0

def calculate_std_dev(arr):
    return np.std(arr) if arr and len(arr) > 1 else 0

def get_glyph_bbox(glyph_set, glyph_name):
    try:
        glyph = glyph_set[glyph_name]
        glyph.recalcBounds(glyph_set)
        if hasattr(glyph, 'xMin'):
            return (glyph.xMin, glyph.yMin, glyph.xMax, glyph.yMax)
    except Exception:
        return None
    return None