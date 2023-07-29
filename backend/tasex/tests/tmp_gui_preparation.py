from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.test import TestCase, Client

from ..models import Experiment, Product, Panel, SampleSet, Sample


class PanelViewTest(TestCase):
    def setUp(self):
        self.p1 = Product.objects.create(
            brew_id='prod_brew_id_1',
            internal_name='prod_internal_name_1',
            name='prod_name_1',
            description='prod_description_1'
        )
        self.p2 = Product.objects.create(
            brew_id='prod_brew_id_2',
            internal_name='prod_internal_name_2',
            name='prod_name_2',
            description='prod_description_2'
        )
        self.exp = Experiment.objects.create(
            internal_title='exp_internal_title',
            title='exp_title',
            description='exp_description',
            product_A=self.p1,
            product_B=self.p2
        )
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
