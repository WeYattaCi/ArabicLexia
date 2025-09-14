# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')

@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope')
    list_filter = ('language_scope',)
    search_fields = ('criterion_name', 'metric_key')

admin.site.register(AnalysisResult)