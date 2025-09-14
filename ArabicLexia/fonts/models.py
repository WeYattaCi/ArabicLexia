# fonts/models.py
from django.db import models

class Font(models.Model):
    FONT_TYPE_CHOICES = [('serif', 'Serif'), ('sans-serif', 'Sans Serif')]
    LANG_SUPPORT_CHOICES = [('arabic_only', 'عربي فقط'), ('latin_only', 'لاتيني فقط'), ('bilingual', 'ثنائي اللغة')]
    CLASSIFICATION_CHOICES = [('standard', 'خط قياسي'), ('dyslexia-friendly', 'خط مصمم لعسر القراءة')]

    font_name = models.CharField(max_length=100, verbose_name="اسم الخط")
    designer = models.CharField(max_length=100, blank=True, null=True, verbose_name="المصمم")
    font_file = models.FileField(upload_to='font_files/', verbose_name="ملف الخط")
    font_type = models.CharField(max_length=20, choices=FONT_TYPE_CHOICES, verbose_name="فصيلة الخط")
    language_support = models.CharField(max_length=20, choices=LANG_SUPPORT_CHOICES, verbose_name="الدعم اللغوي")
    classification = models.CharField(max_length=30, choices=CLASSIFICATION_CHOICES, default='standard', verbose_name="تصنيف الخط")
    upload_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الرفع")

    def __str__(self):
        return self.font_name

class Criterion(models.Model):
    LANG_SCOPE_CHOICES = [('general', 'عام'), ('arabic', 'عربي فقط'), ('latin', 'لاتيني فقط')]

    criterion_name = models.CharField(max_length=200, verbose_name="اسم المعيار")
    metric_key = models.CharField(max_length=50, unique=True, verbose_name="المفتاح البرمجي")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    ideal_value = models.FloatField(verbose_name="القيمة المثالية")
    weight = models.FloatField(default=1.0, verbose_name="الأهمية (الوزن)")
    language_scope = models.CharField(max_length=20, choices=LANG_SCOPE_CHOICES, default='general', verbose_name="نطاق اللغة")

    def __str__(self):
        return self.criterion_name

class AnalysisResult(models.Model):
    font = models.OneToOneField(Font, on_delete=models.CASCADE, primary_key=True, verbose_name="الخط")
    final_score = models.FloatField(null=True, blank=True)
    # سيتم إضافة باقي حقول النتائج هنا لاحقًا

    def __str__(self):
        return f"نتائج تحليل {self.font.font_name}"