from django.contrib import admin
from django.utils.safestring import mark_safe

from .forms import ExperimentForm, PanelFormAdd, PanelFormChange
from .models import (Experiment, Panel, Product, SampleSet, Sample, Result, Scale, ScalePoint,
                     Question, QuestionSet, PanelQuestion)


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at',)
    list_display = ('internal_title', 'title', 'created_at', 'prod_a_internal_name', 'prod_b_internal_name')
    ordering = ('-created_at',)
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
    readonly_fields = (
        'created_at',
        'modified_at',
    )
    list_display = (
        '__str__',
        'temp_gui',
        'experiment',
        'status',
        'created_at',
        'description',
    )
    list_filter = (
        'experiment',
        'status',
        'created_at'
    )
    ordering = (
        'experiment',
        '-closed_at',
        '-created_at',
    )

    @staticmethod
    def temp_gui(obj):
        return mark_safe('<a href="%s">Temp GUI</a>' % obj.get_absolute_url())

    def add_view(self, request, form_url="", extra_context=None):
        self.form = PanelFormAdd
        self.inlines = tuple(())
        return super().add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        class Tabular(admin.TabularInline):
            model = PanelQuestion
            extra = 0
            classes = ['collapse']

            def formfield_for_dbfield(self, db_field, **kwargs):
                formfield = super().formfield_for_dbfield(db_field, **kwargs)
                if db_field.name == 'scale':
                    formfield.widget.can_delete_related = False
                    formfield.widget.can_change_related = False
                return formfield

        self.inlines = (Tabular,)
        self.form = PanelFormChange
        return super().change_view(request, object_id, form_url, extra_context)
    
    def save_model(self, request, obj, form, change):
        # copy questions from experiment on panel creation and user chose to copy
        if not change and form.cleaned_data.get('create_questions', None) == 'copy':
            PanelQuestion.objects.bulk_create([
                PanelQuestion(
                    panel=obj,
                    order=question_order.order,
                    question_text=question_order.question.question_text,
                    scale=question_order.question.scale
                )
                for question_order in obj.experiment.question_set.question_order.all()
            ])

        super().save_model(request, obj, form, change)


class QuestionInQuestionSetAdmin(admin.TabularInline):
    model = QuestionSet.questions.through
    extra = 0


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
    list_display = ('__str__', 'panel', 'is_used')


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'sample_set',
        'code',
        'product'
    )


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        '__str__',
        'sample_set',
        'odd_sample',
        'is_correct'
    )


class ScalePointAdmin(admin.TabularInline):
    model = ScalePoint
    extra = 1


@admin.register(Scale)
class ScaleAdmin(admin.ModelAdmin):
    inlines = (ScalePointAdmin,)


class QuestionInQuestionSetAdmin(admin.TabularInline):
    model = QuestionSet.questions.through
    extra = 0


@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    inlines = (QuestionInQuestionSetAdmin,)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(PanelQuestion)
class PanelQuestionAdmin(admin.ModelAdmin):
    pass

# for debug: check session data in admin module
# from django.contrib.sessions.models import Session
#
#
# @admin.register(Session)
# class SessionAdmin(admin.ModelAdmin):
#     def _session_data(self, obj):
#         return obj.get_decoded()
#
#     list_display = ['session_key', '_session_data', 'expire_date']
#     ordering = ['-expire_date']
