import qrcode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import reverse
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
    queryset = Panel.objects.filter(is_active=True)


def render_qr_code(request, pk):

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=5,
        border=4,
    )
    qr.add_data(
        request.build_absolute_uri(reverse('tasex:panel', kwargs={'pk': pk}))
    )
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    response = HttpResponse(content_type="image/png")
    img.save(response, 'PNG')
    return response
