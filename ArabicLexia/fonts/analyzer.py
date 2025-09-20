# fonts/analyzer.py
from fontTools.ttLib import TTFont
import matplotlib.pyplot as plt
import os
from .metrics.base_dimensions import calculate_base_dimensions
from .metrics.consistency import calculate_consistency_metrics
from .metrics.special_metrics import calculate_special_metrics
from .metrics.positional_consistency import calculate_positional_consistency
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
        self.raw_data = {'widths': [], 'lsbs': [], 'rsbs': []}

    def _gather_base_data(self):
        if not self.cmap: return
        for glyph_name in self.cmap.values():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)
                bbox = get_glyph_bbox(self.glyph_set, glyph_name)
                if bbox: self.raw_data['rsbs'].append(advance_width - lsb - (bbox[2] - bbox[0]))
            except Exception: continue

    def analyze(self):
        self._gather_base_data()
        self.metrics.update(calculate_base_dimensions(self))
        # consistency metrics are now calculated in their own specialized module
        self.metrics.update(calculate_consistency_metrics(self))
        self.metrics.update(calculate_special_metrics(self))
        if self.language_support != 'latin_only':
            self.metrics.update(calculate_positional_consistency(self))
        kerning_val = self.metrics.pop('kerning_quality', 0)
        self.metrics['arabic_kerning_quality'] = kerning_val
        self.metrics['latin_kerning_quality'] = kerning_val
        return {k: v for k, v in self.metrics.items() if v is not None}
    
    def generate_width_histogram(self, output_dir, font_id, font_name):
        # ... (الكود هنا لم يتغير) ...
        pass