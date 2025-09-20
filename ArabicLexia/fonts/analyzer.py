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
from .metrics.positional_consistency import calculate_positional_consistency # <-- استيراد الوحدة الجديدة

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
            # لم نعد بحاجة لجمع بيانات الأشكال الموضعية هنا
        }

    def _gather_data(self):
        # ... (هذه الدالة الآن تجمع البيانات العامة فقط)
        pass

    def analyze(self):
        # لم نعد بحاجة لـ _gather_data، كل وحدة تجمع بياناتها بنفسها
        self.metrics.update(calculate_base_dimensions(self))
        # consistency.py سيتم تحديثه لاحقًا ليعتمد على نفسه
        # self.metrics.update(calculate_consistency_metrics(self))
        self.metrics.update(calculate_special_metrics(self))
        self.metrics.update(calculate_vertical_consistency(self))
        self.metrics.update(calculate_positional_consistency(self)) # <-- استدعاء الوحدة الجديدة
        
        # ... بقية الكود
        return {k: v for k, v in self.metrics.items() if v is not None}
    
    def generate_width_histogram(self, output_dir, font_id, font_name):
        # ... (الكود هنا لم يتغير)
        pass