# fonts/analyzer.py
from fontTools.ttLib import TTFont
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# --- استيراد المحللات المتخصصة ---
from .metrics.base_dimensions import calculate_base_dimensions
from .metrics.consistency import calculate_consistency_metrics
from .metrics.special_metrics import calculate_special_metrics

# --- دوال مساعدة عامة ---
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

    def _map_positional_glyphs(self):
        self.positional_map = {'init': {}, 'medi': {}, 'fina': {}}
        if 'GSUB' not in self.font: return
        gsub = self.font['GSUB'].table
        if not hasattr(gsub.FeatureList, "FeatureRecord"): return
        features = {f.FeatureTag: f.Feature for f in gsub.FeatureList.FeatureRecord}
        for tag in self.positional_map.keys():
            if tag in features and features[tag].LookupListIndex is not None:
                for lookup_index in features[tag].LookupListIndex:
                    lookup = gsub.LookupList.Lookup[lookup_index]
                    for subtable in lookup.SubTable:
                        if subtable.LookupType == 1:
                            for base, variant in subtable.mapping.items():
                                self.positional_map[tag][base] = variant
    
    def _gather_raw_data(self):
        if not self.cmap: return
        ARABIC_ASC_CHARS, ARABIC_DESC_CHARS = "أإآطظكلام", "جحخعغرزوى"
        LATIN_ASC_CHARS, LATIN_DESC_CHARS = "bdfhkl", "gjpqy"

        for char_code, glyph_name in self.cmap.items():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                glyph = self.glyph_set[glyph_name]
                
                self.raw_data['all_widths'].append(advance_width)
                if hasattr(glyph, 'yMin') and hasattr(glyph, 'yMax'):
                    self.raw_data['vertical_centers'].append(glyph.yMin + (glyph.yMax - glyph.yMin) / 2)

                char = chr(char_code)
                if 0x0600 <= char_code <= 0x06FF:
                    self.raw_data['arabic_widths'].append(advance_width)
                    if char in ARABIC_ASC_CHARS: self.raw_data['arabic_ascenders'].append(glyph.yMax)
                    if char in ARABIC_DESC_CHARS: self.raw_data['arabic_descenders'].append(glyph.yMin)
                    if glyph_name in self.positional_map['init']: self.raw_data['initial_widths'].append(self.hmtx[self.positional_map['init'][glyph_name]][0])
                    if glyph_name in self.positional_map['medi']: self.raw_data['medial_widths'].append(self.hmtx[self.positional_map['medi'][glyph_name]][0])
                    if glyph_name in self.positional_map['fina']: self.raw_data['final_widths'].append(self.hmtx[self.positional_map['fina'][glyph_name]][0])
                elif (0x0041 <= char_code <= 0x005A) or (0x0061 <= char_code <= 0x007A):
                    if char in LATIN_ASC_CHARS: self.raw_data['latin_ascenders'].append(glyph.yMax)
                    if char in LATIN_DESC_CHARS: self.raw_data['latin_descenders'].append(glyph.yMin)
            except (KeyError, AttributeError, TypeError):
                continue
    
    def analyze(self):
        self._gather_raw_data()
        
        # --- استدعاء المحللات وجمع النتائج ---
        self.metrics.update(calculate_base_dimensions(self))
        self.metrics.update(calculate_consistency_metrics(self))
        self.metrics.update(calculate_special_metrics(self))

        return {k: (v if not (isinstance(v, float) and np.isnan(v)) else None) for k, v in self.metrics.items()}

    def generate_width_histogram(self, output_dir, font_id, font_name):
        if not self.raw_data['all_widths']: return
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
