# fonts/metrics/special_metrics.py
from .utils import calculate_mean

def _has_kerning(font):
    if 'GPOS' in font and hasattr(font['GPOS'].table.FeatureList, "FeatureRecord"):
        for feature in font['GPOS'].table.FeatureList.FeatureRecord:
            if feature.FeatureTag == 'kern':
                return True
    if 'kern' in font and hasattr(font['kern'], 'kernTables') and font['kern'].kernTables:
        return True
    return False

def calculate_special_metrics(analyzer):
    results = {}
    font = analyzer.font
    cmap = analyzer.cmap
    
    kerning_present = _has_kerning(font)
    results['latin_kerning_quality'] = 1.0 if kerning_present and analyzer.language_support != 'arabic_only' else 0.0
    results['arabic_kerning_quality'] = 1.0 if kerning_present and analyzer.language_support != 'latin_only' else 0.0
    
    diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
    found = sum(1 for d in diacritics if cmap and cmap.get(ord(d)))
    results['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0
    
    space_width = None
    try:
        space_glyph_name = cmap.get(32)
        space_width = analyzer.hmtx[space_glyph_name][0]
    except (KeyError, TypeError):
        pass

    mean_width = calculate_mean(analyzer.raw_data['widths'])
    results['space_width_ratio'] = (space_width / mean_width) if space_width is not None and mean_width else None
    
    return results