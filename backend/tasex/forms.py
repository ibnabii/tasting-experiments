from django import forms

from .models import Product, Experiment, Panel


class InternalNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if hasattr(obj, 'internal_name'):
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
