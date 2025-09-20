# fonts/metrics/special_metrics.py
from .utils import calculate_mean

def count_kerning_pairs(font):
    """
    يقوم بعد العدد الفعلي لأزواج التقنين في جدولي kern و GPOS.
    """
    total_pairs = 0
    # 1. عد أزواج جدول kern القديم
    if 'kern' in font and hasattr(font['kern'], 'kernTables') and font['kern'].kernTables:
        for subtable in font['kern'].kernTables:
            if hasattr(subtable, 'kernTable'):
                total_pairs += len(subtable.kernTable)
    
    # 2. عد أزواج جدول GPOS الحديث (النوع 2 هو لـ Pair Adjustment)
    if 'GPOS' in font:
        gpos = font['GPOS'].table
        if hasattr(gpos, 'LookupList') and gpos.LookupList:
            for lookup in gpos.LookupList.Lookup:
                if lookup.LookupType == 2 and hasattr(lookup, 'SubTable'):
                    for subtable in lookup.SubTable:
                        if hasattr(subtable, 'PairSet'):
                            for pair_set in subtable.PairSet:
                                total_pairs += len(pair_set.PairValueRecord)
    return total_pairs


def calculate_special_metrics(analyzer):
    results = {}
    font = analyzer.font
    cmap = analyzer.cmap
    
    kerning_pairs_count = count_kerning_pairs(font)
    
    # الآن النتيجة هي عدد الأزواج وليس مجرد 1.0
    results['latin_kerning_quality'] = kerning_pairs_count
    results['arabic_kerning_quality'] = kerning_pairs_count
    
    diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
    found = sum(1 for d in diacritics if cmap and cmap.get(ord(d)))
    results['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0
    
    space_width = None
    try:
        space_glyph_name = cmap.get(32)
        space_width = analyzer.hmtx[space_glyph_name][0]
    except (KeyError, TypeError): pass

    mean_width = calculate_mean(analyzer.raw_data['widths'])
    results['space_width_ratio'] = (space_width / mean_width) if space_width is not None and mean_width else None
    
    return results