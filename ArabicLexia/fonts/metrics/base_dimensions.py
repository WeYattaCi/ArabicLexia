# fonts/metrics/base_dimensions.py

def _get_glyph_prop(cmap, glyph_set, char, prop):
    """دالة مساعدة آمنة لجلب خاصية من حرف معين."""
    glyph_name = cmap.get(ord(char))
    if not glyph_name or glyph_name not in glyph_set:
        return None
    glyph = glyph_set[glyph_name]
    return getattr(glyph, prop, None)

def calculate_base_dimensions(analyzer):
    """
    تحسب الأبعاد الأساسية للخط بوحدات الخط الأولية (FUnits).
    """
    font = analyzer.font
    results = {}
    
    os2 = font.get('OS/2')
    hhea = font.get('hhea')
    
    # --- تم إزالة القسمة على units_per_em من جميع الحسابات ---

    results['ascender_height'] = hhea.ascender if hhea and hasattr(hhea, 'ascender') else None
    results['descender_depth'] = abs(hhea.descender) if hhea and hasattr(hhea, 'descender') else None
    
    # حساب ارتفاع الحرف الكبير (Cap Height)
    cap_height_units = None
    if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight:
        cap_height_units = os2.sCapHeight
    else: 
        cap_height_units = _get_glyph_prop(analyzer.cmap, analyzer.glyph_set, 'H', 'yMax')
    
    results['cap_height'] = cap_height_units

    # حساب ارتفاع حرف x (x-height)
    x_height_units = None
    if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight:
        x_height_units = os2.sxHeight
    else:
        x_height_units = _get_glyph_prop(analyzer.cmap, analyzer.glyph_set, 'x', 'yMax')

    results['x_height'] = x_height_units
    
    # حساب نسبة ارتفاع x
    # (هذا المعيار الوحيد الذي يبقى نسبة مئوية)
    if x_height_units is not None and cap_height_units and cap_height_units > 0:
        results['xheight_ratio'] = x_height_units / cap_height_units
    else:
        results['xheight_ratio'] = None

    return results