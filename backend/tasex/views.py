from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import DetailView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions

from .serializers import ExperimentSerializer, PanelSerializer
from .models import Experiment, Panel


class ExperimentViewSet(viewsets.ModelViewSet):
    serializer_class = ExperimentSerializer
    queryset = Experiment.objects.all()
    permission_classes = [permissions.IsAuthenticated]


class PanelViewSet(viewsets.ModelViewSet):
    serializer_class = PanelSerializer
    queryset = Panel.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ('experiment', 'is_active')
    permission_classes = [permissions.IsAuthenticated]


class AdminPanelView(LoginRequiredMixin, DetailView):
    template_name = 'tasex/admin_panel.html'
    model = Panel