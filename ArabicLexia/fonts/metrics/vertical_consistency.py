# fonts/metrics/vertical_consistency.py
from .utils import get_glyph_bbox, calculate_mean, calculate_std_dev

def calculate_vertical_consistency(analyzer):
    """
    وحدة متخصصة لحساب معايير الاتساق العمودي (الصواعد، الهوابط، التوازن).
    """
    results = {}
    
    # 1. تهيئة قوائم البيانات الأولية لهذه الوحدة فقط
    v_centers = []
    arabic_ascenders, arabic_descenders = [], []
    latin_ascenders, latin_descenders = [], []

    # 2. اكتشاف "المسطرة" الخاصة بالخط من القياسات الأساسية
    x_height = analyzer.metrics.get('x_height') or 0
    
    arabic_body_height = 0
    seen_glyph_name = analyzer.cmap.get(ord('س'))
    if seen_glyph_name:
        bbox = get_glyph_bbox(analyzer.glyph_set, seen_glyph_name)
        if bbox: arabic_body_height = bbox[3] # yMax

    # 3. المرور على كل الحروف لجمع البيانات العمودية فقط
    for char_code, glyph_name in analyzer.cmap.items():
        bbox = get_glyph_bbox(analyzer.glyph_set, glyph_name)
        if bbox:
            xMin, yMin, xMax, yMax = bbox
            v_centers.append(yMin + (yMax - yMin) / 2)

            char = chr(char_code)
            is_arabic = 0x0600 <= char_code <= 0x06FF
            is_latin_lc = 0x0061 <= char_code <= 0x007A # Lowercase Latin

            if is_arabic and analyzer.language_support != 'latin_only':
                if arabic_body_height > 0 and yMax > arabic_body_height * 1.1:
                    arabic_ascenders.append(yMax)
                if yMin < 0:
                    arabic_descenders.append(yMin)
            
            elif is_latin_lc and analyzer.language_support != 'arabic_only':
                if x_height > 0 and yMax > x_height * 1.05:
                    latin_ascenders.append(yMax)
                if yMin < 0:
                    latin_descenders.append(yMin)

    # 4. حساب النتائج النهائية
    def consistency(arr):
        mean_val = calculate_mean(arr)
        if mean_val != 0:
            return calculate_std_dev(arr) / abs(mean_val)
        return None

    cap_height = analyzer.metrics.get('cap_height')
    if cap_height and cap_height > 0:
        results['balance_consistency'] = calculate_std_dev(v_centers) / cap_height
    
    results['arabic_ascender_consistency'] = consistency(arabic_ascenders)
    results['arabic_descender_consistency'] = consistency(arabic_descenders)
    results['latin_ascender_consistency'] = consistency(latin_ascenders)
    results['latin_descender_consistency'] = consistency(latin_descenders)

    return results