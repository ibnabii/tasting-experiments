from django import forms

from .models import Product, Experiment


class InternalNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.internal_name


class ExperimentForm(forms.ModelForm):
    product_A = InternalNameChoiceField(queryset=Product.objects.all())
    product_B = InternalNameChoiceField(queryset=Product.objects.all())

    class Meta:
        model = Experiment
        fields = '__all__'
