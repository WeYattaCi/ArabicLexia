# fonts/metrics/special_metrics.py
# (This file is stable, ensure you have this version)
from .utils import calculate_mean
def count_kerning_pairs(font):
    total_pairs = 0
    if 'GPOS' in font and hasattr(font['GPOS'].table, 'LookupList') and font['GPOS'].table.LookupList:
        for lookup in font['GPOS'].table.LookupList.Lookup:
            if lookup.LookupType == 2 and hasattr(lookup, 'SubTable'):
                for subtable in lookup.SubTable:
                    if hasattr(subtable, 'PairSet'): total_pairs += sum(len(ps.PairValueRecord) for ps in subtable.PairSet)
    return total_pairs
def calculate_special_metrics(analyzer):
    results = {}
    kerning_pairs_count = count_kerning_pairs(analyzer.font)
    results['kerning_quality'] = kerning_pairs_count
    diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
    found = sum(1 for d in diacritics if analyzer.cmap and analyzer.cmap.get(ord(d)))
    results['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0
    space_width = None
    try: space_width = analyzer.hmtx[analyzer.cmap.get(32)][0]
    except Exception: pass
    mean_width = calculate_mean(analyzer.raw_data['widths'])
    results['space_width_ratio'] = (space_width / mean_width) if space_width is not None and mean_width else None
    return results