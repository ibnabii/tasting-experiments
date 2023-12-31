from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe

from .models import Product, Experiment, Panel, Sample, PanelQuestion
from .widgets import VerticalButtonSelect

class InternalNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if hasattr(obj, 'internal_name'):
            if hasattr(obj, 'brew_id'):
                return f'{obj.internal_name} ({obj.brew_id})'
            return obj.internal_name
        if hasattr(obj, 'internal_title'):
            return obj.internal_title
        return obj.__str__


class ExperimentForm(forms.ModelForm):
    product_A = InternalNameChoiceField(queryset=Product.objects)
    product_B = InternalNameChoiceField(queryset=Product.objects)

    class Meta:
        model = Experiment
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        question_set_widget = self.fields['question_set'].widget
        question_set_widget.can_change_related = False
        question_set_widget.can_delete_related = False


class PanelFormAdd(forms.ModelForm):
    experiment = InternalNameChoiceField(queryset=Experiment.objects)
    create_questions = forms.ChoiceField(
        choices=(
            ('copy', "Copy questions from experiment's default question set"),
            ('blank', 'Let me create questions on my own')
        ),
        initial='copy'
    )

    class Meta:
        model = Panel
        fields = '__all__'


class PanelFormChange(forms.ModelForm):
    class Meta:
        model = Panel
        exclude = ('experiment', 'planned_panelists')


class PanelQuestionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions', PanelQuestion.objects.none())
        super().__init__(*args, **kwargs)
        for question in questions:
            self.fields[question.id] = forms.ChoiceField(
                required=True,
                choices=question.scale.points.values_list('code', 'text'),
                # widget=forms.RadioSelect,
                widget=VerticalButtonSelect,
                label=question.question_text
            )

    def clean(self):
        for question in self.fields:
            answer = self.data.get(str(question))
            if answer and answer in PanelQuestion.objects.get(id=question).scale.points.values_list('code', flat=True):
                self.errors.pop(question)
        return self.data


class GenericPanelForm(forms.Form):
    def __init__(self, **kwargs):
        self.panel_state = kwargs.pop('panel_state')
        super().__init__(**kwargs)


class SingleSampleForm(GenericPanelForm):
    code = forms.IntegerField(
        label='Podaj numer dowolnej z otrzymanych próbek, abyśmy mogli sprawdzić czy masz dobry zestaw'
    )

    def clean_code(self):
        data = self.cleaned_data["code"]
        sample = Sample.objects.filter(code=data).filter(sample_set__panel_id=self.panel_state.panel_id)

        if not sample.exists():
            raise ValidationError('Nie ma takiego numeru próbki')

        if not sample.filter(sample_set__is_used=False).exists():
            raise ValidationError('Ten numer próbki został już wykorzystany')

        self.cleaned_data["sample_set_id"] = sample.values_list('sample_set_id')[0][0]

        return data


class CheckSampleSetForm(GenericPanelForm):
    are_samples_correct = forms.ChoiceField(
        # widget=forms.RadioSelect,
        widget=VerticalButtonSelect,
        choices=(
            (False, 'Nie'),
            (True, 'Tak'),
        )
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        samples = Sample.objects.filter(sample_set_id=self.panel_state.sample_set).values_list('code', flat=True)
        self.fields['are_samples_correct'].label = mark_safe(
            f'Sprawdź, czy Twoje próbki mają poniższe numery: <h4>{", ".join(samples)}</h4>' +
            'Czy <b>wszystkie</b> numery się zgadzają?<br/>'
        )


class SelectOddSampleForm(GenericPanelForm):
    odd_sample = forms.ChoiceField(
        # widget=forms.RadioSelect,
        widget=VerticalButtonSelect,
        label=mark_safe('Która z próbek jest  <b>inna</b> od pozostałych?'
                        '<br/>Wybierz dowolną, jeśli Twoim zdaniem są takie same')
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        samples = Sample.objects.filter(sample_set_id=self.panel_state.sample_set).values_list('id', 'code')
        self.fields['odd_sample'].choices = samples


FORM_CLASSES = {
    1: SingleSampleForm,
    2: CheckSampleSetForm,
    3: SelectOddSampleForm
}
