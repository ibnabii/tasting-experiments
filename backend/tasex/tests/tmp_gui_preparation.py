from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Experiment, Product, Panel, SampleSet, Sample


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
        response = c.get(self.panel_hidden.get_absolute_url())
        self.assertEquals(response.status_code, 403)

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

        response = c.get(self.panel_accepting.get_absolute_url())
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        response = c.get(self.panel_accepting.get_absolute_url())
        self.assertTemplateUsed(response, 'tasex/panel_wait_for_finish.html')

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
