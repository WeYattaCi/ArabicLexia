# fonts/metrics/special_metrics.py
from .utils import calculate_mean

def _calculate_kerning_coverage(font, pairs):
    """دالة مساعدة لحساب تغطية التقنين."""
    cmap = font.getBestCmap()
    if not cmap: return 0.0

    # التحقق من جدول التقنين الحديث (GPOS)
    if 'GPOS' in font and hasattr(font['GPOS'].table.FeatureList, "FeatureRecord"):
        for feature in font['GPOS'].table.FeatureList.FeatureRecord:
            if feature.FeatureTag == 'kern':
                return 1.0 
    
    # -- هذا هو الجزء الذي تم إصلاحه --
    # التحقق من جدول التقنين القديم (kern)
    if 'kern' in font and hasattr(font['kern'], 'kernTables') and font['kern'].kernTables:
        kern_table = font['kern'].kernTables[0]
        if hasattr(kern_table, 'kernTable'):
            kerning_data = kern_table.kernTable
            glyph_pairs = []
            for char1, char2 in pairs:
                g1 = cmap.get(ord(char1))
                g2 = cmap.get(ord(char2))
                if g1 and g2:
                    glyph_pairs.append((g1, g2))
            
            if not glyph_pairs: return 0.0
            found_pairs = sum(1 for g1, g2 in glyph_pairs if (g1, g2) in kerning_data)
            return found_pairs / len(glyph_pairs)
            
    return 0.0


def calculate_special_metrics(analyzer):
    """
    تحسب المعايير الخاصة مثل التقنين، التشكيل، ونسبة عرض المسافة.
    """
    results = {}
    font = analyzer.font
    cmap = analyzer.cmap
    hmtx = analyzer.hmtx

    results['score_for_sans_serif'] = 1.0 if analyzer.font_type == 'sans-serif' else 0.0
    results['score_for_serif'] = 1.0 if analyzer.font_type == 'serif' else 0.0
    
    LATIN_KERN_PAIRS = [('A', 'V'), ('T', 'o'), ('V', 'a'), ('Y', 'o'), ('W', 'a')]
    ARABIC_KERN_PAIRS = [('ل', 'ا'), ('ف', 'ي'), ('و', 'ا'), ('ق', 'ا'), ('ع', 'ل')]
    results['latin_kerning_quality'] = _calculate_kerning_coverage(font, LATIN_KERN_PAIRS)
    results['arabic_kerning_quality'] = _calculate_kerning_coverage(font, ARABIC_KERN_PAIRS)
    
    diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
    found = sum(1 for d in diacritics if cmap and cmap.get(ord(d)))
    results['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0
    
    space_width = None
    try:
        space_glyph_name = cmap.get(32)
        space_width = hmtx[space_glyph_name][0]
    except (KeyError, TypeError):
        space_width = None

    mean_width = calculate_mean(analyzer.raw_data['all_widths'])
    results['space_width_ratio'] = (space_width / mean_width) if space_width is not None and mean_width else None
    
    return results