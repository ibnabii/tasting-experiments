from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Experiment, Product, Panel, SampleSet, Sample, PanelQuestion, QuestionSet
from ..forms import FORM_CLASSES


class PanelViewTest(TestCase):
    fixtures = ['test_base', 'test_panel_status']

    def setUp(self):
        self.panel_accepting = Panel.objects.get(description='Panel_accepting')
        self.panel_hidden = Panel.objects.get(description='Panel_hidden')
        self.panel_planned = Panel.objects.get(description='Panel_planned')
        self.panel_results = Panel.objects.get(description='Panel_results')

        self.user_super_pswd = '&!ep$o2Xf#e55#4&n!^$YZUsRLNmF9L36pS9%C*4L7MGdp#w%^b4@W%xY5#9&i'
        self.user_super = User.objects.create_superuser('super_user', 'mail@mail.com', self.user_super_pswd)

    def test_anonymous_user_cannot_access(self):
        c = Client()
        # panel in hidden status
        response = c.get(self.panel_hidden.get_absolute_url())
        self.assertEquals(response.status_code, 403)
        response = c.get(reverse('tasex:panel-qr', kwargs={'pk': self.panel_hidden.id}))
        self.assertEquals(response.status_code, 403)
        response = c.get(reverse('tasex:panel-sets', kwargs={'pk': self.panel_hidden.id}))
        self.assertEquals(response.status_code, 403)
        response = c.get(reverse('tasex:panel-prepare', kwargs={'pk': self.panel_hidden.id}))
        self.assertEquals(response.status_code, 403)

        # admin views for panel in accepting status
        # view with sets
        response = c.get(reverse('tasex:panel-sets', kwargs={'pk': self.panel_accepting.id}))
        self.assertEquals(response.status_code, 403)
        # view for preparation (samples by product)
        response = c.get(reverse('tasex:panel-prepare', kwargs={'pk': self.panel_accepting.id}))
        self.assertEquals(response.status_code, 403)

    def test_anonymous_user_can_access(self):
        c = Client()
        response = c.get(self.panel_planned.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/panel_planned.html')

        response = c.get(self.panel_results.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/panel_results.html')

        for i in range(len(FORM_CLASSES)):
            response = c.get(self.panel_accepting.get_absolute_url())
            self.assertEquals(response.status_code, 200)
            self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
            s = c.session
            s.get('panels').get(str(self.panel_accepting.id))['step'] += 1
            s.save()

        response = c.get(self.panel_accepting.get_absolute_url())
        self.assertTemplateUsed(response, 'tasex/panel_wait_for_finish.html')
        response = c.get(reverse('tasex:panel-qr', kwargs={'pk': self.panel_accepting.id}))
        self.assertEquals(response.status_code, 200)

    def test_superuser_can_access(self):
        c = Client()
        c.force_login(self.user_super)

        response = c.get(self.panel_hidden.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/admin_panel.html')

        response = c.get(self.panel_accepting.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/admin_panel.html')

        response = c.get(self.panel_planned.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/admin_panel.html')

        response = c.get(self.panel_results.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/admin_panel.html')


class PanelAdmin(TestCase):
    fixtures = ['questions', 'test_base']

    def setUp(self):
        self.question_set = QuestionSet.objects.get(id=6660001)
        self.panel_data = {
            'experiment': 'aaa66601-3b2e-4695-bc78-d1becc8428c7',
            'description': 'Test description',
            'planned_panelists': 3,
            'show_exp_description': 'NO',
            'status': 'PLANNED',
            'create_questions': 'blank',
        }
        self.url = '/admin/tasex/panel/add/'
        self.user_super = User.objects.create_superuser('super_user', 'mail@mail.com', 'super_password')
        self.c = Client()
        self.c.force_login(self.user_super)

    def verify_samples(self):
        self.assertEquals(
            SampleSet.objects.count(),
            self.panel_data.get('planned_panelists', None)
        )
        self.assertEquals(
            Sample.objects.count(),
            self.panel_data.get('planned_panelists') * 3
        )

    def create_panel(self):
        response = self.c.post(self.url, follow=True, data=self.panel_data)
        self.assertEquals(response.status_code, 200)
        return response

    def verify_panel_questions_count(self, expected):
        self.assertEquals(
            PanelQuestion.objects.count(),
            expected
        )

    def experiment_add_question_set(self):
        Experiment.objects.filter(id=self.panel_data.get('experiment')).update(question_set=self.question_set)

    def test_questions_exp_no_default_panel_blank(self):
        self.create_panel()
        self.verify_samples()
        self.verify_panel_questions_count(0)

    def test_questions_exp_no_default_panel_copy(self):
        self.panel_data.update({'create_questions': 'copy'})
        self.create_panel()
        self.verify_samples()
        self.verify_panel_questions_count(0)

    def test_questions_exp_basic_panel_blank(self):
        self.experiment_add_question_set()
        self.create_panel()
        self.verify_samples()
        self.verify_panel_questions_count(0)

    def test_questions_exp_basic_default_panel_copy(self):
        self.experiment_add_question_set()
        self.panel_data.update({'create_questions': 'copy'})
        self.create_panel()
        self.verify_samples()
        self.verify_panel_questions_count(self.question_set.questions.count())
        for question_order in self.question_set.question_order.all():
            panel_question = PanelQuestion.objects.get(question_text=question_order.question.question_text)
            self.assertEquals(panel_question.order, question_order.order)
            self.assertEquals(panel_question.scale, question_order.question.scale)
