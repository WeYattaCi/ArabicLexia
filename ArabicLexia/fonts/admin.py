# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
from django.conf import settings
from django.core.files import File
import os
import csv
from django.http import HttpResponse
from django.utils.html import format_html # <-- تم تصحيح هذا السطر
import json
import traceback

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        """دالة مركزية لتنفيذ عملية التحليل الكاملة."""
        # لاحظ أننا أزلنا font_type و language_support من هنا لأنهما غير مستخدمان في النسخة المبسطة
        analyzer = FontAnalyzer(font_obj.font_file.path)
        analysis_data, debug_log = analyzer.analyze()
        
        debug_message = format_html("<strong>--- سجل التدقيق ---</strong><pre>{}</pre>", json.dumps(debug_log, indent=2, ensure_ascii=False))
        self.message_user(request, debug_message, level='INFO')

        # حساب الدرجة النهائية
        total_score = 0
        total_weight = 0
        criteria = Criterion.objects.all()
        if font_obj.language_support == 'arabic_only':
            criteria = criteria.exclude(language_scope='latin')
        elif font_obj.language_support == 'latin_only':
            criteria = criteria.exclude(language_scope='arabic')

        for criterion in criteria:
            metric_value = analysis_data.get(criterion.metric_key)
            if metric_value is not None and criterion.weight > 0:
                ideal, weight = criterion.ideal_value, criterion.weight
                if criterion.lower_is_better:
                    score = max(0, 1 - (metric_value / (ideal if ideal > 0 else 1)))
                else:
                    deviation = abs(metric_value - ideal)
                    score = max(0, 1 - (deviation / (ideal if ideal > 0 else 1)))
                total_score += score * weight
                total_weight += weight
        
        analysis_data['final_score'] = (total_score / total_weight) * 10 if total_weight > 0 else None
        
        AnalysisResult.objects.update_or_create(font=font_obj, defaults=analysis_data)
        
    def _message_user_with_traceback(self, request, font_name):
        error_details = traceback.format_exc()
        error_html = format_html("فشل تحليل الخط {} بسبب الخطأ التالي:<pre>{}</pre>", font_name, error_details)
        self.message_user(request, error_html, level='ERROR')

    @admin.action(description="إعادة تحليل الخطوط المحددة")
    def reanalyze_fonts(self, request, queryset):
        for font in queryset:
            try:
                self._perform_analysis(request, font)
            except Exception:
                self._message_user_with_traceback(request, font.font_name)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            self._perform_analysis(request, obj)
        except Exception:
            self._message_user_with_traceback(request, obj.font_name)


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope', 'lower_is_better')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    # تم إرجاع الرسم البياني بعد حذف النسخة المبسطة السابقة
    readonly_fields = ('view_histogram',)
    
    def get_list_display(self, request):
        # التأكد من أن حقل الصورة موجود قبل محاولة عرضه
        fields = [field.name for field in self.model._meta.get_fields() if field.name != 'font']
        if 'width_histogram' in fields:
            fields.remove('width_histogram')
            fields.insert(0, 'view_histogram')
        fields.insert(0, 'font')
        return fields

    def view_histogram(self, obj):
        if hasattr(obj, 'width_histogram') and obj.width_histogram:
            return format_html('<a href="{}"><img src="{}" width="150" /></a>', obj.width_histogram.url, obj.width_histogram.url)
        return "لا يوجد رسم بياني"
    view_histogram.short_description = "رسم توزيع العرض"
    search_fields = ('font__font_name',)
