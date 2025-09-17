# fonts/admin.py
from django.contrib import admin
from .models import Font, Criterion, AnalysisResult
import subprocess
import json
import sys

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('font_name', 'designer', 'classification', 'language_support', 'upload_date')
    list_filter = ('classification', 'language_support', 'font_type')
    search_fields = ('font_name', 'designer')

    def save_model(self, request, obj, form, change):
        # الخطوة الأولى: حفظ الخط أولاً ليتم إنشاء الملف على الخادم
        super().save_model(request, obj, form, change)

        try:
            # الخطوة الثانية: تشغيل سكربت التحليل
            # نستخدم sys.executable لضمان استخدام نفس بيئة بايثون التي يعمل بها المشروع
            result = subprocess.run(
                [sys.executable, 'fonts/analyzer.py', obj.font_file.path, obj.font_type],
                capture_output=True, text=True, check=True, encoding='utf-8'
            )
            
            # قراءة النتائج التي أرجعها السكربت
            analysis_data = json.loads(result.stdout)
            
            # الخطوة الثالثة: حساب الدرجة النهائية
            total_score = 0
            total_weight = 0
            
            # فلترة المعايير بناءً على دعم الخط للغة
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
                    # المعادلة الحسابية للدرجة
                    score = max(0, 1 - (deviation / (ideal * 2 if ideal != 0 else 1)))
                    
                    total_score += score * weight
                    total_weight += weight
            
            final_score_value = (total_score / total_weight) * 10 if total_weight > 0 else None
            analysis_data['final_score'] = final_score_value

            # الخطوة الرابعة: حفظ كل النتائج في قاعدة البيانات
            AnalysisResult.objects.update_or_create(
                font=obj, defaults=analysis_data
            )
            self.message_user(request, "تم حفظ وتحليل الخط بنجاح.")

        except subprocess.CalledProcessError as e:
            # في حال فشل سكربت التحليل، اعرض الخطأ للمستخدم
            error_output = e.stderr
            self.message_user(request, f"تم حفظ الخط، ولكن فشل التحليل: {error_output}", level='ERROR')
        except Exception as e:
            self.message_user(request, f"حدث خطأ غير متوقع أثناء حساب الدرجة النهائية: {e}", level='ERROR')

@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ('criterion_name', 'metric_key', 'ideal_value', 'weight', 'language_scope')
    list_filter = ('language_scope',)
    search_fields = ('criterion_name', 'metric_key')

@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    # عرض كل حقول النتائج في لوحة التحكم
    list_display = [field.name for field in AnalysisResult._meta.fields]
    search_fields = ('font__font_name',)