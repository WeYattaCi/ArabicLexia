# fonts/metrics/positional_consistency.py
import uharfbuzz as hb
from .utils import calculate_mean, calculate_std_dev

ARABIC_CHAR_SET = [chr(c) for c in range(0x0621, 0x064A + 1)] # All Arabic letters from Alef to Yeh

def calculate_positional_consistency(analyzer):
    results = {}
    initial_widths, medial_widths, final_widths, isolated_widths = [], [], [], []

    try:
        # تحميل بيانات الخط في HarfBuzz
        face = hb.Face(analyzer.font.reader.file.read())
        font = hb.Font(face)
        font.scale = (face.upem, face.upem)
        hb.ot_font_set_funcs(font)

        # كلمات الاختبار
        tatweel = "\u0640"

        for char in ARABIC_CHAR_SET:
            # 1. الشكل المنفرد
            buffer_iso = hb.Buffer()
            buffer_iso.add_str(char)
            buffer_iso.guess_segment_properties()
            hb.shape(font, buffer_iso)
            if buffer_iso.glyph_positions:
                isolated_widths.append(buffer_iso.glyph_positions[0].x_advance)

            # 2. الشكل النهائي
            buffer_fina = hb.Buffer()
            buffer_fina.add_str(tatweel + char)
            buffer_fina.guess_segment_properties()
            hb.shape(font, buffer_fina)
            if len(buffer_fina.glyph_positions) > 1:
                final_widths.append(buffer_fina.glyph_positions[1].x_advance)

            # 3. الشكل الابتدائي
            buffer_init = hb.Buffer()
            buffer_init.add_str(char + tatweel)
            buffer_init.guess_segment_properties()
            hb.shape(font, buffer_init)
            if buffer_init.glyph_positions:
                initial_widths.append(buffer_init.glyph_positions[0].x_advance)

            # 4. الشكل الوسطي
            buffer_medi = hb.Buffer()
            buffer_medi.add_str(tatweel + char + tatweel)
            buffer_medi.guess_segment_properties()
            hb.shape(font, buffer_medi)
            if len(buffer_medi.glyph_positions) > 2:
                medial_widths.append(buffer_medi.glyph_positions[1].x_advance)

    except Exception:
        # إذا فشلت عملية HarfBuzz لأي سبب، نرجع قيمًا فارغة
        return {}

    def consistency(arr):
        mean_val = calculate_mean(arr)
        return calculate_std_dev(arr) / abs(mean_val) if mean_val != 0 else None

    results['isolated_consistency'] = consistency(isolated_widths)
    results['initial_consistency'] = consistency(initial_widths)
    results['medial_consistency'] = consistency(medial_widths)
    results['final_consistency'] = consistency(final_widths)

    return results