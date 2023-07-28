from django.urls import path

from .views import AdminPanelView, render_qr_code

app_name = 'tasex'

urlpatterns = [
    path('<pk>/', AdminPanelView.as_view(), name='panel'),
    path('<pk>/qr/', render_qr_code, name='panel-qr'),
]