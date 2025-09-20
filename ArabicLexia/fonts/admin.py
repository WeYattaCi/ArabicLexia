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
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        # Reset file pointer before analysis
        font_obj.font_file.seek(0)
        analyzer = FontAnalyzer(font_obj.font_file, font_obj.font_type, font_obj.language_support)
        analysis_data = analyzer.analyze()
        font_obj.font_file.seek(0)
        
        # Clear old results to prevent stale data
        fields_to_clear = {field.name: None for field in AnalysisResult._meta.fields if field.name not in ['font', 'font_id']}
        result_obj, _ = AnalysisResult.objects.update_or_create(font=font_obj, defaults=fields_to_clear)

        # Update with new data
        for key, value in analysis_data.items():
            if hasattr(result_obj, key):
                setattr(result_obj, key, value)
        
        # Final Score Calculation
        # ... (This logic can be restored here)
        result_obj.save()

    @admin.action(description="إعادة تحليل الخطوط المحددة")
    def reanalyze_fonts(self, request, queryset):
        for font in queryset:
            try:
                self._perform_analysis(request, font)
                self.message_user(request, f"تمت إعادة تحليل الخط: {font.font_name}")
            except Exception as e:
                # ...
                pass
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            self._perform_analysis(request, obj)
            self.message_user(request, "تم حفظ وتحليل الخط بنجاح.")
        except Exception as e:
            # ...
            pass
# ... (CriterionAdmin and AnalysisResultAdmin remain the same)