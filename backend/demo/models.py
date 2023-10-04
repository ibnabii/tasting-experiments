from django.db import models

from tasex.models import Panel


class DemoInstance(models.Model):
    session_key = models.CharField(max_length=50)
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)


class DemoParam(models.Model):
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=50)
