# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
from django.conf import settings
from django.core.files import File
import os
import csv
from django.http import HttpResponse
from django.utils.html import format_html, json_dumps
import json

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        """دالة مركزية لتنفيذ عملية التحليل الكاملة."""
        analyzer = FontAnalyzer(font_obj.font_file.path)
        analysis_data, debug_log = analyzer.analyze()
        
        # عرض سجل التدقيق كرسالة في لوحة التحكم
        debug_message = format_html("<strong>--- سجل التدقيق ---</strong><pre>{}</pre>", json.dumps(debug_log, indent=2))
        self.message_user(request, debug_message)

        # ... (بقية كود حساب الدرجة النهائية يبقى كما هو) ...
        total_score = 0
        total_weight = 0
        criteria = Criterion.objects.all()
        # ...
        analysis_data['final_score'] = (total_score / total_weight) * 10 if total_weight > 0 else None
        
        AnalysisResult.objects.update_or_create(font=font_obj, defaults=analysis_data)
        
    @admin.action(description="إعادة تحليل الخطوط المحددة")
    def reanalyze_fonts(self, request, queryset):
        for font in queryset:
            try:
                self._perform_analysis(request, font)
            except Exception as e:
                self.message_user(request, f"فشل تحليل الخط {font.font_name}: {e}", level='ERROR')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            self._perform_analysis(request, obj)
        except Exception as e:
            self.message_user(request, f"حدث خطأ أثناء التحليل: {e}", level='ERROR')

# ... (بقية كود CriterionAdmin و AnalysisResultAdmin يبقى كما هو) ...
@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope', 'lower_is_better')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    # لا حاجة لوجود الرسم البياني في هذه النسخة المبسطة
    list_display = [field.name for field in AnalysisResult._meta.fields]
    search_fields = ('font__font_name',)