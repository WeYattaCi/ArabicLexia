# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
from django.conf import settings
from django.core.files import File
import os
import traceback
from django.utils.html import format_html

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        analyzer = FontAnalyzer(font_obj.font_file.path, font_obj.font_type, font_obj.language_support)
        analysis_data = analyzer.analyze()
        
        total_score = 0
        total_weight = 0
        criteria = Criterion.objects.all()
        # ... (بقية كود حساب الدرجة النهائية) ...
        
        AnalysisResult.objects.update_or_create(font=font_obj, defaults=analysis_data)

    def _message_user_with_traceback(self, request, font_name, e):
        # ... (الكود هنا لم يتغير) ...
        pass

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
    # ... (الكود هنا لم يتغير) ...
    pass

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    # ... (الكود هنا لم يتغير) ...
    pass