import qrcode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest, PermissionDenied
# from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import reverse
from django.views.generic import DetailView, FormView, ListView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions

from .serializers import ExperimentSerializer, PanelSerializer
from .models import Experiment, Panel, Sample, SampleSet, Product


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


class SamplePreparationView(LoginRequiredMixin, ListView):
    raise_exception = True
    template_name = 'tasex/owner_panel_products.html'
    context_object_name = 'products'

    def get_queryset(self):
        # Sample.objects.filter(sample_set__panel_id=self.kwargs['pk']).select_related('product')
        products = (Panel.objects
                    .filter(id=self.kwargs['pk'])
                    .values_list('experiment__product_A', 'experiment__product_B'))
        return Product.objects.filter(pk__in=list(*products))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['samplesA'] = (
            Sample.objects
            .filter(product_id=context['products'][0])
            .filter(sample_set__panel_id=self.kwargs['pk']))
        context['samplesB'] = (
            Sample.objects
            .filter(product_id=context['products'][1])
            .filter(sample_set__panel_id=self.kwargs['pk']))

        return context



class SampleSetsView(LoginRequiredMixin, ListView):
    raise_exception = True
    template_name = 'tasex/owner_panel_sets.html'
    context_object_name = 'sample_sets'

    def get_queryset(self):
        return SampleSet.objects.filter(panel_id=self.kwargs['pk']).prefetch_related('samples')

class AdminPanelView(LoginRequiredMixin, DetailView):
    template_name = 'tasex/admin_panel.html'
    model = Panel
    # 404 instead of redirect to login page for not logged-in user
    # raise_exception = True


# class PanelStep1(FormView):
#     def get_form_kwargs(self):
#         form_kwargs = super().get_form_kwargs()
#         if 'pk' in self.kwargs:
#             form_kwargs['samples'] = Sample.objects.get(pk=int(self.kwargs['pk']))
#         return form_kwargs

class PanelStep1(DetailView):
    model = Panel
    template_name = 'tasex/panel_step_1.html'

    def dispatch(self, request, *args, **kwargs):
        panel_id = str(self.get_object().id)
        request.session.get('panels').update({panel_id: 2})
        return super().dispatch(request, *args, **kwargs)


class AnonymousPanelView(DetailView):
    model = Panel
    template_name = 'tasex/panel_closed.html'

    # this one is equivalent to raising Http404 based on panel_status in dispatch()
    # queryset = Panel.objects.filter(~Q(status=Panel.PanelStatus.HIDDEN))

    def dispatch(self, request, *args, **kwargs):
        # decide what to serve depending on panel status
        match self.get_object().status:
            # this condition is the equivalent of defining queryset to skip HIDDEN
            case Panel.PanelStatus.HIDDEN:
                raise PermissionDenied
            case Panel.PanelStatus.PLANNED:
                self.template_name = 'tasex/panel_planned.html'
            case Panel.PanelStatus.PRESENTING_RESULTS:
                self.template_name = 'tasex/panel_results.html'

            case Panel.PanelStatus.ACCEPTING_ANSWERS:
                # if panel is accepting_answers, the status of the user will be saved
                panel_id = str(self.get_object().id)

                # save session
                if not request.session or not request.session.session_key:
                    request.session['panels'] = {}
                    request.session.save()
                # update session with this panel
                if not request.session.get('panels', {}).get(panel_id):
                    request.session.get('panels').update({panel_id: 1})
                    request.session.save()

                # check user status
                match request.session.get('panels', {}).get(panel_id):
                    case 1:
                        return PanelStep1.as_view()(request, *args, **kwargs)
                    case _:
                        self.template_name = 'tasex/panel_wait_for_finish.html'
            case _:
                # for debug
                raise BadRequest(f'I do not know what to do with panel status {self.get_object().status}')
        return super().dispatch(request, *args, **kwargs)


class PanelView(DetailView):

    def dispatch(self, request, *args, **kwargs):
        # serve another view if dealing with anonymous user
        if request.user.is_anonymous:
            return AnonymousPanelView.as_view()(request, *args, **kwargs)
        else:
            return AdminPanelView.as_view()(request, *args, **kwargs)


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
