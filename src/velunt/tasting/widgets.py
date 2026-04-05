from django.forms import TextInput
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from velunt.tasting.models import BeerLink


class DatalistTextInput(TextInput):
    """Text input with a datalist for typeahead suggestions."""

    def __init__(self, datalist_id, *args, **kwargs):
        self.datalist_id = datalist_id
        super().__init__(*args, **kwargs)

    def get_suggestions(self):
        return []

    def render(self, name, value, attrs=None, renderer=None):
        attrs = attrs or {}
        attrs["list"] = self.datalist_id
        html = super().render(name, value, attrs, renderer)
        options = mark_safe(
            "".join(
                format_html('<option value="{}">', s) for s in self.get_suggestions()
            )
        )
        datalist = format_html(
            '<datalist id="{}">{}</datalist>', self.datalist_id, options
        )
        return html + datalist


class BeerLinkLabelInput(DatalistTextInput):
    """Text input with typeahead for existing beer link labels."""

    def __init__(self, *args, **kwargs):
        super().__init__(datalist_id="beer-link-labels", *args, **kwargs)

    def get_suggestions(self):
        return (
            BeerLink.objects.values_list("label", flat=True)
            .distinct()
            .order_by("label")
        )
