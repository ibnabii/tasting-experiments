from rest_framework import serializers

from .models import Experiment, Panel

class ExperimentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = '__all__'


class PanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Panel
        fields = '__all__'
