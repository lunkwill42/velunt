from django import forms

from velunt.tasting.models import Scorecard


class ScorecardForm(forms.Form):
    judge_name = forms.CharField(
        max_length=100,
        label="Ditt navn",
        widget=forms.TextInput(attrs={"placeholder": "F.eks. Ola Nordmann"}),
    )

    def __init__(self, *args, event=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.event = event

    def clean_judge_name(self):
        name = self.cleaned_data["judge_name"].strip()
        if not name:
            raise forms.ValidationError("Du må oppgi et navn.")
        if Scorecard.objects.filter(event=self.event, judge_name=name).exists():
            raise forms.ValidationError(
                "Dette navnet er allerede i bruk for dette arrangementet. "
                "Legg til noe ekstra for å skille deg ut, "
                'f.eks. "Ola N" eller "Ola (Bergen)".'
            )
        return name
