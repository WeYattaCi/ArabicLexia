# fonts/metrics/base_dimensions.py

def _get_glyph_bbox_prop(cmap, glyph_set, char, prop_index, is_abs=False):
    """
    دالة مساعدة آمنة لجلب إحداثيات (yMin, yMax) من حرف معين.
    prop_index: 3 for yMax, 1 for yMin
    """
    if not cmap: return None
    glyph_name = cmap.get(ord(char))
    if not glyph_name or glyph_name not in glyph_set:
        return None
    
    try:
        pen = glyph_set[glyph_name].getPen()
        bbox = pen.getbbox()
        # bbox is (xMin, yMin, xMax, yMax)
        if not bbox: return None
        value = bbox[prop_index]
        return abs(value) if is_abs else value
    except (AttributeError, TypeError):
        return None

def calculate_base_dimensions(analyzer):
    """
    تحسب الأبعاد الأساسية للخط باستخدام خوارزمية هجينة وذكية.
    """
    results = {}
    font = analyzer.font
    os2 = font.get('OS/2')
    hhea = font.get('hhea')

    # --- الطريقة الأولى (الأكثر دقة): القياس المباشر للحروف ---
    cap_height_from_glyph = _get_glyph_bbox_prop(analyzer.cmap, analyzer.glyph_set, 'H', 3)
    x_height_from_glyph = _get_glyph_bbox_prop(analyzer.cmap, analyzer.glyph_set, 'x', 3)
    ascender_from_glyph = _get_glyph_bbox_prop(analyzer.cmap, analyzer.glyph_set, 'd', 3)
    descender_from_glyph = _get_glyph_bbox_prop(analyzer.cmap, analyzer.glyph_set, 'p', 1, is_abs=True)

    # --- الطريقة الثانية (الخطة البديلة): قراءة البيانات الوصفية العامة ---
    ascender_from_meta = hhea.ascender if hhea and hasattr(hhea, 'ascender') else None
    descender_from_meta = abs(hhea.descender) if hhea and hasattr(hhea, 'descender') else None
    cap_height_from_meta = os2.sCapHeight if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else None
    x_height_from_meta = os2.sxHeight if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else None
    
    # --- القرار: استخدم القياس المباشر إن وجد، وإلا استخدم الخطة البديلة ---
    results['ascender_height'] = ascender_from_glyph or ascender_from_meta
    results['descender_depth'] = descender_from_glyph or descender_from_meta
    results['cap_height'] = cap_height_from_glyph or cap_height_from_meta or ascender_from_meta # CapHeight قد يساوي Ascender كخطة بديلة أخيرة
    results['x_height'] = x_height_from_glyph or x_height_from_meta
    
    # حساب نسبة ارتفاع x بناءً على القيم النهائية
    final_x_height = results.get('x_height')
    final_cap_height = results.get('cap_height')
    
    if final_x_height is not None and final_cap_height and final_cap_height > 0:
        results['xheight_ratio'] = final_x_height / final_cap_height
    else:
        results['xheight_ratio'] = None

    return results