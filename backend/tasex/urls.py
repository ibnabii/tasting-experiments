from django.urls import path

from .views import AdminPanelView

app_name = 'tasex'

urlpatterns = [
    path('<pk>/', AdminPanelView.as_view(), name='panel'),
]