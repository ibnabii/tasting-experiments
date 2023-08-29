import qrcode

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import BadRequest, PermissionDenied, ValidationError
# from django.db.models import Q
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import reverse
from django.views.generic import DetailView, FormView, ListView, RedirectView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions

from .forms import FORM_CLASSES, PanelQuestionsForm
from .models import Experiment, Panel, Sample, SampleSet, Product, Result, PanelQuestion, Answer

from .serializers import ExperimentSerializer, PanelSerializer
from .utils import PanelResult, SurveyPlots


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        panel = self.kwargs.get('pk')
        context['statuses'] = Panel.PanelStatus
        if panel:
            results = Result.objects.filter(sample_set__in=SampleSet.objects.filter(panel_id=panel))
            context['results'] = results.count()
            answers = Answer.objects.filter(result__in=results)
            questions = PanelQuestion.objects.filter(panel_id=panel)
            context['answers'] = answers.count() // questions.count()
        return context


class ResultsView(DetailView):
    model = Panel
    template_name = 'tasex/panel_results.html'
    context_object_name = 'panel'

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context["panel_result"] = PanelResult(self.object)
        context["survey_plots"] = SurveyPlots(self.object)
        return context


class PanelState:
    def __init__(self, panel_id, step=1, sample_set=None, result=None):
        self.panel_id = panel_id
        self.step = step
        self.sample_set = sample_set
        self.result = result


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
            if are_samples_correct == 'False':
                # reset panel
                self.panel_state = PanelState(self.panel_id)
            if are_samples_correct == 'True':
                sample_set = SampleSet.objects.filter(id=self.panel_state.sample_set).update(is_used=True)

            odd_sample = form.cleaned_data.get('odd_sample')
            if odd_sample:
                self.panel_state.result = Result.objects.create(
                    sample_set=SampleSet.objects.get(id=self.panel_state.sample_set),
                    odd_sample=Sample.objects.get(id=odd_sample)
                )
                self.panel_state.result = self.panel_state.result.id

            self.request.session.get('panels')[self.panel_id] = self.panel_state.__dict__
            self.request.session.save()

        return HttpResponseRedirect(self.get_success_url())

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


class PanelQuestionsView(FormView):
    form_class = PanelQuestionsForm
    template_name = 'tasex/panel_questions.html'

    def __init__(self):
        super().__init__()
        self.panel_id = None
        self.panel_state = None

    def setup(self, request, *args, **kwargs):
        self.panel_id = kwargs.get('pk')
        self.panel_state = PanelState(**request.session.get('panels').get(self.panel_id))
        return super().setup(request, *args, **kwargs)

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        # form_kwargs['panel_state'] = self.panel_state
        form_kwargs['questions'] = PanelQuestion.objects.filter(panel_id=self.panel_id)
        return form_kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_a = Panel.objects.get(id=self.panel_id).experiment.product_A
        result = Result.objects.get(id=self.panel_state.result)
        odd = result.odd_sample
        other = list(result.sample_set.samples.values_list('code', flat=True))
        other.remove(odd.code)
        if odd.product == product_a:
            context['product_a'] = [odd.code]
            context['product_b'] = other
        else:
            context['product_b'] = [odd.code]
            context['product_a'] = other

        return context

    def form_valid(self, form):
        # increment panel_state.step
        self.panel_state.step += 1
        self.request.session.get('panels')[self.panel_id] = self.panel_state.__dict__
        self.request.session.save()

        # save answers
        result = Result.objects.get(id=self.panel_state.result)
        if Answer.objects.filter(result=result).exists():
            raise ValidationError('Answers already recorded')
        for question in PanelQuestion.objects.filter(panel_id=self.panel_id):
            answer = form.cleaned_data.get(str(question.id))
            if answer:
                answer_text = question.scale.points.get(code=answer).text
                Answer.objects.create(
                    question=question,
                    result=result,
                    answer_code=answer,
                    answer_text=answer_text
                )
        return HttpResponseRedirect(
            reverse('tasex:panel', kwargs={'pk': self.kwargs.get('pk')})
        )


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
                return ResultsView.as_view()(request, *args, **kwargs)

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
                elif step == len(FORM_CLASSES) + 1:
                    return PanelQuestionsView.as_view()(request, *args, **kwargs)
                else:
                    self.template_name = 'tasex/panel_wait_for_finish.html'
            case _:
                # for debug
                raise BadRequest(f'I do not know what to do with panel status {self.get_object().status}')
        return super().dispatch(request, *args, **kwargs)


class UpdatePanelStatusView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('tasex:panel', kwargs={'pk': self.kwargs.get('pk')})

    def get(self, request, *args, **kwargs):
        new_status = self.kwargs.get('status')
        if new_status in Panel.PanelStatus:
            Panel.objects.filter(id=self.kwargs.get('pk')).update(status=new_status)
        return super().get(request, *args, **kwargs)


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
