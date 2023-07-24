from django.contrib import admin
from django.utils.safestring import mark_safe

from .forms import ExperimentForm, PanelForm
from .models import Experiment, Panel, Product, SampleSet, Sample


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', )
    list_display = ('internal_title', 'title', 'created_at', 'prod_a_internal_name', 'prod_b_internal_name')
    ordering = ('-created_at', )
    form = ExperimentForm

    def prod_a_internal_name(self, obj):
        return obj.product_A.internal_name
    prod_a_internal_name.short_description = 'Product A'

    def prod_b_internal_name(self, obj):
        return obj.product_B.internal_name

    prod_b_internal_name.short_description = 'Product B'

    def get_queryset(self, request):
        return super(ExperimentAdmin, self).get_queryset(request).select_related('product_A', 'product_B')

    # alternatively one could use (?)
    # class ArticleAdmin(admin.ModelAdmin):
    #     list_select_related = ["author", "category"]


@admin.register(Panel)
class PanelAdmin(admin.ModelAdmin):
    form = PanelForm
    readonly_fields = (
        'created_at',
        'modified_at',
    )
    list_display = (
        '__str__',
        'temp_gui',
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

    def temp_gui(self, obj):
        return mark_safe('<a href="%s">Temp GUI</a>' % obj.get_absolute_url())


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'brew_id',
        'internal_name',
        'name',
        'description',
    )


@admin.register(SampleSet)
class SampleSetAdmin(admin.ModelAdmin):
    pass


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = (
        'sample_set',
        'code',
        'product'
    )
