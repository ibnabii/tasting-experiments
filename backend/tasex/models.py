from uuid import uuid4

from django.db import models


class Experiment(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    title = models.CharField(max_length=120)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Panel(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    experiment = models.ForeignKey(Experiment, on_delete=models.CASCADE, related_name='panels')
    description = models.TextField()
    planned_samples = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)
    closed_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.description[:50]
