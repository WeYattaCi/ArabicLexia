# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
from django.conf import settings
from django.core.files import File
import os
import csv
from django.http import HttpResponse
from django.utils.html import format_html
import traceback

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        # --- هذا هو السطر الذي تم إصلاحه ليتوافق مع المحلل ---
        analyzer = FontAnalyzer(font_obj.font_file.path, font_obj.font_type, font_obj.language_support)
        analysis_data = analyzer.analyze()
        
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
            if metric_value is not None and metric_value is not False and criterion.weight > 0:
                ideal, weight = criterion.ideal_value, criterion.weight
                if criterion.lower_is_better:
                    score = max(0, 1 - (metric_value / (ideal if ideal > 0 else 1)))
                else:
                    deviation = abs(metric_value - ideal)
                    score = max(0, 1 - (deviation / (ideal if ideal > 0 else 1)))
                total_score += score * weight
                total_weight += weight
        
        analysis_data['final_score'] = (total_score / total_weight) * 10 if total_weight > 0 else None
        
        result_obj, _ = AnalysisResult.objects.update_or_create(font=font_obj, defaults=analysis_data)
        
        histogram_path = analyzer.generate_width_histogram(
            output_dir=os.path.join(settings.MEDIA_ROOT, 'analysis_reports'),
            font_id=font_obj.id,
            font_name=font_obj.font_name
        )
        if histogram_path and os.path.exists(histogram_path):
            with open(histogram_path, 'rb') as f:
                result_obj.width_histogram.save(os.path.basename(histogram_path), File(f), save=True)
            os.remove(histogram_path)

    def _message_user_with_traceback(self, request, font_name, e):
        error_details = traceback.format_exc()
        error_html = format_html("فشل تحليل الخط {} بسبب الخطأ التالي:<br><strong>{}</strong><pre>{}</pre>", font_name, str(e), error_details)
        self.message_user(request, error_html, level='ERROR')

    @admin.action(description="إعادة تحليل الخطوط المحددة")
    def reanalyze_fonts(self, request, queryset):
        for font in queryset:
            try:
                self._perform_analysis(request, font)
                self.message_user(request, f"تمت إعادة تحليل الخط: {font.font_name}")
            except Exception as e:
                self._message_user_with_traceback(request, font.font_name, e)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            self._perform_analysis(request, obj)
            self.message_user(request, "تم حفظ وتحليل الخط بنجاح.")
        except Exception as e:
            self._message_user_with_traceback(request, obj.font_name, e)


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope', 'lower_is_better')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    readonly_fields = ('view_histogram',)
    
    def get_list_display(self, request):
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