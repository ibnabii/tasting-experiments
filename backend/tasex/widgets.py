from django.forms.widgets import RadioSelect


class VerticalButtonSelect(RadioSelect):
    template_name = "tasex/widgets/vertical_button_select.html"