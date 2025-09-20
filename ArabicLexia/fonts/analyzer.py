# fonts/analyzer.py (النسخة النهائية المصححة)
from fontTools.ttLib import TTFont
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as as plt
import os

class FontAnalyzer:
    def __init__(self, font_path, font_type, language_support):
        self.font = TTFont(font_path)
        self.font_type = font_type
        self.language_support = language_support
        self.metrics = {}
        self.raw_data = {
            'widths': [], 'lsbs': [], 'rsbs': [], 'v_centers': [],
            'arabic_ascenders': [], 'arabic_descenders': [], 'arabic_widths': [],
            'latin_ascenders': [], 'latin_descenders': [],
            'initial_widths': [], 'medial_widths': [], 'final_widths': []
        }
        # --- هذا هو الإصلاح: تعريف المتغيرات الأساسية هنا ---
        self.glyph_set = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font['hmtx']
        self._map_positional_glyphs()

    def _map_positional_glyphs(self):
        self.positional_map = {'init': {}, 'medi': {}, 'fina': {}}
        if 'GSUB' not in self.font or not hasattr(self.font['GSUB'].table, 'FeatureList') or not self.font['GSUB'].table.FeatureList:
            return
        features = {f.FeatureTag: f.Feature for f in self.font['GSUB'].table.FeatureList.FeatureRecord}
        for tag in self.positional_map.keys():
            if tag in features and features[tag].LookupListIndex is not None:
                for lookup_index in features[tag].LookupListIndex:
                    lookup = self.font['GSUB'].table.LookupList.Lookup[lookup_index]
                    for subtable in lookup.SubTable:
                        if subtable.LookupType == 1:
                            for base, variant in subtable.mapping.items():
                                self.positional_map[tag][base] = variant

    def _calculate_metrics(self):
        hhea = self.font.get('hhea')
        os2 = self.font.get('OS/2')
        if hhea:
            self.metrics['ascender_height'] = hhea.ascender
            self.metrics['descender_depth'] = abs(hhea.descender)
        if os2:
            self.metrics['cap_height'] = getattr(os2, 'sCapHeight', self.metrics.get('ascender_height'))
            self.metrics['x_height'] = getattr(os2, 'sxHeight', None)
            if self.metrics.get('x_height') and self.metrics.get('cap_height', 0) > 0:
                self.metrics['xheight_ratio'] = self.metrics['x_height'] / self.metrics['cap_height']
        
        def mean(arr): return np.mean(arr) if len(arr) > 1 else 0
        def std(arr): return np.std(arr) if len(arr) > 1 else 0
        def consistency(arr):
            mean_val = mean(arr)
            return std(arr) / abs(mean_val) if mean_val != 0 else None

        mean_width = mean(self.raw_data['widths'])
        if mean_width > 0:
            self.metrics['width_consistency'] = std(self.raw_data['widths']) / mean_width
            all_bearings = self.raw_data['lsbs'] + self.raw_data['rsbs']
            self.metrics['sidebearing_consistency'] = std(all_bearings) / mean_width
        
        cap_h = self.metrics.get('cap_height')
        if cap_h and cap_h > 0:
            self.metrics['balance_consistency'] = std(self.raw_data['v_centers']) / cap_h
        
        self.metrics['isolated_consistency'] = consistency(self.raw_data['arabic_widths'])
        self.metrics['initial_consistency'] = consistency(self.raw_data['initial_widths'])
        self.metrics['medial_consistency'] = consistency(self.raw_data['medial_widths'])
        self.metrics['final_consistency'] = consistency(self.raw_data['final_widths'])
        
        self.metrics['arabic_ascender_consistency'] = consistency(self.raw_data['arabic_ascenders'])
        self.metrics['arabic_descender_consistency'] = consistency(self.raw_data['arabic_descenders'])
        self.metrics['latin_ascender_consistency'] = consistency(self.raw_data['latin_ascenders'])
        self.metrics['latin_descender_consistency'] = consistency(self.raw_data['latin_descenders'])

        # Special Metrics
        kerning_pairs = 0
        if 'GPOS' in self.font and hasattr(self.font['GPOS'].table, 'LookupList') and self.font['GPOS'].table.LookupList:
            for lookup in self.font['GPOS'].table.LookupList.Lookup:
                if lookup.LookupType == 2:
                    for subtable in lookup.SubTable:
                        if hasattr(subtable, 'PairSet'):
                            kerning_pairs += sum(len(ps.PairValueRecord) for ps in subtable.PairSet)
        self.metrics['arabic_kerning_quality'] = kerning_pairs
        self.metrics['latin_kerning_quality'] = kerning_pairs

        diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
        found = sum(1 for d in diacritics if self.cmap and self.cmap.get(ord(d)))
        self.metrics['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0

    def analyze(self):
        if not self.cmap: return {}
        
        LATIN_ASC_CHARS = "bdfhijklt"
        LATIN_DESC_CHARS = "gjpqy"
        ARABIC_ASC_CHARS = "أإآادذرزطظكلف"
        ARABIC_DESC_CHARS = "جحخعغرزوىقينم"
        
        for char_code, glyph_name in self.cmap.items():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                
                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)
                
                glyph = self.glyph_set[glyph_name]
                pen = glyph.getPen()
                glyph.draw(pen)
                bbox = pen.getbbox()
                
                if bbox:
                    xMin, yMin, xMax, yMax = bbox
                    self.raw_data['rsbs'].append(advance_width - lsb - (xMax - xMin))
                    self.raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)
                    
                    char = chr(char_code)
                    is_arabic = 0x0600 <= char_code <= 0x06FF
                    is_latin = 0x0041 <= char_code <= 0x007A

                    if is_arabic:
                        if char in ARABIC_ASC_CHARS: self.raw_data['arabic_ascenders'].append(yMax)
                        if char in ARABIC_DESC_CHARS: self.raw_data['arabic_descenders'].append(yMin)
                    elif is_latin:
                        if char in LATIN_ASC_CHARS: self.raw_data['latin_ascenders'].append(yMax)
                        if char in LATIN_DESC_CHARS: self.raw_data['latin_descenders'].append(yMin)

                if 0x0600 <= char_code <= 0x06FF:
                    self.raw_data['arabic_widths'].append(advance_width)
                    if glyph_name in self.positional_map['init']: self.raw_data['initial_widths'].append(self.hmtx[self.positional_map['init'][glyph_name]][0])
                    if glyph_name in self.positional_map['medi']: self.raw_data['medial_widths'].append(self.hmtx[self.positional_map['medi'][glyph_name]][0])
                    if glyph_name in self.positional_map['fina']: self.raw_data['final_widths'].append(self.hmtx[self.positional_map['fina'][glyph_name]][0])
            except Exception:
                continue
                
        self._calculate_metrics()
        return {k: v for k, v in self.metrics.items() if v is not None}

    def generate_width_histogram(self, output_dir, font_id, font_name):
        # ... (الكود هنا لم يتغير) ...
        pass