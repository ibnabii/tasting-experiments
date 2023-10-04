from random import sample, getrandbits
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse


class Product(models.Model):
    # TODO: change id to uuid
    # id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
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
    question_set = models.ForeignKey(
        'QuestionSet',
        on_delete=models.SET_NULL,
        related_name='experiment',
        help_text='Default question set for panels in this experiment',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.title


class SampleSet(models.Model):
    panel = models.ForeignKey('Panel', on_delete=models.CASCADE, related_name='sample_sets')
    is_used = models.BooleanField(default=False)


class Sample(models.Model):
    sample_set = models.ForeignKey(SampleSet, on_delete=models.CASCADE, related_name='samples')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='samples')
    code = models.CharField(max_length=5)

    class Meta:
        ordering = ('code',)


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
            super().save(*args, **kwargs)
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


class Result(models.Model):
    # panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name='results')
    sample_set = models.ForeignKey(SampleSet, on_delete=models.CASCADE, related_name='results')
    odd_sample = models.ForeignKey(Sample, on_delete=models.CASCADE, related_name='results')
    is_correct = models.BooleanField(editable=False)

    def validate(self):
        if (Result.objects
                .filter(sample_set=self.sample_set)
                .exclude(id=self.id)
                .exists()):
            raise ValidationError('A Result for this SampleSet already exists')
        # odd sample must belong to sample set
        if self.odd_sample.sample_set != self.sample_set:
            raise ValidationError('odd sample does not belong to this Sample Set')

    def clean(self):
        self.validate()

    def save(self, *args, **kwargs):
        self.validate()
        odd_product = (
            Sample.objects
            .filter(sample_set=self.sample_set)
            .values('product_id')
            .annotate(cnt=models.Count('product_id'))
            .filter(cnt=1)
            .values_list('product_id', flat=True)[0]
        )
        odd_sample = (
            Sample.objects
            .filter(sample_set=self.sample_set)
            .filter(product_id=odd_product)
            .values_list('id', flat=True)[0]
        )
        self.is_correct = odd_sample == self.odd_sample.id
        self.sample_set.is_used = True
        self.sample_set.save()
        super().save(*args, **kwargs)


class ScalePoint(models.Model):
    code = models.CharField(max_length=10)
    text = models.CharField(max_length=50)
    scale = models.ForeignKey('Scale', related_name='points', on_delete=models.CASCADE)

    def __str__(self):
        return f'({self.code}){self.text}'


class Scale(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return (self.name + ' - ' + ', '
                .join([f'({point[0]}) {point[1]}' for point in self.points.values_list('code', 'text')]))


class Question(models.Model):
    question_text = models.CharField(max_length=100)
    scale = models.ForeignKey(Scale, related_name='questions', on_delete=models.PROTECT)

    def __str__(self):
        return self.question_text + ' - [' + str(self.scale) + ']'


class QuestionOrder(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_set = models.ForeignKey('QuestionSet', on_delete=models.CASCADE, related_name='question_order')
    order = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ('question_set', 'order', 'question')
        verbose_name = 'Question'
        unique_together = (
            ('question', 'question_set'),
            ('question_set', 'order'),
        )


class QuestionSet(models.Model):
    name = models.CharField(max_length=120)
    questions = models.ManyToManyField(Question, blank=True, through=QuestionOrder)

    def __str__(self):
        return self.name


class PanelQuestion(models.Model):
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)
    order = models.PositiveSmallIntegerField()
    question_text = models.CharField(max_length=100)
    scale = models.ForeignKey(Scale, related_name='panel_questions', on_delete=models.PROTECT)

    def __str__(self):
        return self.question_text + ' - [' + str(self.scale) + ']'

    class Meta:
        ordering = ('panel', 'order', 'question_text')
        verbose_name = 'Panel question'
        unique_together = (
            ('panel', 'order'),
        )

    def delete(self, **kwargs):
        if self.panel.status != Panel.PanelStatus.PLANNED:
            raise ValidationError('Cannot delete questions once panel is started!')
        super().delete(**kwargs)

    def save(self, **kwargs):
        if self.panel.status != Panel.PanelStatus.PLANNED:
            raise ValidationError('Cannot add questions once panel is started!')
        super().save(**kwargs)


class Answer(models.Model):
    question = models.ForeignKey(PanelQuestion, on_delete=models.CASCADE, related_name='answers')
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='answers')
    answer_code = models.CharField(max_length=10)
    answer_text = models.CharField(max_length=50)
