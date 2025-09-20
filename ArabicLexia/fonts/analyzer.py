# fonts/analyzer.py
import subprocess
import json
import tempfile
import os
from fontTools.ttLib import TTFont

class FontAnalyzer:
    def __init__(self, font_path, font_type, language_support):
        self.font_path = font_path
        self.font_type = font_type
        self.language_support = language_support
        self.metrics = {}

    def analyze(self):
        # --- 1. تشغيل أداة gftools qa والحصول على تقرير JSON ---
        # نستخدم ملفًا مؤقتًا لحفظ التقرير
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as report_file:
            report_path = report_file.name
        
        command = ["gftools", "qa", self.font_path, "--json", report_path]
        
        try:
            # نشغل الأمر. قد يستغرق بضع ثوانٍ.
            subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8')
            
            # نقرأ التقرير المفصل الذي تم إنشاؤه
            with open(report_path, "r", encoding='utf-8') as f:
                report_data = json.load(f)
        
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError) as e:
            # إذا فشلت الأداة لأي سبب، نطبع الخطأ ونرجع نتيجة فارغة
            print(f"gftools qa failed: {e}")
            report_data = {}
        finally:
            # نحذف الملف المؤقت
            if os.path.exists(report_path):
                os.remove(report_path)

        # --- 2. استخلاص المقاييس الهامة من التقرير ---
        # تقرير gftools معقد، سنبحث فيه عن النتائج التي تهمنا
        if "com.google.fonts/check/vertical_metrics" in report_data:
            for result in report_data["com.google.fonts/check/vertical_metrics"].get("results", []):
                if "hhea" in result.get("message", ""):
                    self.metrics['ascender_height'] = result.get('ascender')
                    self.metrics['descender_depth'] = abs(result.get('descender', 0))
                if "OS/2" in result.get("message", ""):
                    # هذه الأداة لا توفر x-height مباشرة، سنقرأه يدويًا كخطة بديلة
                    pass
        
        if "com.google.fonts/check/kern_consistency" in report_data:
            # gftools لا يعد أزواج التقنين مباشرة، لكنه يتحقق من وجودها
            # سنعتبر وجود نتيجة ناجحة كمؤشر على جودة التقنين
            result = report_data["com.google.fonts/check/kern_consistency"].get("result")
            kerning_quality = 1 if result == "PASS" else 0
            self.metrics['arabic_kerning_quality'] = kerning_quality
            self.metrics['latin_kerning_quality'] = kerning_quality

        # --- 3. استخلاص المقاييس التي لا يوفرها gftools مباشرة ---
        # نستخدم fontTools كأداة مساعدة
        try:
            font = TTFont(self.font_path)
            os2 = font.get('OS/2')
            if os2 and hasattr(os2, 'sCapHeight'):
                self.metrics['cap_height'] = os2.sCapHeight
            if os2 and hasattr(os2, 'sxHeight'):
                self.metrics['x_height'] = os2.sxHeight
        except Exception:
            pass # نتجاهل الأخطاء إذا فشلت القراءة

        if self.metrics.get('x_height') and self.metrics.get('cap_height', 0) > 0:
            self.metrics['xheight_ratio'] = self.metrics['x_height'] / self.metrics['cap_height']
            
        return self.metrics

    def generate_width_histogram(self, output_dir, font_id, font_name):
        # هذه الدالة يمكن إعادة تفعيلها بنفس طريقتنا السابقة
        pass