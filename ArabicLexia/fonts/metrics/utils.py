# fonts/metrics/utils.py
import numpy as np
def calculate_mean(arr): return np.mean(arr) if arr and len(arr) > 1 else 0
def calculate_std_dev(arr): return np.std(arr) if arr and len(arr) > 1 else 0
def get_glyph_bbox(glyph_set, glyph_name):
    try:
        glyph = glyph_set[glyph_name]
        pen = glyph.getPen(); glyph.draw(pen)
        return pen.getbbox()
    except Exception: return None