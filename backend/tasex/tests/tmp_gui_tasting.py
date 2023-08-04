from random import randrange, choice
from json import dumps

from django.test import TestCase, Client
from django.urls import reverse

from ..models import Experiment, Product, Panel, SampleSet, Sample, Result


class SingleSampleFormTests(TestCase):
    fixtures = ['test_base']

    def setUp(self):
        self.exp = Experiment.objects.get(id='aaa66601-3b2e-4695-bc78-d1becc8428c7')
        self.p1 = Product.objects.get(id=6660001)
        self.p2 = Product.objects.get(id=6660002)
        self.DEFAULT_PANEL_ATTRIBUTES = {
            'experiment': self.exp,
            'description': 'pnl_description',
            'planned_panelists': 5,
            'status': Panel.PanelStatus.ACCEPTING_ANSWERS,
        }
        self.pnl = Panel.objects.create(**self.DEFAULT_PANEL_ATTRIBUTES)
        self.pnl2 = Panel.objects.create(**self.DEFAULT_PANEL_ATTRIBUTES)

    def test_code_not_exists(self):
        code_not_exists = randrange(1000, 10000)
        while Sample.objects.filter(code=code_not_exists).exists():
            code_not_exists = randrange(1000, 10000)
        c = Client()
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code_not_exists}
        )
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Nie ma takiego numeru próbki', html=True)

    def test_code_from_other_panel(self):
        code_from_pnl2 = (
            Sample.objects
            .filter(sample_set__panel=self.pnl2)
            .values_list('code', flat=True)[2]
        )
        c = Client()
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code_from_pnl2}
        )
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Nie ma takiego numeru próbki', html=True)

    def test_code_from_used_sample_set(self):
        code, sample_set_id = (Sample.objects
                               .filter(sample_set__panel=self.pnl)
                               .values_list('code', 'sample_set_id')[2])
        SampleSet.objects.filter(id=sample_set_id).update(is_used=True)
        c = Client()
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code}
        )
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'Ten numer próbki został już wykorzystany', html=True)

    def test_happy_path(self):
        sample_id, code, sample_set_id = choice(
            Sample.objects.filter(sample_set__panel=self.pnl).values_list('id', 'code', 'sample_set_id')
        )
        sample_set_codes = Sample.objects.filter(sample_set_id=sample_set_id).values_list('code', flat=True)
        self.assertIn(code, sample_set_codes)

        c = Client()
        # page with one code
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code}
        )

        # should redirect to next step
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            2
        )

        # which shows all 3 samples codes for confirmation
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        for sample_code in sample_set_codes:
            self.assertContains(response, sample_code)
        self.assertContains(response, 'Czy <b>wszystkie</b> numery się zgadzają')

        # upon confirmation next redirect
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'are_samples_correct': 'True'}
        )
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            3
        )

        # to select odd sample
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        for sample_code in sample_set_codes:
            self.assertContains(response, sample_code)
        self.assertContains(response, 'Która z próbek jest')
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['sample_set'],
            sample_set_id
        )

        # select sample
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'odd_sample': sample_id}
        )
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            4
        )

        # follow redirect
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_wait_for_finish.html')

        # check if response has been recorder correctly
        result_id = c.session.get('panels').get(str(self.pnl.id))['result']
        self.assertIsNotNone(result_id)
        result_code = Result.objects.get(id=result_id).odd_sample.code
        self.assertEquals(result_code, code)

    def test_path_with_wrong_sample_ids(self):
        sample_id, code, sample_set_id = choice(
            Sample.objects.filter(sample_set__panel=self.pnl).values_list('id', 'code', 'sample_set_id')
        )
        sample_set_codes = Sample.objects.filter(sample_set_id=sample_set_id).values_list('code', flat=True)
        self.assertIn(code, sample_set_codes)

        c = Client()
        # page with one code
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code}
        )

        # should redirect to next step
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            2
        )

        # which shows all 3 samples codes for confirmation
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        for sample_code in sample_set_codes:
            self.assertContains(response, sample_code)
        self.assertContains(response, 'Czy <b>wszystkie</b> numery się zgadzają')

        # ups, wrong samples - should go back to step 1
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'are_samples_correct': 'False'}
        )
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            1
        )

        # select different code from other sample set
        sample_id, code, sample_set_id = choice(
            Sample.objects
            .exclude(sample_set_id=sample_set_id)
            .filter(sample_set__panel=self.pnl)
            .values_list('id', 'code', 'sample_set_id')
        )
        sample_set_codes = Sample.objects.filter(sample_set_id=sample_set_id).values_list('code', flat=True)
        self.assertIn(code, sample_set_codes)

        # page with one code
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'code': code}
        )

        # should redirect to next step
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            2
        )

        # which shows all 3 samples codes for confirmation
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        for sample_code in sample_set_codes:
            self.assertContains(response, sample_code)
        self.assertContains(response, 'Czy <b>wszystkie</b> numery się zgadzają')

        # upon confirmation next redirect
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'are_samples_correct': 'True'}
        )
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            3
        )

        # to select odd sample
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_step_1.html')
        for sample_code in sample_set_codes:
            self.assertContains(response, sample_code)
        self.assertContains(response, 'Która z próbek jest')
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['sample_set'],
            sample_set_id
        )

        # select sample
        response = c.post(
            self.pnl.get_absolute_url(),
            data={'odd_sample': sample_id}
        )
        self.assertRedirects(response, self.pnl.get_absolute_url())
        self.assertEquals(
            c.session.get('panels').get(str(self.pnl.id))['step'],
            4
        )

        # follow redirect
        response = c.get(response.url)
        self.assertTemplateUsed(response, 'tasex/panel_wait_for_finish.html')

        # check if response has been recorder correctly
        result_id = c.session.get('panels').get(str(self.pnl.id))['result']
        self.assertIsNotNone(result_id)
        result_code = Result.objects.get(id=result_id).odd_sample.code
        self.assertEquals(result_code, code)
