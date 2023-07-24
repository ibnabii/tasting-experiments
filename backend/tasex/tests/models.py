from django.test import TestCase

from ..models import Experiment, Product, Panel, SampleSet, Sample


class PanelModelTests(TestCase):
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
