from django.urls import path

from .views import AdminPanelView, PanelView, render_qr_code

app_name = 'tasex'

urlpatterns = [
    path('<pk>/', PanelView.as_view(), name='panel'),
    path('<pk>/qr/', render_qr_code, name='panel-qr'),
]