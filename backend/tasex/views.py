import qrcode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest, PermissionDenied
# from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic import DetailView, FormView, ListView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions

from .forms import FORM_CLASSES
from .models import Experiment, Panel, Sample, SampleSet, Product
from .serializers import ExperimentSerializer, PanelSerializer


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


class PanelState:
    def __init__(self, panel_id, step=1, sample_set=None):
        self.panel_id = panel_id
        self.step = step
        self.sample_set = sample_set


class PanelStep1(FormView):
    # form_class = SingleSampleForm
    template_name = 'tasex/panel_step_1.html'

    def __init__(self):
        super().__init__()
        self.panel_id = None
        self.panel_state = None

    def form_valid(self, form):
        if form.is_valid():
            self.panel_state.step += 1

            sample_set_id = form.cleaned_data.get('sample_set_id')
            if sample_set_id:
                self.panel_state.sample_set = sample_set_id

            are_samples_correct = form.cleaned_data.get('are_samples_correct')
            print('are_samples_correct', are_samples_correct)
            if are_samples_correct == 'False':
                # reset panel
                self.panel_state = PanelState(self.panel_id)

            self.request.session.get('panels')[self.panel_id] = self.panel_state.__dict__
            self.request.session.save()

        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, form):
        print('form_invalid')
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse('tasex:panel', kwargs={'pk': self.kwargs.get('pk')})

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs['panel_state'] = self.panel_state
        return form_kwargs

    def get_form_class(self):
        return FORM_CLASSES.get(self.panel_state.step)

    def setup(self, request, *args, **kwargs):
        self.panel_id = kwargs.get('pk')
        self.panel_state = PanelState(**request.session.get('panels').get(self.panel_id))
        return super().setup(request, *args, **kwargs)


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
                    request.session.get('panels')[panel_id] = PanelState(panel_id).__dict__
                    request.session.save()

                # check user status
                step = (request.session.get('panels', {}).get(panel_id, {}).get('step'))
                if step in FORM_CLASSES:
                    return PanelStep1.as_view()(request, *args, **kwargs)
                else:
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
    if (
        request.user.is_anonymous
        and
        Panel.objects.filter(id=pk).values_list('status')[0][0] == Panel.PanelStatus.HIDDEN
    ):
        raise PermissionDenied
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
