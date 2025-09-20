# fonts/analyzer.py
from fontTools.ttLib import TTFont
import numpy as np
import matplotlib.pyplot as plt
import os
import uharfbuzz as hb

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

    def analyze(self):
        self._gather_data()
        self._calculate_metrics()
        return {k: v for k, v in self.metrics.items() if v is not None and not (isinstance(v, float) and np.isnan(v))}

    def _get_glyph_bbox(self, glyph_name):
        try:
            glyph = self.glyph_set[glyph_name]
            pen = glyph.getPen()
            glyph.draw(pen)
            return pen.getbbox()
        except Exception:
            return None

    def _gather_data(self):
        if not self.cmap: return
        
        LATIN_ASC_CHARS = "bdfhijklt"
        LATIN_DESC_CHARS = "gjpqy"
        ARABIC_ASC_CHARS = "أإآادذرزطظكلف"
        ARABIC_DESC_CHARS = "جحخعغرزوىقينم"
        
        for char_code, glyph_name in self.cmap.items():
            if not isinstance(glyph_name, str) or glyph_name == ".notdef": continue
            try:
                advance_width, lsb = self.hmtx[glyph_name]
                if advance_width == 0: continue
                
                self.raw_data['widths'].append(advance_width)
                self.raw_data['lsbs'].append(lsb)
                
                bbox = self._get_glyph_bbox(glyph_name)
                if bbox:
                    xMin, yMin, xMax, yMax = bbox
                    self.raw_data['rsbs'].append(advance_width - lsb - (xMax - xMin))
                    self.raw_data['v_centers'].append(yMin + (yMax - yMin) / 2)
                    
                    char = chr(char_code)
                    is_arabic = 0x0600 <= char_code <= 0x06FF
                    is_latin = 0x0041 <= char_code <= 0x007A

                    if is_arabic and self.language_support != 'latin_only':
                        if char in ARABIC_ASC_CHARS: self.raw_data['arabic_ascenders'].append(yMax)
                        if char in ARABIC_DESC_CHARS: self.raw_data['arabic_descenders'].append(yMin)
                    elif is_latin and self.language_support != 'arabic_only':
                        if char in LATIN_ASC_CHARS: self.raw_data['latin_ascenders'].append(yMax)
                        if char in LATIN_DESC_CHARS: self.raw_data['latin_descenders'].append(yMin)
            except Exception:
                continue

    def _calculate_metrics(self):
        # Base Dimensions
        hhea = self.font.get('hhea')
        os2 = self.font.get('OS/2')
        if hhea:
            self.metrics['ascender_height'] = hhea.ascender
            self.metrics['descender_depth'] = abs(hhea.descender)
        if os2:
            cap_h = getattr(os2, 'sCapHeight', self.metrics.get('ascender_height'))
            x_h = getattr(os2, 'sxHeight', None)
            # Fallback for x_height if not in OS/2
            if not x_h and self.language_support != 'arabic_only':
                bbox_x = self._get_glyph_bbox(self.cmap.get(ord('x')))
                if bbox_x: x_h = bbox_x[3]
            self.metrics['cap_height'] = cap_h
            self.metrics['x_height'] = x_h
            if x_h and cap_h and cap_h > 0:
                self.metrics['xheight_ratio'] = x_h / cap_h

        # Positional Consistency (HarfBuzz)
        try:
            face = hb.Face(self.font.reader.file.read())
            font = hb.Font(face)
            font.scale = (face.upem, face.upem)
            hb.ot_font_set_funcs(font)
            tatweel = "\u0640"
            ARABIC_CHAR_SET = [chr(c) for c in range(0x0621, 0x064A + 1)]
            for char in ARABIC_CHAR_SET:
                # Medial
                buf = hb.Buffer.create(); buf.add_str(tatweel + char + tatweel); buf.guess_segment_properties(); hb.shape(font, buf)
                if len(buf.glyph_positions) > 2: self.raw_data['medial_widths'].append(buf.glyph_positions[1].x_advance)
        except Exception: pass
        
        # Consistency Metrics
        def mean(arr): return np.mean(arr) if len(arr) > 1 else 0
        def std(arr): return np.std(arr) if len(arr) > 1 else 0
        def consistency(arr):
            mean_val = mean(arr)
            return std(arr) / abs(mean_val) if mean_val != 0 else None

        self.metrics['medial_consistency'] = consistency(self.raw_data['medial_widths'])
        self.metrics['balance_consistency'] = consistency(self.raw_data['v_centers'])
        self.metrics['arabic_ascender_consistency'] = consistency(self.raw_data['arabic_ascenders'])
        self.metrics['arabic_descender_consistency'] = consistency(self.raw_data['arabic_descenders'])
        self.metrics['latin_ascender_consistency'] = consistency(self.raw_data['latin_ascenders'])
        self.metrics['latin_descender_consistency'] = consistency(self.raw_data['latin_descenders'])

    def generate_width_histogram(self, output_dir, font_id, font_name):
        # ...
        pass