# fonts/metrics/positional_consistency.py
import uharfbuzz as hb
from .utils import calculate_mean, calculate_std_dev
ARABIC_CHAR_SET = [chr(c) for c in range(0x0621, 0x064A + 1)]
def calculate_positional_consistency(analyzer):
    results = {}
    widths = {'initial': [], 'medial': [], 'final': [], 'isolated': [], 'arabic_widths': []}
    try:
        font_data = analyzer.font.reader.file.read(); analyzer.font.reader.file.seek(0)
        face = hb.Face(font_data); font = hb.Font(face); font.scale = (face.upem, face.upem); hb.ot_font_set_funcs(font)
        tatweel = "\u0640"
        for char in ARABIC_CHAR_SET:
            iso_buf = hb.Buffer.create(); iso_buf.add_str(char); iso_buf.guess_segment_properties(); hb.shape(font, iso_buf)
            if iso_buf.glyph_positions: widths['isolated'].append(iso_buf.glyph_positions[0].x_advance)
            fina_buf = hb.Buffer.create(); fina_buf.add_str(tatweel + char); fina_buf.guess_segment_properties(); hb.shape(font, fina_buf)
            if len(fina_buf.glyph_positions) > 1: widths['final'].append(fina_buf.glyph_positions[1].x_advance)
            init_buf = hb.Buffer.create(); init_buf.add_str(char + tatweel); init_buf.guess_segment_properties(); hb.shape(font, init_buf)
            if init_buf.glyph_positions: widths['initial'].append(init_buf.glyph_positions[0].x_advance)
            medi_buf = hb.Buffer.create(); medi_buf.add_str(tatweel + char + tatweel); medi_buf.guess_segment_properties(); hb.shape(font, medi_buf)
            if len(medi_buf.glyph_positions) > 2: widths['medial'].append(medi_buf.glyph_positions[1].x_advance)
    except Exception: return {}
    def consistency(arr):
        mean_val = calculate_mean(arr)
        return calculate_std_dev(arr) / abs(mean_val) if mean_val != 0 else None
    results['isolated_consistency'] = consistency(widths['isolated'])
    results['initial_consistency'] = consistency(widths['initial'])
    results['medial_consistency'] = consistency(widths['medial'])
    results['final_consistency'] = consistency(widths['final'])
    analyzer.raw_data['arabic_widths'] = widths['isolated'] # Pass isolated widths to main analyzer
    return results