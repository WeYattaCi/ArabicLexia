# fonts/models.py
from django.db import models

class Font(models.Model):
    # ... (الكود هنا لم يتغير)
    font_name = models.CharField(max_length=100, verbose_name="اسم الخط")
    designer = models.CharField(max_length=100, blank=True, null=True, verbose_name="المصمم")
    font_file = models.FileField(upload_to='font_files/', verbose_name="ملف الخط")
    font_type = models.CharField(max_length=20, choices=[('serif', 'Serif'), ('sans-serif', 'Sans Serif')], verbose_name="فصيلة الخط")
    language_support = models.CharField(max_length=20, choices=[('arabic_only', 'عربي فقط'), ('latin_only', 'لاتيني فقط'), ('bilingual', 'ثنائي اللغة')], verbose_name="الدعم اللغوي")
    classification = models.CharField(max_length=30, choices=[('standard', 'خط قياسي'), ('dyslexia-friendly', 'خط مصمم لعسر القراءة')], default='standard', verbose_name="تصنيف الخط")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    def __str__(self):
        return self.font_name

class Criterion(models.Model):
    # ... (الكود هنا لم يتغير)
    criterion_name = models.CharField(max_length=200, verbose_name="اسم المعيار")
    metric_key = models.CharField(max_length=50, unique=True, verbose_name="المفتاح البرمجي")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    ideal_value = models.FloatField(verbose_name="القيمة المثالية")
    weight = models.FloatField(default=1.0, verbose_name="الأهمية (الوزن)")
    language_scope = models.CharField(max_length=20, choices=[('general', 'عام'), ('arabic', 'عربي فقط'), ('latin', 'لاتيني فقط')], default='general', verbose_name="نطاق اللغة")
    lower_is_better = models.BooleanField(default=False, verbose_name="هل القيمة الأقل أفضل؟")

    def __str__(self):
        return self.criterion_name

class AnalysisResult(models.Model):
    font = models.OneToOneField(Font, on_delete=models.CASCADE, primary_key=True, verbose_name="الخط")
    final_score = models.FloatField(null=True, blank=True, verbose_name="الدرجة النهائية")
    # ... (بقية الحقول تبقى كما هي)
    score_for_sans_serif = models.FloatField(null=True, blank=True, verbose_name="درجة Sans Serif")
    score_for_serif = models.FloatField(null=True, blank=True, verbose_name="درجة Serif")
    ascender_height = models.FloatField(null=True, blank=True, verbose_name="ارتفاع الصواعد")
    descender_depth = models.FloatField(null=True, blank=True, verbose_name="عمق الهوابط")
    cap_height = models.FloatField(null=True, blank=True, verbose_name="ارتفاع الحرف الكبير")
    x_height = models.FloatField(null=True, blank=True, verbose_name="ارتفاع حرف x")
    xheight_ratio = models.FloatField(null=True, blank=True, verbose_name="نسبة ارتفاع x")
    space_width_ratio = models.FloatField(null=True, blank=True, verbose_name="نسبة عرض الفراغ")
    width_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق عرض الحروف")
    balance_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق توازن الحروف")
    sidebearing_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الهوامش الجانبية")
    initial_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الأشكال الابتدائية")
    medial_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الأشكال الوسطية")
    final_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الأشكال النهائية")
    isolated_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الأشكال المنفردة")
    arabic_ascender_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الصواعد (عربي)")
    arabic_descender_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الهوابط (عربي)")
    diacritic_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق مواضع التشكيل")
    latin_ascender_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الصواعد (لاتيني)")
    latin_descender_consistency = models.FloatField(null=True, blank=True, verbose_name="اتساق الهوابط (لاتيني)")
    width_histogram = models.ImageField(upload_to='analysis_reports/', null=True, blank=True, verbose_name="رسم توزيع العرض")
    
    # -- تم تغيير هذين الحقلين --
    arabic_kerning_quality = models.IntegerField(null=True, blank=True, verbose_name="جودة التقنين (عربي)")
    latin_kerning_quality = models.IntegerField(null=True, blank=True, verbose_name="جودة التقنين (لاتيني)")
    
    def __str__(self):
        return f"نتائج تحليل {self.font.font_name}"