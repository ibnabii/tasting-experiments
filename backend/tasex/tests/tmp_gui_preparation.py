from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client

from ..models import Experiment, Product, Panel, SampleSet, Sample


class PanelViewTest(TestCase):
    fixtures = ['auto_test_data']

    def setUp(self):
        self.exp = Experiment.objects.get(id='aaa66601-3b2e-4695-bc78-d1becc8428c7')
        self.p1 = Product.objects.get(id=6660001)
        self.p2 = Product.objects.get(id=6660002)

        self.pnl_1 = Panel.objects.create(
            experiment=self.exp,
            description='pnl_1_description',
            planned_panelists=5
        )
        self.user_super_pswd = '&!ep$o2Xf#e55#4&n!^$YZUsRLNmF9L36pS9%C*4L7MGdp#w%^b4@W%xY5#9&i'
        self.user_super = User.objects.create_superuser('super_user', 'mail@mail.com', self.user_super_pswd)
        self.panel1_url = self.pnl_1.get_absolute_url()

    def test_anonymous_user_cannot_access(self):
        c = Client()
        response = c.get(self.panel1_url)
        self.assertEquals(response.status_code, 403)

    def test_superuser_can_access(self):
        c = Client()
        c.force_login(self.user_super)
        response = c.get(self.panel1_url)
        self.assertEquals(response.status_code, 200)
