# fonts/analyzer.py (النسخة المبسطة والشفافة)
from fontTools.ttLib import TTFont
import numpy as np

class FontAnalyzer:
    def __init__(self, font_path):
        self.font = TTFont(font_path)
        self.metrics = {}
        self.raw_data = {
            'widths': [], 'lsbs': [], 'rsbs': [], 'v_centers': [],
            'arabic_ascenders': [], 'arabic_descenders': [],
            'latin_ascenders': [], 'latin_descenders': []
        }
        self.debug_log = {
            "Total Glyphs in Cmap": 0, "Glyphs Processed": 0, "Glyphs with BBox": 0,
            "Arabic Glyphs Found": 0, "Latin Glyphs Found": 0
        }

    def analyze(self):
        cmap = self.font.getBestCmap()
        if not cmap:
            return {}, {"Error": "No valid cmap table found."}
        
        glyph_set = self.font.getGlyphSet()
        hmtx = self.font['hmtx']
        hhea = self.font.get('hhea')
        os2 = self.font.get('OS/2')
        
        self.debug_log["Total Glyphs in Cmap"] = len(cmap)
        
        # --- حلقة واحدة لجمع كل البيانات ---
        for char_code, glyph_name in cmap.items():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef":
                continue
            
            try:
                advance_width, lsb = hmtx[glyph_name]
                if advance_width == 0: continue

                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)
                
                glyph = glyph_set[glyph_name]
                pen = glyph.getPen()
                bbox = pen.getbbox()
                
                if bbox:
                    self.debug_log["Glyphs with BBox"] += 1
                    xMin, yMin, xMax, yMax = bbox
                    self.raw_data['rsbs'].append(advance_width - lsb - (xMax - xMin))
                    self.raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)
                    
                    is_arabic = 0x0600 <= char_code <= 0x06FF
                    is_latin = 0x0041 <= char_code <= 0x007A

                    if is_arabic:
                        self.debug_log["Arabic Glyphs Found"] += 1
                        if yMax > 300: self.raw_data['arabic_ascenders'].append(yMax)
                        if yMin < 0: self.raw_data['arabic_descenders'].append(yMin)
                    elif is_latin:
                        self.debug_log["Latin Glyphs Found"] += 1
                        if yMax > 500: self.raw_data['latin_ascenders'].append(yMax)
                        if yMin < -100: self.raw_data['latin_descenders'].append(yMin)
                
                self.debug_log["Glyphs Processed"] += 1
            except Exception:
                continue

        # --- حساب كل المعايير في مكان واحد ---
        
        # الأبعاد الأساسية
        if hhea:
            self.metrics['ascender_height'] = hhea.ascender
            self.metrics['descender_depth'] = abs(hhea.descender)
        if os2:
            self.metrics['cap_height'] = os2.sCapHeight if hasattr(os2, 'sCapHeight') else None
            self.metrics['x_height'] = os2.sxHeight if hasattr(os2, 'sxHeight') else None
            if self.metrics.get('x_height') and self.metrics.get('cap_height'):
                if self.metrics['cap_height'] > 0:
                    self.metrics['xheight_ratio'] = self.metrics['x_height'] / self.metrics['cap_height']

        # معايير الاتساق
        mean_width = np.mean(self.raw_data['widths']) if self.raw_data['widths'] else 0
        self.metrics['width_consistency'] = np.std(self.raw_data['widths']) / mean_width if mean_width > 0 else None
        
        all_bearings = self.raw_data['lsbs'] + self.raw_data['rsbs']
        self.metrics['sidebearing_consistency'] = np.std(all_bearings) / mean_width if mean_width > 0 and len(all_bearings) > 1 else None
        
        cap_height = self.metrics.get('cap_height', 0)
        self.metrics['balance_consistency'] = np.std(self.raw_data['v_centers']) / cap_height if cap_height and cap_height > 0 and len(self.raw_data['v_centers']) > 1 else None

        # اتساق الصواعد والهوابط
        if len(self.raw_data['arabic_ascenders']) > 1: self.metrics['arabic_ascender_consistency'] = np.std(self.raw_data['arabic_ascenders']) / np.mean(self.raw_data['arabic_ascenders'])
        if len(self.raw_data['arabic_descenders']) > 1: self.metrics['arabic_descender_consistency'] = np.std(self.raw_data['arabic_descenders']) / np.mean(self.raw_data['arabic_descenders'])
        if len(self.raw_data['latin_ascenders']) > 1: self.metrics['latin_ascender_consistency'] = np.std(self.raw_data['latin_ascenders']) / np.mean(self.raw_data['latin_ascenders'])
        if len(self.raw_data['latin_descenders']) > 1: self.metrics['latin_descender_consistency'] = np.std(self.raw_data['latin_descenders']) / np.mean(self.raw_data['latin_descenders'])

        # تحديث سجل التدقيق بأعداد العناصر
        for key, value in self.raw_data.items():
            self.debug_log[f"Count_{key}"] = len(value)
            
        return self.metrics, self.debug_log