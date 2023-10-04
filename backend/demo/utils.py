from numpy.random import choice

from django.db.models import Count

from tasex.models import Product, Experiment, Panel, Scale, ScalePoint, PanelQuestion, Answer, Result, SampleSet, Sample
from .models import DemoParam, DemoInstance

DEMO_PRODUCT_1_KEY = 'DEMO_PRODUCT_1'
DEMO_PRODUCT_2_KEY = 'DEMO_PRODUCT_2'
DEMO_EXPERIMENT_KEY = 'DEMO_EXPERIMENT'
DEMO_SCALE_ABC_KEY = 'DEMO_SCALE_ABC'
DEMO_PANEL_RESULTS_SIGNIFICANT_KEY = 'DEMO_PANEL_RESULTS_SIGNIFICANT'
DEMO_PANEL_RESULTS_INDISTINGUISHABLE_KEY = 'DEMO_PANEL_RESULTS_INDISTINGUISHABLE'
DEMO_RESULTS = (
    DEMO_PANEL_RESULTS_SIGNIFICANT_KEY,
    DEMO_PANEL_RESULTS_INDISTINGUISHABLE_KEY
)


def reset_panel(panel):
    sample_sets = SampleSet.objects.filter(panel=panel)
    sample_sets.update(is_used=False)
    results = Result.objects.filter(sample_set__in=sample_sets)
    Answer.objects.filter(result__in=results).delete()
    results.delete()


def get_session_panel(session_key) -> Panel:
    return DemoInstance.objects.get(session_key=session_key).panel


def get_significant_result_id():
    return DemoParam.objects.get(key=DEMO_PANEL_RESULTS_SIGNIFICANT_KEY).value


def get_indistinguishable_result_id():
    return DemoParam.objects.get(key=DEMO_PANEL_RESULTS_INDISTINGUISHABLE_KEY).value


def ensure_demo_data(session_key):
    if not check_demo_products_exist():
        clean_demo_products()
        create_demo_products()

    if not check_demo_experiment_exist():
        clean_demo_experiment()
        create_demo_experiment()

    if not check_scale_exists():
        clean_demo_scale()
        create_demo_scale()

    if not check_demo_results_exist():
        clean_demo_results()
        create_demo_results()

    if not check_session_panel_exists(session_key):
        clean_session_panel(session_key)
        create_session_panel(session_key)


def check_session_panel_exists(session_key):
    items = DemoInstance.objects.filter(session_key=session_key)
    if items.count() != 1:
        return False

    panels = Panel.objects.filter(sessions__in=items)
    if panels.count() != 1:
        return False

    return True


def clean_session_panel(session_key):
    items = DemoInstance.objects.filter(session_key=session_key)
    Panel.objects.filter(sessions__in=items).delete()
    items.delete()


def create_session_panel(session_key):
    panel = Panel.objects.create(**get_demo_panel_data())
    create_demo_panel_questions(panel)

    DemoInstance.objects.create(
        session_key=session_key,
        panel=panel
    )


def check_scale_exists():
    param = DemoParam.objects.filter(key=DEMO_SCALE_ABC_KEY)
    if param.count() != 1:
        return False

    experiment = Scale.objects.filter(id__in=list(param.values_list('value', flat=True)))
    if experiment.count() != 1:
        return False

    return True


def clean_demo_scale():
    param = DemoParam.objects.filter(key=DEMO_SCALE_ABC_KEY)
    Scale.objects.filter(id__in=list(param.values_list('value', flat=True))).delete()
    param.delete()


def create_demo_scale():
    scale = Scale.objects.create(name=DEMO_SCALE_ABC_KEY)
    DemoParam.objects.create(
        key=DEMO_SCALE_ABC_KEY,
        value=scale.id
    )

    ScalePoint.objects.create(
        code='A',
        text='Product A',
        scale=scale
    )

    ScalePoint.objects.create(
        code='ND',
        text='No difference',
        scale=scale
    )

    ScalePoint.objects.create(
        code='B',
        text='Product B',
        scale=scale
    )


def check_demo_results_exist():
    for demo_result in DEMO_RESULTS:
        param = DemoParam.objects.filter(key=demo_result)
        if param.count() != 1:
            return False

        experiment = Panel.objects.filter(id__in=list(param.values_list('value', flat=True)))
        if experiment.count() != 1:
            return False
    return True


def clean_demo_results():
    for demo_result in DEMO_RESULTS:
        param = DemoParam.objects.filter(key=demo_result)
        Panel.objects.filter(id__in=list(param.values_list('value', flat=True))).delete()
        param.delete()


def create_demo_results():
    for demo_result in DEMO_RESULTS:
        panel = Panel.objects.create(**get_demo_panel_data(demo_result))
        DemoParam.objects.create(
            key=demo_result,
            value=panel.id
        )
        create_demo_panel_questions(panel)
        create_panel_results(panel, 0.9 if demo_result == DEMO_PANEL_RESULTS_SIGNIFICANT_KEY else 0.33)


def create_demo_panel_questions(panel):
    status = panel.status
    panel.status = Panel.PanelStatus.PLANNED
    scale = Scale.objects.get(id=DemoParam.objects.get(key=DEMO_SCALE_ABC_KEY).value)
    questions = (
        'Which product do you prefer overall?',
        'Which product tastes more acidic?',
        'Which product smells more fruity?'
    )
    for idx, question in enumerate(questions):
        PanelQuestion.objects.create(
            panel=panel,
            order=idx,
            question_text=question,
            scale=scale
        )
    panel.status = status


def get_demo_panel_data(key=None):
    if key == DEMO_PANEL_RESULTS_SIGNIFICANT_KEY:
        return {
            'experiment': Experiment.objects.get(
                id=DemoParam.objects.get(
                    key=DEMO_EXPERIMENT_KEY
                ).value
            ),
            'description': 'Demo panel with results showing significant difference between products',
            'planned_panelists': 30,
            'status': Panel.PanelStatus.PRESENTING_RESULTS
        }

    if key == DEMO_PANEL_RESULTS_INDISTINGUISHABLE_KEY:
        return {
            'experiment': Experiment.objects.get(
                id=DemoParam.objects.get(
                    key=DEMO_EXPERIMENT_KEY
                ).value
            ),
            'description': 'Demo panel with results showing no difference between products',
            'planned_panelists': 30,
            'status': Panel.PanelStatus.PRESENTING_RESULTS
        }

    # else return data for panel created per user session
    return {
        'experiment': Experiment.objects.get(
            id=DemoParam.objects.get(
                key=DEMO_EXPERIMENT_KEY
            ).value
        ),
        'description': 'Panel created for demo purposes',
        'planned_panelists': 10
    }


def check_demo_experiment_exist():
    param = DemoParam.objects.filter(key=DEMO_EXPERIMENT_KEY)
    if param.count() != 1:
        return False

    experiment = Experiment.objects.filter(id__in=list(param.values_list('value', flat=True)))
    if experiment.count() != 1:
        return False

    return True


def clean_demo_experiment():
    param = DemoParam.objects.filter(key=DEMO_EXPERIMENT_KEY)
    Experiment.objects.filter(id__in=list(param.values_list('value', flat=True))).delete()
    param.delete()


def create_demo_experiment():
    demo_experiment = {
        'internal_title': 'Experiment used in demo site',
        'title': 'Demo experiment title',
        'description': 'Demo experiment description',
        'product_A': Product.objects.get(id=DemoParam.objects.get(key=DEMO_PRODUCT_1_KEY).value),
        'product_B': Product.objects.get(id=DemoParam.objects.get(key=DEMO_PRODUCT_2_KEY).value),
    }

    experiment = Experiment.objects.create(**demo_experiment)
    DemoParam.objects.create(
        key=DEMO_EXPERIMENT_KEY,
        value=experiment.id
    )


def check_demo_products_exist():
    return (
            product_with_key_exists(DEMO_PRODUCT_1_KEY)
            and product_with_key_exists(DEMO_PRODUCT_2_KEY)
            )


def clean_demo_products():
    delete_demo_product(DEMO_PRODUCT_1_KEY)
    delete_demo_product(DEMO_PRODUCT_2_KEY)


def product_with_key_exists(demo_param_key):
    param = DemoParam.objects.filter(key=demo_param_key)
    if param.count() != 1:
        return False

    product = Product.objects.filter(id__in=list(param.values_list('value', flat=True)))
    if product.count() != 1:
        return False

    return True


def delete_demo_product(demo_param_key):
    product = Product.objects.filter(
        id__in=list(DemoParam.objects.filter(
            key=demo_param_key
        )
        .values_list('value', flat=True)
    ))
    if product:
        product.delete()

    DemoParam.objects.filter(key=demo_param_key).delete()


def create_demo_products():
    demo_product_1 = {
        'brew_id': 'demo_product_1',
        'internal_name': 'Product 1 for demo site',
        'name': 'Demo product 1',
        'description': 'Product 1 used in demo site',
    }

    demo_product_2 = {
        'brew_id': 'demo_product_2',
        'internal_name': 'Product 2 for demo site',
        'name': 'Demo product 2',
        'description': 'Product 2 used in demo site',
    }

    product = Product.objects.create(**demo_product_1)
    DemoParam.objects.create(
        key=DEMO_PRODUCT_1_KEY,
        value=product.id
    )

    product = Product.objects.create(**demo_product_2)
    DemoParam.objects.create(
        key=DEMO_PRODUCT_2_KEY,
        value=product.id
    )


def get_odd_sample(sample_set, probability=0.33):
    samples = Sample.objects.filter(sample_set=sample_set)
    odd_product = (
        samples
        .values('product_id')
        .annotate(cnt=Count('product_id'))
        .values_list('product_id', flat=True)[0]
    )
    return choice(
        (samples.filter(product_id=odd_product).first(), samples.exclude(product_id=odd_product).first()),
        p=(probability, 1-probability)
    )


def create_panel_results(panel, probability_correct=0.33, probabilities=(0.4, 0.2, 0.4)):
    scale_points = list(
        ScalePoint.objects.filter(
            scale__id=DemoParam.objects.get(
                key=DEMO_SCALE_ABC_KEY
            ).value
        ).values_list('code', 'text')
    )

    for sample_set in SampleSet.objects.filter(panel=panel).filter(is_used=False):
        result = Result.objects.create(
            sample_set=sample_set,
            odd_sample=get_odd_sample(sample_set, probability_correct)
        )
        for question in PanelQuestion.objects.filter(panel=panel):
            answer_code, answer_text = scale_points[choice(len(scale_points), p=probabilities)]
            Answer.objects.create(
                question=question,
                result=result,
                answer_code=answer_code,
                answer_text=answer_text
            )

