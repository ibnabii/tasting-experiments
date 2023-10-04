from django.urls import path

from .views import IndexView, ChangePanelStatusView, ResetPanelView, GeneratePanelAnswersView


app_name = 'demo'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('status/', ChangePanelStatusView.as_view(), name='change_panel_status'),
    path('reset/', ResetPanelView.as_view(), name='reset_panel'),
    path('randomize/', GeneratePanelAnswersView.as_view(), name='randomize_panel'),
]
