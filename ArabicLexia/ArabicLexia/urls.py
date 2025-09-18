# ArabicLexia/urls.py
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView # استيراد أداة إعادة التوجيه

urlpatterns = [
    # -- هذا هو السطر الجديد --
    # يقوم بتوجيه أي زيارة للصفحة الرئيسية إلى لوحة التحكم
    path("", RedirectView.as_view(url="/admin/", permanent=False)),
    
    path("admin/", admin.site.urls),
]

# هذا الجزء يبقى كما هو لعرض الصور
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)