# fonts/analyzer.py
from fontTools.ttLib import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from .metrics.base_dimensions import calculate_base_dimensions
from .metrics.consistency import calculate_consistency_metrics
from .metrics.special_metrics import calculate_special_metrics
from .metrics.vertical_consistency import calculate_vertical_consistency
from .metrics.utils import get_glyph_bbox

class FontAnalyzer:
    def __init__(self, font_path, font_type, language_support):
        self.font = TTFont(font_path)
        self.font_type = font_type
        self.language_support = language_support
        self.metrics = {}
        self.glyph_set = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.hmtx = self.font['hmtx']
        self.raw_data = {
            'widths': [], 'lsbs': [], 'rsbs': [], 
            'arabic_widths': [],
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

    def _gather_horizontal_data(self):
        if not self.cmap: return
        for glyph_name in self.cmap.values():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                
                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)

                bbox = get_glyph_bbox(self.glyph_set, glyph_name)
                if bbox:
                    xMin, yMin, xMax, yMax = bbox
                    self.raw_data['rsbs'].append(advance_width - lsb - (xMax - xMin))

                char_code = next((code for code, name in self.cmap.items() if name == glyph_name), None)
                if char_code and 0x0600 <= char_code <= 0x06FF:
                    self.raw_data['arabic_widths'].append(advance_width)
                    if glyph_name in self.positional_map['init']: self.raw_data['initial_widths'].append(self.hmtx[self.positional_map['init'][glyph_name]][0])
                    if glyph_name in self.positional_map['medi']: self.raw_data['medial_widths'].append(self.hmtx[self.positional_map['medi'][glyph_name]][0])
                    if glyph_name in self.positional_map['fina']: self.raw_data['final_widths'].append(self.hmtx[self.positional_map['fina'][glyph_name]][0])
            except Exception:
                continue

    def analyze(self):
        self.metrics.update(calculate_base_dimensions(self))
        self._gather_horizontal_data()
        self.metrics.update(calculate_consistency_metrics(self))
        self.metrics.update(calculate_special_metrics(self))
        self.metrics.update(calculate_vertical_consistency(self))
        
        return {k: v for k, v in self.metrics.items() if v is not None}

    def generate_width_histogram(self, output_dir, font_id, font_name):
        if not self.raw_data['widths']: return None
        # ... (الكود هنا لم يتغير) ...
        pass