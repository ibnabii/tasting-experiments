from django.contrib import admin

from .models import Experiment, Panel


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    list_display = ('title', 'created_at', 'description',)


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    readonly_fields = (
        'created_at',
        'modified_at',
    )
    list_display = (
        'experiment',
        'is_active',
        'created_at',
        'description',
    )
    list_filter = (
        'experiment',
        'is_active',
        'created_at'
    )
    ordering = (
        'experiment',
        '-is_active',
        'closed_at',
        'created_at',
    )

