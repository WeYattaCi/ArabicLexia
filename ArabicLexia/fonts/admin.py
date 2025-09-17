# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
import json
import sys
from django.conf import settings
from django.core.files import File
import os
import csv
from django.http import HttpResponse
from django.utils.html import format_html # <-- تم إضافة هذا السطر

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        try:
            analyzer = FontAnalyzer(obj.font_file.path, obj.font_type)
            analysis_data = analyzer.analyze()
            
            total_score = 0
            total_weight = 0
            criteria = Criterion.objects.all()
            if obj.language_support == 'arabic_only':
                criteria = criteria.exclude(language_scope='latin')
            elif obj.language_support == 'latin_only':
                criteria = criteria.exclude(language_scope='arabic')

            for criterion in criteria:
                metric_value = analysis_data.get(criterion.metric_key)
                if metric_value is not None and criterion.weight > 0:
                    ideal = criterion.ideal_value
                    weight = criterion.weight
                    deviation = abs(metric_value - ideal)
                    score = max(0, 1 - (deviation / (ideal * 2 if ideal != 0 else 1)))
                    total_score += score * weight
                    total_weight += weight
            
            final_score_value = (total_score / total_weight) * 10 if total_weight > 0 else None
            analysis_data['final_score'] = final_score_value

            histogram_path = analyzer.generate_width_histogram(
                output_dir=os.path.join(settings.MEDIA_ROOT, 'analysis_reports'),
                font_id=obj.id
            )

            result_obj, created = AnalysisResult.objects.update_or_create(
                font=obj, defaults=analysis_data
            )

            with open(histogram_path, 'rb') as f:
                result_obj.width_histogram.save(os.path.basename(histogram_path), File(f), save=True)
            
            os.remove(histogram_path)

            self.message_user(request, "تم حفظ وتحليل الخط وإنشاء الرسم البياني بنجاح.")

        except Exception as e:
            self.message_user(request, f"حدث خطأ: {e}", level='ERROR')


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope')
    list_filter = ('language_scope',)
    search_fields = ('criterion_name', 'metric_key')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    
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

        if arabic_fonts.exists():
            writer.writerow(['--- ARABIC-ONLY FONTS ---'])
            write_rows(arabic_fonts)
        
        if latin_fonts.exists():
            writer.writerow(['--- LATIN-ONLY FONTS ---'])
            write_rows(latin_fonts)

        if bilingual_fonts.exists():
            writer.writerow(['--- BILINGUAL FONTS ---'])
            write_rows(bilingual_fonts)

        return response
    export_as_csv.short_description = "تصدير النتائج المحددة إلى ملف CSV"

    actions = ["export_as_csv"]

    def get_list_display(self, request):
        fields = [field.name for field in self.model._meta.fields if field.name != 'width_histogram']
        fields.insert(1, 'view_histogram')
        return fields

    def view_histogram(self, obj):
        if obj.width_histogram:
            # تم تصحيح هذا السطر: أزلنا self من format_html
            return format_html('<a href="{}"><img src="{}" width="150" /></a>', obj.width_histogram.url, obj.width_histogram.url)
        return "لا يوجد رسم بياني"
    view_histogram.short_description = "رسم توزيع العرض"
    
    search_fields = ('font__font_name',)
    readonly_fields = ('view_histogram',)# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
from .analyzer import FontAnalyzer
import json
import sys
from django.conf import settings
from django.core.files import File
import os
import csv
from django.http import HttpResponse
from django.utils.html import format_html # <-- تم إضافة هذا السطر

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        try:
            analyzer = FontAnalyzer(obj.font_file.path, obj.font_type)
            analysis_data = analyzer.analyze()
            
            total_score = 0
            total_weight = 0
            criteria = Criterion.objects.all()
            if obj.language_support == 'arabic_only':
                criteria = criteria.exclude(language_scope='latin')
            elif obj.language_support == 'latin_only':
                criteria = criteria.exclude(language_scope='arabic')

            for criterion in criteria:
                metric_value = analysis_data.get(criterion.metric_key)
                if metric_value is not None and criterion.weight > 0:
                    ideal = criterion.ideal_value
                    weight = criterion.weight
                    deviation = abs(metric_value - ideal)
                    score = max(0, 1 - (deviation / (ideal * 2 if ideal != 0 else 1)))
                    total_score += score * weight
                    total_weight += weight
            
            final_score_value = (total_score / total_weight) * 10 if total_weight > 0 else None
            analysis_data['final_score'] = final_score_value

            histogram_path = analyzer.generate_width_histogram(
                output_dir=os.path.join(settings.MEDIA_ROOT, 'analysis_reports'),
                font_id=obj.id
            )

            result_obj, created = AnalysisResult.objects.update_or_create(
                font=obj, defaults=analysis_data
            )

            with open(histogram_path, 'rb') as f:
                result_obj.width_histogram.save(os.path.basename(histogram_path), File(f), save=True)
            
            os.remove(histogram_path)

            self.message_user(request, "تم حفظ وتحليل الخط وإنشاء الرسم البياني بنجاح.")

        except Exception as e:
            self.message_user(request, f"حدث خطأ: {e}", level='ERROR')


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope')
    list_filter = ('language_scope',)
    search_fields = ('criterion_name', 'metric_key')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    
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

        if arabic_fonts.exists():
            writer.writerow(['--- ARABIC-ONLY FONTS ---'])
            write_rows(arabic_fonts)
        
        if latin_fonts.exists():
            writer.writerow(['--- LATIN-ONLY FONTS ---'])
            write_rows(latin_fonts)

        if bilingual_fonts.exists():
            writer.writerow(['--- BILINGUAL FONTS ---'])
            write_rows(bilingual_fonts)

        return response
    export_as_csv.short_description = "تصدير النتائج المحددة إلى ملف CSV"

    actions = ["export_as_csv"]

    def get_list_display(self, request):
        fields = [field.name for field in self.model._meta.fields if field.name != 'width_histogram']
        fields.insert(1, 'view_histogram')
        return fields

    def view_histogram(self, obj):
        if obj.width_histogram:
            # تم تصحيح هذا السطر: أزلنا self من format_html
            return format_html('<a href="{}"><img src="{}" width="150" /></a>', obj.width_histogram.url, obj.width_histogram.url)
        return "لا يوجد رسم بياني"
    view_histogram.short_description = "رسم توزيع العرض"
    
    search_fields = ('font__font_name',)
    readonly_fields = ('view_histogram',)