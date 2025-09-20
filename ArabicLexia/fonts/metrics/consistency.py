from .utils import calculate_mean, calculate_std_dev, get_glyph_bbox
def calculate_consistency_metrics(analyzer):
    results = {}
    raw_data = {'v_centers': [], 'latin_ascenders': [], 'latin_descenders': [], 'arabic_ascenders': [], 'arabic_descenders': []}
    LATIN_ASC_CHARS, LATIN_DESC_CHARS = "bdfhijklt", "gjpqy"
    ARABIC_ASC_CHARS, ARABIC_DESC_CHARS = "أإآادذرزطظكلف", "جحخعغرزوىقينم"
    for char_code, glyph_name in analyzer.cmap.items():
        if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
        bbox = get_glyph_bbox(analyzer.glyph_set, glyph_name)
        if bbox:
            yMin, yMax = bbox[1], bbox[3]
            raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)
            char = chr(char_code)
            is_arabic, is_latin = 0x0600 <= char_code <= 0x06FF, 0x0041 <= char_code <= 0x007A
            if is_arabic and analyzer.language_support != 'latin_only':
                if char in ARABIC_ASC_CHARS: raw_data['arabic_ascenders'].append(yMax)
                if char in ARABIC_DESC_CHARS: raw_data['arabic_descenders'].append(yMin)
            elif is_latin and analyzer.language_support != 'arabic_only':
                if char in LATIN_ASC_CHARS: raw_data['latin_ascenders'].append(yMax)
                if char in LATIN_DESC_CHARS: raw_data['latin_descenders'].append(yMin)
    def consistency(arr):
        mean_val = calculate_mean(arr)
        return calculate_std_dev(arr) / abs(mean_val) if mean_val != 0 else None
    cap_height = analyzer.metrics.get('cap_height')
    if cap_height and cap_height > 0: results['balance_consistency'] = calculate_std_dev(raw_data['v_centers']) / cap_height
    results['arabic_ascender_consistency'] = consistency(raw_data['arabic_ascenders'])
    results['arabic_descender_consistency'] = consistency(raw_data['arabic_descenders'])
    results['latin_ascender_consistency'] = consistency(raw_data['latin_ascenders'])
    results['latin_descender_consistency'] = consistency(raw_data['latin_descenders'])
    return results