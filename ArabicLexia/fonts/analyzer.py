# fonts/analyzer.py
import sys
import json
import numpy as np
from fontTools.ttLib import TTFont
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def calculate_mean(arr):
    return np.mean(arr) if arr and len(arr) > 0 else None

def calculate_std_dev(arr):
    return np.std(arr) if arr and len(arr) > 1 else 0

class FontAnalyzer:
    def __init__(self, font_path, font_type):
        self.font = TTFont(font_path)
        self.font_type = font_type
        self.metrics = {}
        self.glyph_set = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font['hmtx']
        
        self.raw_data = {
            'latin_widths': [], 'arabic_widths': [], 'all_widths': [],
            'latin_ascenders': [], 'arabic_ascenders': [],
            'latin_descenders': [], 'arabic_descenders': [],
            'vertical_centers': [], 'left_side_bearings': [], 'right_side_bearings': [],
            'initial_widths': [], 'medial_widths': [], 'final_widths': []
        }
        self._map_positional_glyphs()

    def analyze(self):
        self._gather_raw_data()
        self._calculate_basic_dimensions()
        self._calculate_consistency_metrics()
        self._calculate_special_metrics()
        return {k: (None if v is None or (isinstance(v, float) and np.isnan(v)) else v) for k, v in self.metrics.items()}

    def _get_glyph_prop(self, char, prop):
        glyph_name = self.cmap.get(ord(char))
        if not glyph_name or glyph_name not in self.glyph_set: return None
        glyph = self.glyph_set[glyph_name]
        return getattr(glyph, prop, None)

    def _map_positional_glyphs(self):
        self.positional_map = {'init': {}, 'medi': {}, 'fina': {}}
        if 'GSUB' not in self.font: return
        gsub = self.font['GSUB'].table
        if not hasattr(gsub.FeatureList, "FeatureRecord"): return
        features = {f.FeatureTag: f.Feature for f in gsub.FeatureList.FeatureRecord}
        for tag in self.positional_map.keys():
            if tag in features:
                for lookup_index in features[tag].LookupListIndex:
                    lookup = gsub.LookupList.Lookup[lookup_index]
                    for subtable in lookup.SubTable:
                        if subtable.LookupType == 1:
                            for base, variant in subtable.mapping.items():
                                self.positional_map[tag][base] = variant

    def _gather_raw_data(self):
        if not self.cmap: return
        
        ARABIC_ASC_CHARS = "أإآطظكلام"
        ARABIC_DESC_CHARS = "جحخعغرزوى"
        LATIN_ASC_CHARS = "bdfhkl"
        LATIN_DESC_CHARS = "gjpqy"

        for char_code, glyph_name in self.cmap.items():
            # -- الإصلاح النهائي: التحقق من صلاحية اسم الحرف --
            if not isinstance(glyph_name, str) or glyph_name == ".notdef":
                continue
            
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                glyph = self.glyph_set[glyph_name]
                
                self.raw_data['all_widths'].append(advance_width)
                self.raw_data['left_side_bearings'].append(lsb)
                if hasattr(glyph, 'xMin') and hasattr(glyph, 'xMax'):
                    self.raw_data['right_side_bearings'].append(advance_width - lsb - (glyph.xMax - glyph.xMin))
                if hasattr(glyph, 'yMin') and hasattr(glyph, 'yMax'):
                    self.raw_data['vertical_centers'].append(glyph.yMin + (glyph.yMax - glyph.yMin) / 2)

                is_arabic = 0x0600 <= char_code <= 0x06FF
                is_latin = (0x0041 <= char_code <= 0x005A) or (0x0061 <= char_code <= 0x007A)
                char = chr(char_code)

                if is_latin:
                    self.raw_data['latin_widths'].append(advance_width)
                    if char in LATIN_ASC_CHARS and hasattr(glyph, 'yMax'): self.raw_data['latin_ascenders'].append(glyph.yMax)
                    if char in LATIN_DESC_CHARS and hasattr(glyph, 'yMin'): self.raw_data['latin_descenders'].append(glyph.yMin)
                elif is_arabic:
                    self.raw_data['arabic_widths'].append(advance_width)
                    if char in ARABIC_ASC_CHARS and hasattr(glyph, 'yMax'): self.raw_data['arabic_ascenders'].append(glyph.yMax)
                    if char in ARABIC_DESC_CHARS and hasattr(glyph, 'yMin'): self.raw_data['arabic_descenders'].append(glyph.yMin)
                    
                    if glyph_name in self.positional_map['init']: self.raw_data['initial_widths'].append(self.hmtx[self.positional_map['init'][glyph_name]][0])
                    if glyph_name in self.positional_map['medi']: self.raw_data['medial_widths'].append(self.hmtx[self.positional_map['medi'][glyph_name]][0])
                    if glyph_name in self.positional_map['fina']: self.raw_data['final_widths'].append(self.hmtx[self.positional_map['fina'][glyph_name]][0])
            except (KeyError, AttributeError, TypeError):
                continue

    def _calculate_basic_dimensions(self):
        units_per_em = self.font['head'].unitsPerEm
        os2 = self.font.get('OS/2')
        hhea = self.font.get('hhea')
        
        self.metrics['ascender_height'] = hhea.ascender / units_per_em if hhea else None
        self.metrics['descender_depth'] = abs(hhea.descender / units_per_em) if hhea else None
        self.metrics['cap_height'] = os2.sCapHeight / units_per_em if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else self.metrics.get('ascender_height')
        
        x_height_val = (os2.sxHeight if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else self._get_glyph_prop('x', 'yMax')) or 0
        self.metrics['x_height'] = x_height_val / units_per_em if x_height_val else None
        
        cap_height_funits = (self.metrics.get('cap_height') or 0) * units_per_em
        self.metrics['xheight_ratio'] = (x_height_val / cap_height_funits) if cap_height_funits and x_height_val > 0 else None

    def _calculate_consistency_metrics(self):
        def consistency_score(data_list):
            mean = calculate_mean(data_list)
            return (calculate_std_dev(data_list) / mean) if mean and mean > 0 else None

        self.metrics['width_consistency'] = consistency_score(self.raw_data['all_widths'])
        cap_height_funits = (self.metrics.get('cap_height') or 0) * self.font['head'].unitsPerEm
        self.metrics['balance_consistency'] = (calculate_std_dev(self.raw_data['vertical_centers']) / cap_height_funits) if cap_height_funits and cap_height_funits > 0 else None
        self.metrics['sidebearing_consistency'] = consistency_score(self.raw_data['left_side_bearings'] + self.raw_data['right_side_bearings'])
        
        self.metrics['latin_ascender_consistency'] = consistency_score(self.raw_data['latin_ascenders'])
        self.metrics['arabic_ascender_consistency'] = consistency_score(self.raw_data['arabic_ascenders'])
        self.metrics['latin_descender_consistency'] = consistency_score([abs(d) for d in self.raw_data['latin_descenders']])
        self.metrics['arabic_descender_consistency'] = consistency_score([abs(d) for d in self.raw_data['arabic_descenders']])
        
        self.metrics['isolated_consistency'] = consistency_score(self.raw_data['arabic_widths'])
        self.metrics['initial_consistency'] = consistency_score(self.raw_data['initial_widths'])
        self.metrics['medial_consistency'] = consistency_score(self.raw_data['medial_widths'])
        self.metrics['final_consistency'] = consistency_score(self.raw_data['final_widths'])

    def _calculate_kerning_coverage(self, pairs):
        if 'kern' not in self.font or not self.font['kern'].tables: return 0.0
        kern_table = self.font['kern'].tables[0]
        if not kern_table.kernTables: return 0.0
        kerning_data = kern_table.kernTables[0].kernTable
        
        glyph_pairs = []
        for char1, char2 in pairs:
            g1 = self.cmap.get(ord(char1))
            g2 = self.cmap.get(ord(char2))
            if g1 and g2:
                glyph_pairs.append((g1, g2))
        
        if not glyph_pairs: return 0.0
        found_pairs = sum(1 for g1, g2 in glyph_pairs if (g1, g2) in kerning_data)
        return found_pairs / len(glyph_pairs)

    def _calculate_special_metrics(self):
        self.metrics['score_for_sans_serif'] = 1.0 if self.font_type == 'sans-serif' else 0.0
        self.metrics['score_for_serif'] = 1.0 if self.font_type == 'serif' else 0.0
        
        LATIN_KERN_PAIRS = [('A', 'V'), ('T', 'o'), ('V', 'a'), ('Y', 'o'), ('W', 'a')]
        ARABIC_KERN_PAIRS = [('ل', 'ا'), ('ف', 'ي'), ('و', 'ا'), ('ق', 'ا'), ('ع', 'ل')]
        self.metrics['latin_kerning_quality'] = self._calculate_kerning_coverage(LATIN_KERN_PAIRS)
        self.metrics['arabic_kerning_quality'] = self._calculate_kerning_coverage(ARABIC_KERN_PAIRS)
        
        diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
        found = sum(1 for d in diacritics if self.cmap and self.cmap.get(ord(d)))
        self.metrics['diacritic_consistency'] = found / len(diacritics) if diacritics else 0.0
        
        space_glyph_name = self.cmap.get(32)
        space_width = self.hmtx[space_glyph_name][0] if space_glyph_name and space_glyph_name in self.hmtx else None
        mean_width = calculate_mean(self.raw_data['all_widths'])
        self.metrics['space_width_ratio'] = (space_width / mean_width) if space_width is not None and mean_width else None

    def generate_width_histogram(self, output_dir, font_id, font_name):
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        plt.figure(figsize=(10, 6))
        plt.hist(self.raw_data['all_widths'], bins=50, color='teal', edgecolor='black')
        plt.title(f'Glyph Width Distribution for: {font_name}')
        plt.xlabel('Glyph Advance Width (FUnits)')
        plt.ylabel('Frequency')
        plt.grid(True, linestyle='--', alpha=0.6)
        file_path = os.path.join(output_dir, f'width_histogram_{font_id}.png')
        plt.savefig(file_path)
        plt.close()
        return file_path