# fonts/analyzer.py
from fontTools.ttLib import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from .metrics.base_dimensions import calculate_base_dimensions
from .metrics.consistency import calculate_consistency_metrics
# special_metrics سيتم إضافته لاحقًا بعد التأكد من عمل الأساسيات
# from .metrics.special_metrics import calculate_special_metrics
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
            'widths': [], 'lsbs': [], 'rsbs': [], 'v_centers': [],
            'arabic_ascenders': [], 'arabic_descenders': [],
            'latin_ascenders': [], 'latin_descenders': [],
        }

    def _gather_data(self):
        if not self.cmap: return

        x_height = self.metrics.get('x_height', 0)

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
                    self.raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)

                    # تحديد الصواعد والهوابط
                    if self.language_support != 'arabic_only' and x_height > 0 and yMax > x_height * 1.1:
                        self.raw_data['latin_ascenders'].append(yMax)
                    elif self.language_support != 'latin_only' and yMax > 300: # Heuristic for Arabic
                        self.raw_data['arabic_ascenders'].append(yMax)

                    if yMin < 0:
                        if self.language_support != 'arabic_only': self.raw_data['latin_descenders'].append(yMin)
                        if self.language_support != 'latin_only': self.raw_data['arabic_descenders'].append(yMin)
            except Exception:
                continue

    def analyze(self):
        self.metrics.update(calculate_base_dimensions(self))
        self._gather_data()
        self.metrics.update(calculate_consistency_metrics(self))
        # self.metrics.update(calculate_special_metrics(self)) # معطل مؤقتًا
        
        return {k: v for k, v in self.metrics.items() if v is not None}

    def generate_width_histogram(self, output_dir, font_id, font_name):
        # ... الكود هنا يبقى كما هو ...
        pass