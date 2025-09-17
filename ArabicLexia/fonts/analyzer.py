# fonts/analyzer.py
import sys
import json
import numpy as np
from fontTools.ttLib import TTFont
import os
import matplotlib
matplotlib.use('Agg') # وضع التشغيل غير التفاعلي للرسوم البيانية
import matplotlib.pyplot as plt


# --- الدوال الإحصائية المساعدة ---
def calculate_mean(arr):
    return np.mean(arr) if arr and len(arr) > 0 else None

def calculate_std_dev(arr):
    return np.std(arr) if arr and len(arr) > 1 else 0

# --- الفئة الرئيسية للتحليل ---
class FontAnalyzer:
    def __init__(self, font_path, font_type):
        try:
            self.font = TTFont(font_path)
        except Exception as e:
            raise IOError(f"Could not read font file: {e}")
        self.font_type = font_type
        self.metrics = {}
        # قاموس لتخزين بيانات الحروف العربية الموضعية
        self.arabic_positional_widths = {'initial': [], 'medial': [], 'final': []}
        self.raw_data = {
            'latin_widths': [], 'arabic_widths': [], 'all_widths': [],
            'latin_ascenders': [], 'arabic_ascenders': [],
            'latin_descenders': [], 'arabic_descenders': [],
            'vertical_centers': [], 'left_side_bearings': [], 'right_side_bearings': []
        }
        # استدعاء دالة تحليل GSUB الجديدة
        self._map_positional_glyphs()

    def analyze(self):
        """Runs the full analysis suite."""
        self._gather_raw_data()
        self._calculate_basic_dimensions()
        self._calculate_consistency_metrics()
        self._calculate_contextual_metrics() # سيتم تفعيل هذه الدالة الآن
        self._calculate_special_metrics()
        return {k: (None if v is None or (isinstance(v, float) and np.isnan(v)) else v) for k, v in self.metrics.items()}

    def _map_positional_glyphs(self):
        """يقرأ جدول GSUB لربط الحروف الأساسية بأشكالها الموضعية."""
        self.positional_map = {'init': {}, 'medi': {}, 'fina': {}}
        if 'GSUB' not in self.font:
            return

        gsub = self.font['GSUB'].table
        features = {feature.FeatureTag: feature.Feature for feature in gsub.FeatureList.FeatureRecord}
        
        for tag in ['init', 'medi', 'fina']:
            if tag in features:
                for lookup_index in features[tag].LookupListIndex:
                    lookup = gsub.LookupList.Lookup[lookup_index]
                    for subtable in lookup.SubTable:
                        if subtable.LookupType == 1: # Single Substitution
                            for base_glyph, variant_glyph in subtable.mapping.items():
                                self.positional_map[tag][base_glyph] = variant_glyph

    def _gather_raw_data(self):
        cmap = self.font.getBestCmap()
        if not cmap: return

        glyph_set = self.font.getGlyphSet()
        hmtx = self.font['hmtx']
        
        for char_code in cmap:
            glyph_name = cmap[char_code]
            try:
                advance_width, lsb = hmtx[glyph_name]
                if advance_width == 0: continue
                
                glyph = glyph_set[glyph_name]
                self.raw_data['all_widths'].append(advance_width)
                self.raw_data['left_side_bearings'].append(lsb)
                if hasattr(glyph, 'xMin') and hasattr(glyph, 'xMax'):
                    self.raw_data['right_side_bearings'].append(advance_width - lsb - (glyph.xMax - glyph.xMin))

                if hasattr(glyph, 'yMin') and hasattr(glyph, 'yMax'):
                    self.raw_data['vertical_centers'].append(glyph.yMin + (glyph.yMax - glyph.yMin) / 2)

                is_arabic = 0x0600 <= char_code <= 0x06FF
                is_latin = (0x0041 <= char_code <= 0x005A) or (0x0061 <= char_code <= 0x007A)

                if is_latin:
                    self.raw_data['latin_widths'].append(advance_width)
                    if chr(char_code) in 'bdfhklt' and hasattr(glyph, 'yMax'): self.raw_data['latin_ascenders'].append(glyph.yMax)
                    if chr(char_code) in 'gjpqy' and hasattr(glyph, 'yMin'): self.raw_data['latin_descenders'].append(glyph.yMin)
                elif is_arabic:
                    self.raw_data['arabic_widths'].append(advance_width)
                    if chr(char_code) in 'أطظكلام' and hasattr(glyph, 'yMax'): self.raw_data['arabic_ascenders'].append(glyph.yMax)
                    if chr(char_code) in 'جحخروز' and hasattr(glyph, 'yMin'): self.raw_data['arabic_descenders'].append(glyph.yMin)
                    
                    # جلب عرض الأشكال الموضعية
                    for tag, mapping in self.positional_map.items():
                        if glyph_name in mapping:
                            variant_glyph_name = mapping[glyph_name]
                            variant_width, _ = hmtx[variant_glyph_name]
                            if variant_width > 0:
                                self.arabic_positional_widths[tag.replace('init', 'initial').replace('medi', 'medial').replace('fina', 'final')].append(variant_width)

            except (KeyError, AttributeError):
                continue
    
    def _calculate_basic_dimensions(self):
        units_per_em = self.font['head'].unitsPerEm
        os2 = self.font.get('OS/2')
        hhea = self.font.get('hhea')
        
        self.metrics['ascender_height'] = hhea.ascender / units_per_em if hhea else None
        self.metrics['descender_depth'] = abs(hhea.descender / units_per_em) if hhea else None
        self.metrics['cap_height'] = os2.sCapHeight / units_per_em if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else self.metrics.get('ascender_height')
        self.metrics['x_height'] = os2.sxHeight / units_per_em if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else None
        
        cap_height_funits = os2.sCapHeight if os2 and hasattr(os2, 'sCapHeight') and os2.sCapHeight else (hhea.ascender if hhea else None)
        x_height_funits = os2.sxHeight if os2 and hasattr(os2, 'sxHeight') and os2.sxHeight else None
        self.metrics['xheight_ratio'] = (x_height_funits / cap_height_funits) if cap_height_funits and x_height_funits and cap_height_funits > 0 else None

    def _calculate_consistency_metrics(self):
        width_mean = calculate_mean(self.raw_data['all_widths'])
        self.metrics['width_consistency'] = (calculate_std_dev(self.raw_data['all_widths']) / width_mean) if width_mean and width_mean > 0 else None
        
        cap_height_funits = (self.metrics.get('cap_height') or 0) * self.font['head'].unitsPerEm
        self.metrics['balance_consistency'] = (calculate_std_dev(self.raw_data['vertical_centers']) / cap_height_funits) if cap_height_funits > 0 else None
        
        all_bearings = self.raw_data['left_side_bearings'] + self.raw_data['right_side_bearings']
        self.metrics['sidebearing_consistency'] = (calculate_std_dev(all_bearings) / width_mean) if width_mean and width_mean > 0 else None

        mean_lat_asc = calculate_mean(self.raw_data['latin_ascenders'])
        self.metrics['latin_ascender_consistency'] = (calculate_std_dev(self.raw_data['latin_ascenders']) / mean_lat_asc) if mean_lat_asc and mean_lat_asc > 0 else None
        
        mean_ara_asc = calculate_mean(self.raw_data['arabic_ascenders'])
        self.metrics['arabic_ascender_consistency'] = (calculate_std_dev(self.raw_data['arabic_ascenders']) / mean_ara_asc) if mean_ara_asc and mean_ara_asc > 0 else None

        mean_lat_desc = calculate_mean(self.raw_data['latin_descenders'])
        self.metrics['latin_descender_consistency'] = (calculate_std_dev(self.raw_data['latin_descenders']) / abs(mean_lat_desc)) if mean_lat_desc and mean_lat_desc != 0 else None
        
        mean_ara_desc = calculate_mean(self.raw_data['arabic_descenders'])
        self.metrics['arabic_descender_consistency'] = (calculate_std_dev(self.raw_data['arabic_descenders']) / abs(mean_ara_desc)) if mean_ara_desc and mean_ara_desc != 0 else None

        isolated_mean = calculate_mean(self.raw_data['arabic_widths'])
        self.metrics['isolated_consistency'] = (calculate_std_dev(self.raw_data['arabic_widths']) / isolated_mean) if isolated_mean and isolated_mean > 0 else None

    def _calculate_contextual_metrics(self):
        """تحسب اتساق عرض الأشكال العربية الموضعية."""
        for key, widths in self.arabic_positional_widths.items():
            mean_val = calculate_mean(widths)
            std_dev = calculate_std_dev(widths)
            consistency = (std_dev / mean_val) if mean_val and mean_val > 0 else None
            self.metrics[f'{key}_consistency'] = consistency
        
    def _calculate_special_metrics(self):
        self.metrics['score_for_sans_serif'] = 1.0 if self.font_type == 'sans-serif' else 0.0
        self.metrics['score_for_serif'] = 1.0 if self.font_type == 'serif' else 0.0
        
        self.metrics['latin_kerning_quality'] = 1.0 if 'kern' in self.font else 0.0
        self.metrics['arabic_kerning_quality'] = 1.0 if 'GPOS' in self.font and any(f.FeatureTag == 'kern' for f in self.font['GPOS'].table.FeatureList.FeatureRecord) else 0.0
        
        diacritics = [chr(c) for c in range(0x064B, 0x0652 + 1)]
        cmap = self.font.getBestCmap()
        if cmap:
            found_diacritics = [d for d in diacritics if ord(d) in cmap]
            self.metrics['diacritic_consistency'] = len(found_diacritics) / len(diacritics) if diacritics else 0.0
        else:
            self.metrics['diacritic_consistency'] = 0.0
        
        width_mean = calculate_mean(self.raw_data['all_widths'])
        space_glyph_name = cmap.get(32) if cmap else None
        if space_glyph_name and width_mean and width_mean > 0:
            try:
                self.metrics['space_width_ratio'] = self.font['hmtx'][space_glyph_name][0] / width_mean
            except KeyError:
                self.metrics['space_width_ratio'] = None
        else:
            self.metrics['space_width_ratio'] = None
            
    def generate_width_histogram(self, output_dir, font_id):
        """تنشئ رسمًا بيانيًا لتوزيع عرض الحروف."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        plt.figure(figsize=(10, 6))
        plt.hist(self.raw_data['all_widths'], bins=50, color='skyblue', edgecolor='black')
        plt.title(f'Glyph Width Distribution for Font ID: {font_id}')
        plt.xlabel('Glyph Advance Width (FUnits)')
        plt.ylabel('Frequency')
        plt.grid(True, linestyle='--', alpha=0.6)
        
        file_path = os.path.join(output_dir, f'width_histogram_{font_id}.png')
        plt.savefig(file_path)
        plt.close()
        return file_path


if __name__ == "__main__":
    if len(sys.argv) > 2:
        font_path, font_type = sys.argv[1], sys.argv[2]
        try:
            analyzer = FontAnalyzer(font_path, font_type)
            results = analyzer.analyze()
            print(json.dumps(results, indent=2))
        except Exception as e:
            error_data = {"error": f"Analysis failed in analyzer.py: {e}"}
            print(json.dumps(error_data), file=sys.stderr)
            sys.exit(1)