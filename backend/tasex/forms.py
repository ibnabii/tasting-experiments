from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Experiment, Panel, Sample


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


class PanelForm(forms.ModelForm):
    experiment = InternalNameChoiceField(queryset=Experiment.objects)

    class Meta:
        model = Panel
        fields = '__all__'


class SingleSampleForm(forms.Form):
    code = forms.IntegerField(label='Numer dowolnej próbki')

    def __init__(self, **kwargs):
        self.panel_id = kwargs.pop('panel_id', None)
        super().__init__(**kwargs)

    def clean_code(self):
        data = self.cleaned_data["code"]
        sample = Sample.objects.filter(code=data).filter(sample_set__panel_id=self.panel_id)

        if not sample.exists():
            raise ValidationError('Nie ma takiego numeru próbki')

        if not sample.filter(sample_set__is_used=False).exists():
            raise ValidationError('Ten numer próbki został już wykorzystany')

        return data
