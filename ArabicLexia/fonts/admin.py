# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
from django.conf import settings
from django.core.files import File
import os
import traceback
from django.utils.html import format_html
import csv

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')
    actions = ['reanalyze_fonts']

    def _perform_analysis(self, request, font_obj):
        """دالة مركزية لتنفيذ عملية التحليل الكاملة."""
        # التأكد من أن مؤشر الملف في البداية قبل القراءة
        font_obj.font_file.seek(0)
        analyzer = FontAnalyzer(font_obj.font_file, font_obj.font_type, font_obj.language_support)
        analysis_data = analyzer.analyze()
        font_obj.font_file.seek(0) # إعادة المؤشر مرة أخرى احتياطًا
        
        # مسح النتائج القديمة لضمان عدم وجود بيانات قديمة
        fields_to_clear = {field.name: None for field in AnalysisResult._meta.fields if field.name not in ['font', 'font_id']}
        result_obj, created = AnalysisResult.objects.update_or_create(font=font_obj, defaults=fields_to_clear)
        
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
            if metric_value is not None and isinstance(metric_value, (int, float)) and criterion.weight > 0:
                ideal, weight = criterion.ideal_value, criterion.weight
                if criterion.lower_is_better:
                    score = max(0, 1 - (metric_value / (ideal if ideal > 0 else 1)))
                else:
                    deviation = abs(metric_value - ideal)
                    score = max(0, 1 - (deviation / (ideal if ideal > 0 else 1)))
                total_score += score * weight
                total_weight += weight
        
        analysis_data['final_score'] = (total_score / total_weight) * 10 if total_weight > 0 else None
        
        # تحديث الكائن بالبيانات الجديدة والدرجة النهائية
        for key, value in analysis_data.items():
            if hasattr(result_obj, key):
                setattr(result_obj, key, value)
        
        # إنشاء وحفظ الرسم البياني
        histogram_path = analyzer.generate_width_histogram(
            output_dir=os.path.join(settings.MEDIA_ROOT, 'analysis_reports'),
            font_id=font_obj.id,
            font_name=font_obj.font_name
        )
        if histogram_path and os.path.exists(histogram_path):
            with open(histogram_path, 'rb') as f:
                result_obj.width_histogram.save(os.path.basename(histogram_path), File(f))
            os.remove(histogram_path)
            
        result_obj.save()

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
    list_filter = ('language_scope',)
    search_fields = ('criterion_name', 'metric_key')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    readonly_fields = ('view_histogram',)
    actions = ['export_as_csv']
    
    def get_list_display(self, request):
        fields = [field.name for field in self.model._meta.fields if field.name not in ['font', 'width_histogram']]
        fields.insert(0, 'view_histogram')
        fields.insert(0, 'font')
        return fields

    def view_histogram(self, obj):
        if hasattr(obj, 'width_histogram') and obj.width_histogram:
            return format_html('<a href="{}"><img src="{}" width="150" /></a>', obj.width_histogram.url, obj.width_histogram.url)
        return "لا يوجد رسم بياني"
    view_histogram.short_description = "رسم توزيع العرض"
    search_fields = ('font__font_name',)
    
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = ['font'] + [field.name for field in meta.fields if field.name not in ['font', 'width_histogram']]
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response.write('\ufeff'.encode('utf8'))
        response['Content-Disposition'] = f'attachment; filename=analysis_results.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        arabic_fonts = queryset.filter(font__language_support='arabic_only').select_related('font')
        latin_fonts = queryset.filter(font__language_support='latin_only').select_related('font')
        bilingual_fonts = queryset.filter(font__language_support='bilingual').select_related('font')
        def write_rows(qs):
            for obj in qs:
                row = [str(obj.font)] + [getattr(obj, field) for field in field_names[1:]]
                writer.writerow(row)
        if arabic_fonts.exists(): writer.writerow(['--- ARABIC-ONLY FONTS ---']); write_rows(arabic_fonts)
        if latin_fonts.exists(): writer.writerow(['--- LATIN-ONLY FONTS ---']); write_rows(latin_fonts)
        if bilingual_fonts.exists(): writer.writerow(['--- BILINGUAL FONTS ---']); write_rows(bilingual_fonts)
        return response
    export_as_csv.short_description = "تصدير النتائج المحددة إلى ملف CSV"