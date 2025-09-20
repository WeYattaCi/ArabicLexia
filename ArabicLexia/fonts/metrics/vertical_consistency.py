# fonts/metrics/vertical_consistency.py
from .utils import get_glyph_bbox, calculate_mean, calculate_std_dev

def calculate_vertical_consistency(analyzer):
    results = {}
    v_centers = []
    arabic_ascenders, arabic_descenders = [], []
    latin_ascenders, latin_descenders = [], []

    # قوائم حروف شاملة لضمان العثور على البيانات
    LATIN_ASC_CHARS = "bdfhijklt"
    LATIN_DESC_CHARS = "gjpqy"
    ARABIC_ASC_CHARS = "أإآادذرزطظكلف"
    ARABIC_DESC_CHARS = "جحخعغرزوىقينم"
    
    for char_code, glyph_name in analyzer.cmap.items():
        bbox = get_glyph_bbox(analyzer.glyph_set, glyph_name)
        if bbox:
            xMin, yMin, xMax, yMax = bbox
            v_centers.append(yMin + (yMax - yMin) / 2)

            char = chr(char_code)
            is_arabic = 0x0600 <= char_code <= 0x06FF
            is_latin = 0x0041 <= char_code <= 0x007A

            if is_arabic and analyzer.language_support != 'latin_only':
                if char in ARABIC_ASC_CHARS: arabic_ascenders.append(yMax)
                if char in ARABIC_DESC_CHARS: arabic_descenders.append(yMin)
            
            elif is_latin and analyzer.language_support != 'arabic_only':
                if char in LATIN_ASC_CHARS: latin_ascenders.append(yMax)
                if char in LATIN_DESC_CHARS: latin_descenders.append(yMin)

    def consistency(arr):
        mean_val = calculate_mean(arr)
        return calculate_std_dev(arr) / abs(mean_val) if mean_val != 0 else None

    cap_height = analyzer.metrics.get('cap_height')
    if cap_height and cap_height > 0:
        results['balance_consistency'] = calculate_std_dev(v_centers) / cap_height
    
    results['arabic_ascender_consistency'] = consistency(arabic_ascenders)
    results['arabic_descender_consistency'] = consistency(arabic_descenders)
    results['latin_ascender_consistency'] = consistency(latin_ascenders)
    results['latin_descender_consistency'] = consistency(latin_descenders)

    return results