from uuid import uuid4

from django.db import models


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


class Panel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='panels')
    description = models.TextField()
    planned_samples = models.PositiveSmallIntegerField()
    class ShowExperimentDescription(models.TextChoices):
        NO = 'NO', 'No'
        AFTER_TASTING= 'AFTER_TASTING', 'Show after tasting',
        BEFORE_TASTING = 'BEFORE_TASTING', 'Show before tasting'
    show_exp_description = models.CharField(
        choices=ShowExperimentDescription.choices,
        default=ShowExperimentDescription.NO,
        max_length=20,
        verbose_name="Show experiment description to panelists?"
    )
    is_active = models.BooleanField(default=True, help_text='if Panel accepts results')
    closed_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description[:50]


class SampleSet(models.Model):
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name='sample_sets')
    is_used = models.BooleanField(default=False)


class Sample(models.Model):
    sample_set = models.ForeignKey(SampleSet, on_delete=models.CASCADE, related_name='samples')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='samples')
    code = models.CharField(max_length=5)
