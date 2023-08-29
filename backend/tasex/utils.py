import base64
import io

import matplotlib.pyplot as plt
import scipy.stats as stats

from .models import Result, PanelQuestion, Answer


def generate_pie_chart(data):
    title = data.pop('title', None)
    explode = data.pop('explode', None)
    colors = data.pop('colors', None)

    plt.figure()
    plt.pie(data.values(),
            labels=data.keys(),
            explode=explode,
            autopct='%.0f%%',
            colors=colors,
            shadow=True
            )
    if title:
        plt.title(title)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    plot_image = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return plot_image


class PanelResult:
    def __init__(self, panel):
        results = Result.objects.filter(sample_set__panel=panel)
        self.participants = results.count()
        self.correct = results.filter(is_correct=True).count()

        self.wrong = self.participants - self.correct
        if self.correct > 0:
            self.percent_correct = round(self.correct / self.participants * 100)
        else:
            self.percent_correct = 0
        test_result = stats.binomtest(
            self.correct,
            self.participants,
            p=1/3,
            alternative="greater")
        self.p_value = test_result.pvalue

        self.plot_correct = generate_pie_chart({
            'title': f'Poprawnie zidentyfkowane próbki (P-value = {self.p_value:.3f})',
            'explode': [0.0, 0.1] if self.correct > self.wrong else [0.1, 0.0],
            'colors': ['limegreen', 'tomato'],
            f'Poprawnie ({self.correct})': self.correct,
            f'Niepoprawnie ({self.wrong})': self.wrong
        })


class SurveyPlots:
    def __init__(self, panel):
        default_colors = {
            2: ['limegreen', 'tomato'],
            3: ['limegreen', 'gold', 'tomato'],
            5: ['red', 'tomato', 'gold', 'limegreen', 'green'],
            7: ['red', 'tomato', 'lightcoral', 'gold', 'palegreen', 'limegreen', 'green'],
        }
        questions = PanelQuestion.objects.filter(panel=panel)
        results = Result.objects.filter(is_correct=True).filter(sample_set__panel=panel)
        answers = Answer.objects.filter(result__in=results)
        self.plots = []
        if answers.count() == 0:
            return
        for question in questions:
            plot = {
                'title': question.question_text,
            }
            colors = default_colors.get(question.scale.points.count()).copy()
            idx = 0

            for point in question.scale.points.all():
                n = answers.filter(question=question).filter(answer_code=point.code).count()
                if n:
                    plot.update({
                        f'{point.text} ({n})': n
                    })
                    idx += 1
                else:
                    del colors[idx]

            if colors:
                plot.update({'colors': colors})
            self.plots.append(generate_pie_chart(plot))

