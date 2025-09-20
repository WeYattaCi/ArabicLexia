# fonts/analyzer.py
import subprocess
import json
from fontTools.ttLib import TTFont
import matplotlib.pyplot as plt
import os

class FontAnalyzer:
    def __init__(self, font_path, font_type, language_support):
        self.font = TTFont(font_path)
        self.font_path = font_path
        self.font_type = font_type
        self.language_support = language_support
        self.metrics = {}

    def analyze(self):
        # --- 1. استدعاء الأداة الخارجية للحصول على المقاييس الدقيقة ---
        command = ["fv-font-metrics", "-j", self.font_path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            font_v_metrics = json.loads(result.stdout)
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # إذا فشلت الأداة الخارجية، نرجع قاموسًا فارغًا
            font_v_metrics = {}

        # --- 2. خريطة لربط أسماء نتائج الأداة بأسماء حقولنا ---
        key_map = {
            "ascender": "ascender_height",
            "descender": "descender_depth",
            "cap_height": "cap_height",
            "x_height": "x_height",
            "units_per_em": "units_per_em", # كمثال لمقياس جديد
            "kerning_pair_count": "kerning_quality"
        }

        # --- 3. تعبئة قاموس النتائج الخاص بنا ---
        for key, value in font_v_metrics.items():
            if key in key_map:
                our_key = key_map[key]
                # تحويل القيم السالبة للهوابط إلى موجبة
                if our_key == 'descender_depth':
                    self.metrics[our_key] = abs(value)
                else:
                    self.metrics[our_key] = value
        
        # ربط نتيجة التقنين باللغتين كما في السابق
        kerning_count = self.metrics.get('kerning_quality', 0)
        self.metrics['arabic_kerning_quality'] = kerning_count
        self.metrics['latin_kerning_quality'] = kerning_count

        # حساب المعايير التي لم توفرها الأداة (إذا أردنا)
        if self.metrics.get('x_height') and self.metrics.get('cap_height', 0) > 0:
            self.metrics['xheight_ratio'] = self.metrics['x_height'] / self.metrics['cap_height']
            
        return self.metrics

    def generate_width_histogram(self, output_dir, font_id, font_name):
        # هذه الدالة يمكن إعادة تفعيلها بنفس طريقتنا السابقة إذا أردنا
        pass