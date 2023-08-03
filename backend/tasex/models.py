from random import sample, getrandbits
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Product(models.Model):
    brew_id = models.CharField(max_length=20, help_text='Internal brewing ID, not shown to panelists')
    internal_name = models.CharField(max_length=100, help_text='Internal name, not shown to panelists')
    name = models.CharField(max_length=100, help_text='Name of the product shown to panelists')
    description = models.TextField()

    def __str__(self):
        return self.name


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    internal_title = models.CharField(max_length=120, help_text='Internal title, not shown to panelists')
    title = models.CharField(max_length=120, help_text='Title shown to panelists')
    description = models.TextField(help_text='Decide if show this description to panelists on panel level')
    created_at = models.DateTimeField(auto_now_add=True)
    product_A = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')
    product_B = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='+')

    def __str__(self):
        return self.title


class SampleSet(models.Model):
    panel = models.ForeignKey('Panel', on_delete=models.CASCADE, related_name='sample_sets')
    is_used = models.BooleanField(default=False)


class Sample(models.Model):
    sample_set = models.ForeignKey(SampleSet, on_delete=models.CASCADE, related_name='samples')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='samplesp')
    code = models.CharField(max_length=5)


class Panel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='panels')
    description = models.TextField()
    planned_panelists = models.PositiveSmallIntegerField()

    class ShowExperimentDescription(models.TextChoices):
        NO = 'NO', 'No'
        AFTER_TASTING = 'AFTER_TASTING', 'Show after tasting'
        BEFORE_TASTING = 'BEFORE_TASTING', 'Show before tasting'
    show_exp_description = models.CharField(
        choices=ShowExperimentDescription.choices,
        default=ShowExperimentDescription.NO,
        max_length=20,
        verbose_name="Show experiment description to panelists?"
    )

    class PanelStatus(models.TextChoices):
        PLANNED = 'PLANNED', 'Planned, but not accepting answers yet'
        ACCEPTING_ANSWERS = 'ACCEPTING_ANSWERS', 'Accepting answers'
        PRESENTING_RESULTS = 'PRESENTING_RESULTS', 'Presenting results'
        HIDDEN = 'HIDDEN', 'Hidden from anonymous users'
    status = models.CharField(
        choices=PanelStatus.choices,
        default=PanelStatus.PLANNED,
        max_length=20
    )
    closed_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description[:50]

    def clean(self):
        if Panel.objects.filter(pk=self.pk).exists():
            orig = Panel.objects.get(pk=self.pk)
            if self.planned_panelists != orig.planned_panelists:
                raise ValidationError('Cannot change "planned_panelists" field')

    def save(self, *args, **kwargs):
        # Automatically creates samples for the panel upon it's creation
        if self._state.adding:
            # generate random ids for all the samples
            sample_codes = sample(range(1000, 10000), self.planned_panelists * 3)
            # randomly decide how to assign samples to products
            product_ids = [
                self.experiment.product_A,
                self.experiment.product_B
            ]
            if getrandbits(1):
                product_ids.reverse()

            for i in range(self.planned_panelists):
                sample_set = SampleSet.objects.create(panel=self)
                for j in range(3):
                    Sample.objects.create(
                        sample_set=sample_set,
                        product=product_ids[(i + j) % 2],
                        code=sample_codes[3 * i + j]
                    )
        else:
            orig = Panel.objects.get(pk=self.pk)
            if self.planned_panelists != orig.planned_panelists:
                raise ValidationError('Cannot change "planned_panelists" field')

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('tasex:panel', kwargs={"pk": self.id})
