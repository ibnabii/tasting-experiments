from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework import routers
from rest_framework.schemas import get_schema_view

from tasex import views

router = routers.DefaultRouter()
router.register('experiments', views.ExperimentViewSet, 'experiment')
router.register('panels', views.PanelViewSet, 'panel')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/swagger-ui/', TemplateView.as_view(
        template_name='tasex/swagger-ui.html',
        extra_context={'schema_url':'openapi-schema'}
    ), name='swagger-ui'),
    path('api/openapi/', get_schema_view(
            title="Tasting Experiments",
            version="1.0.0"
    ), name='openapi-schema'),
]
