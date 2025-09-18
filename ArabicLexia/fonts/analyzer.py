# fonts/analyzer.py
from fontTools.ttLib import TTFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

from .metrics.base_dimensions import calculate_base_dimensions
from .metrics.consistency import calculate_consistency_metrics
from .metrics.special_metrics import calculate_special_metrics
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
            'arabic_ascenders': [], 'arabic_descenders': [], 'arabic_widths': [],
            'latin_ascenders': [], 'latin_descenders': [],
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

    def _gather_data(self):
        if not self.cmap: return
        
        LATIN_ASC_CHARS = "bdfhkl"
        LATIN_DESC_CHARS = "gjpqy"
        ARABIC_ASC_CHARS = "أإآادذرزطظكلام"
        ARABIC_DESC_CHARS = "جحخعغفقرزوى"

        for char_code, glyph_name in self.cmap.items():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                
                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)
                
                # --- الإصلاح الجذري هنا: نستخدم الحرف الفعلي للمقارنة ---
                char = chr(char_code)
                is_arabic = 0x0600 <= char_code <= 0x06FF
                is_latin = 0x0041 <= char_code <= 0x007A
                
                if is_arabic and self.language_support != 'latin_only':
                    self.raw_data['arabic_widths'].append(advance_width)
                    if glyph_name in self.positional_map['init']: self.raw_data['initial_widths'].append(self.hmtx[self.positional_map['init'][glyph_name]][0])
                    if glyph_name in self.positional_map['medi']: self.raw_data['medial_widths'].append(self.hmtx[self.positional_map['medi'][glyph_name]][0])
                    if glyph_name in self.positional_map['fina']: self.raw_data['final_widths'].append(self.hmtx[self.positional_map['fina'][glyph_name]][0])

                bbox = get_glyph_bbox(self.glyph_set, glyph_name)
                if bbox:
                    xMin, yMin, xMax, yMax = bbox
                    self.raw_data['rsbs'].append(advance_width - lsb - (xMax - xMin))
                    self.raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)
                    
                    if is_arabic and self.language_support != 'latin_only':
                        if char in ARABIC_ASC_CHARS: self.raw_data['arabic_ascenders'].append(yMax)
                        if char in ARABIC_DESC_CHARS: self.raw_data['arabic_descenders'].append(yMin)
                    elif is_latin and self.language_support != 'arabic_only':
                        if char in LATIN_ASC_CHARS: self.raw_data['latin_ascenders'].append(yMax)
                        if char in LATIN_DESC_CHARS: self.raw_data['latin_descenders'].append(yMin)
            except Exception:
                continue

    def analyze(self):
        self.metrics.update(calculate_base_dimensions(self))
        self._gather_data()
        self.metrics.update(calculate_consistency_metrics(self))
        self.metrics.update(calculate_special_metrics(self))
        return {k: v for k, v in self.metrics.items() if v is not None}

    def generate_width_histogram(self, output_dir, font_id, font_name):
        if not self.raw_data['widths']: return None
        # ... (بقية الكود تبقى كما هي)
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        plt.figure(figsize=(10, 6))
        plt.hist(self.raw_data['widths'], bins=50, color='teal', edgecolor='black')
        plt.title(f'Glyph Width Distribution for: {font_name}')
        plt.xlabel('Glyph Advance Width (FUnits)')
        plt.ylabel('Frequency')
        plt.grid(True, linestyle='--', alpha=0.6)
        file_path = os.path.join(output_dir, f'width_histogram_{font_id}.png')
        plt.savefig(file_path)
        plt.close()
        return file_path