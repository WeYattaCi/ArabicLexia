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
    تحسب الأبعاد الأساسية للخط مثل ارتفاع الصواعد والهوابط وارتفاع حرف x.
    """
    font = analyzer.font
    results = {}
    
    units_per_em = font['head'].unitsPerEm
    os2 = font.get('OS/2')
    hhea = font.get('hhea')
    
    results['ascender_height'] = hhea.ascender / units_per_em if hhea else None
    results['descender_depth'] = abs(hhea.descender / units_per_em) if hhea else None
    
    cap_height_units = (os2.sCapHeight if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else 
                        _get_glyph_prop(analyzer.cmap, analyzer.glyph_set, 'H', 'yMax'))
    
    results['cap_height'] = (cap_height_units / units_per_em) if cap_height_units is not None else results.get('ascender_height')

    x_height_units = (os2.sxHeight if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else
                      _get_glyph_prop(analyzer.cmap, analyzer.glyph_set, 'x', 'yMax'))

    results['x_height'] = (x_height_units / units_per_em) if x_height_units is not None else None
    
    cap_height_for_ratio = (results.get('cap_height') or 0) * units_per_em
    if x_height_units is not None and cap_height_for_ratio > 0:
        results['xheight_ratio'] = x_height_units / cap_height_for_ratio
    else:
        results['xheight_ratio'] = None

    return results
