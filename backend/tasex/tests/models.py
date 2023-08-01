from django.core.exceptions import ValidationError
from django.test import TestCase

from ..models import Experiment, Product, Panel, SampleSet, Sample


class PanelModelTests(TestCase):
    fixtures = ['test_base']

    def setUp(self):
        self.exp = Experiment.objects.get(id='aaa66601-3b2e-4695-bc78-d1becc8428c7')
        self.p1 = Product.objects.get(id=6660001)
        self.p2 = Product.objects.get(id=6660002)
        self.DEFAULT_PANEL_ATTRIBUTES = {
            'experiment': self.exp,
            'description': 'pnl_description',
            'planned_panelists': 1,
        }

    def test_create_panel_with_even_panelists(self):
        PANELISTS = 6
        panel_attributes = self.DEFAULT_PANEL_ATTRIBUTES.copy()
        panel_attributes['planned_panelists'] = PANELISTS
        pnl = Panel.objects.create(**panel_attributes)

        # correct number of SampleSets
        self.assertEquals(
            PANELISTS,
            SampleSet.objects.count()
        )

        # correct number of Samples
        self.assertEquals(
            PANELISTS * 3,
            Sample.objects.count()
        )

        # Samples are evenly divided
        self.assertEquals(
            Sample.objects.filter(product=self.p1).count(),
            Sample.objects.filter(product=self.p2).count()
        )

        # all sample codes are unique
        samples_codes = Sample.objects.values_list('code', flat=True)
        self.assertEquals(
            len(samples_codes),
            len(set(samples_codes))
        )

    def test_create_panel_with_odd_panelists(self):
        PANELISTS = 7
        panel_attributes = self.DEFAULT_PANEL_ATTRIBUTES.copy()
        panel_attributes['planned_panelists'] = PANELISTS
        pnl = Panel.objects.create(**panel_attributes)

        # correct number of SampleSets
        self.assertEquals(
            PANELISTS,
            SampleSet.objects.count()
        )

        # correct number of Samples
        self.assertEquals(
            PANELISTS * 3,
            Sample.objects.count()
        )

        # Sample number are close to equal
        # close means differ by 1 sample only, because of odd panelist count
        self.assertEquals(
            abs(Sample.objects.filter(product=self.p1).count()
                - Sample.objects.filter(product=self.p2).count()),
            1
        )

        # all sample codes are unique
        samples_codes = Sample.objects.values_list('code', flat=True)
        self.assertEquals(
            len(samples_codes),
            len(set(samples_codes))
        )

    def test_editing_fields(self):
        pnl = Panel.objects.create(**self.DEFAULT_PANEL_ATTRIBUTES)

        # ok to change attributes
        new_description = 'changed description'
        new_show_exp_description = 'AFTER_TASTING'
        new_is_active = False

        pnl.description = new_description
        pnl.show_exp_description = new_show_exp_description
        pnl.status = Panel.PanelStatus.HIDDEN

        pnl.save()
        pnl2 = Panel.objects.get(pk=pnl.pk)

        self.assertEquals(new_description, pnl2.description)
        self.assertEquals(new_show_exp_description, pnl2.show_exp_description)
        self.assertEquals(pnl.status, pnl2.status)

        # fail change of planned_panelists
        pnl.planned_panelists = pnl.planned_panelists - 1
        self.assertRaises(ValidationError, pnl.save)


