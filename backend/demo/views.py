from django.urls import reverse_lazy
from django.views.generic import TemplateView, RedirectView, View


from .utils import (ensure_demo_data, get_indistinguishable_result_id,
                    get_significant_result_id, get_session_panel, reset_panel, create_panel_results)
from tasex.models import Panel, Sample, SampleSet


class IndexView(TemplateView):
    template_name = 'demo/index.html'

    def dispatch(self, request, *args, **kwargs):
        # create session for anonymous user
        if not request.session or not request.session.session_key:
            request.session.save()
        # check and create demo data for session
        ensure_demo_data(request.session.session_key)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['result_significant_id'] = get_significant_result_id()
        context['result_indistinguishable_id'] = get_indistinguishable_result_id()
        context['panel'] = get_session_panel(self.request.session.session_key)
        sample_sets = SampleSet.objects.filter(panel=context['panel']).filter(is_used=False)
        context['sample_set'] = Sample.objects.filter(
            sample_set=sample_sets.first()
        ).values_list('code', flat=True)
        context['is_panel_full'] = sample_sets.count() == 0
        context['current_tab'] = self.request.session.get('current_tab')
        return context


class SetOwnPanelTabView(View):
    def dispatch(self, request, *args, **kwargs):
        request.session['current_tab'] = 'own_panel'
        request.session.save()
        return super().dispatch(request, *args, **kwargs)


class ChangePanelStatusView(RedirectView, SetOwnPanelTabView):
    url = reverse_lazy('demo:index')

    def post(self, request, *args, **kwargs):
        next_status = request.POST.get('set_status')
        if next_status in Panel.PanelStatus:
            panel = get_session_panel(request.session.session_key)
            panel.status = next_status
            panel.save()
        return super().post(request, *args, **kwargs)


class ResetPanelView(RedirectView, SetOwnPanelTabView):
    url = reverse_lazy('demo:index')

    def get(self, request, *args, **kwargs):
        reset_panel(get_session_panel(request.session.session_key))
        return super().get(request, *args, **kwargs)


class GeneratePanelAnswersView(RedirectView, SetOwnPanelTabView):
    url = reverse_lazy('demo:index')

    def post(self, request, *args, **kwargs):
        mode = request.POST.get('mode')
        panel = get_session_panel(request.session.session_key)
        if mode == 'different':
            probability = 0.95
        else:
            probability = 0.33
        create_panel_results(panel, probability, (0.7, 0.1, 0.2))
        return super().post(request, *args, **kwargs)