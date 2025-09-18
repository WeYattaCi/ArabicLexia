# fonts/metrics/utils.py
import numpy as np

def calculate_mean(arr):
    """يحسب المتوسط الحسابي للقائمة."""
    return np.mean(arr) if arr and len(arr) > 0 else None

def calculate_std_dev(arr):
    """يحسب الانحراف المعياري للقائمة."""
    return np.std(arr) if arr and len(arr) > 1 else 0