# fonts/metrics/base_dimensions.py
from .utils import get_glyph_bbox

def calculate_base_dimensions(analyzer):
    results = {}
    hhea = analyzer.font.get('hhea')
    os2 = analyzer.font.get('OS/2')

    # الطريقة الهجينة: استخدم البيانات الوصفية كأساس، وحاول تحسينها بالقياس المباشر
    ascender = hhea.ascender if hhea else 0
    descender = abs(hhea.descender) if hhea else 0
    cap_height = os2.sCapHeight if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else ascender
    x_height = os2.sxHeight if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else 0

    # محاولة القياس المباشر للحروف اللاتينية لتحسين الدقة إن وجدت
    if analyzer.language_support != 'arabic_only':
        bbox_H = get_glyph_bbox(analyzer.glyph_set, analyzer.cmap.get(ord('H')))
        bbox_x = get_glyph_bbox(analyzer.glyph_set, analyzer.cmap.get(ord('x')))
        if bbox_H: cap_height = bbox_H[3] # yMax
        if bbox_x: x_height = bbox_x[3] # yMax
            
    results['ascender_height'] = ascender
    results['descender_depth'] = descender
    results['cap_height'] = cap_height
    results['x_height'] = x_height if x_height > 0 else None
    
    if results.get('x_height') and results.get('cap_height') and results['cap_height'] > 0:
        results['xheight_ratio'] = results['x_height'] / results['cap_height']
    else:
        results['xheight_ratio'] = None

    return results