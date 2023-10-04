from django.contrib import admin
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import DemoInstance, DemoParam


@admin.register(DemoInstance)
class DemoInstanceAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'session_key', 'panel_link')
    ordering = ('created_at', 'session_key', 'panel')
    fields = ('created_at', 'session_key', 'panel_link')
    readonly_fields = ('created_at', 'session_key', 'panel_link')


    def panel_link(self, obj):
        return mark_safe('<a href="{}">{}</a>'.format(
            reverse('admin:tasex_panel_change', args=(obj.panel.id,)),
            obj.panel.id
        ))
        # obj.panel.id

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('panel')


@admin.register(DemoParam)
class DemoParamsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    ordering = ('key', 'value')
