from django.urls import path

from .views import PanelView, render_qr_code, SampleSetsView, SamplePreparationView

app_name = 'tasex'

urlpatterns = [
    path('<pk>/', PanelView.as_view(), name='panel'),
    path('<pk>/qr/', render_qr_code, name='panel-qr'),
    path('<pk>/sets/', SampleSetsView.as_view(), name='panel-sets'),
    path('<pk>/products/', SamplePreparationView.as_view(), name='panel-prepare'),
]