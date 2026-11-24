from django import forms
from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from django.urls import reverse
from django.utils.html import format_html

from velunt.tasting.models import (
    AnswerKey,
    AnswerKeyEntry,
    Beer,
    BeerLink,
    Event,
    Scorecard,
    ScorecardLine,
)


class BeerInline(admin.TabularInline):
    model = Beer
    extra = 1
    fields = ["name", "is_homebrew"]
    show_change_link = True


class BeerLinkForm(forms.ModelForm):
    class Meta:
        model = BeerLink
        fields = ["label", "url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from velunt.tasting.widgets import BeerLinkLabelInput

        self.fields["label"].widget = BeerLinkLabelInput()


class BeerLinkInline(admin.TabularInline):
    model = BeerLink
    form = BeerLinkForm
    extra = 1
    fields = ["label", "url"]


class ScorecardInline(admin.TabularInline):
    model = Scorecard
    extra = 0
    fields = ["public_id", "judge_name", "scorecard_link", "created_at"]
    readonly_fields = ["public_id", "scorecard_link", "created_at"]

    @admin.display(description="Dommerskjema")
    def scorecard_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("tasting:scorecard_detail", args=[obj.public_id])
        return format_html('<a href="{}">{}</a>', url, url)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["description", "event_date", "scoring_system", "state"]
    list_filter = ["scoring_system"]
    readonly_fields = [
        "public_id",
        "created_at",
        "event_page_link",
        "answer_key_link",
    ]
    fields = [
        "public_id",
        "event_page_link",
        "answer_key_link",
        "description",
        "event_date",
        "scoring_system",
        "closed_at",
        "owner",
        "created_at",
    ]
    actions = ["recalculate_scores"]
    inlines = [BeerInline, ScorecardInline]

    @admin.display(description="Status")
    def state(self, obj):
        return obj.state

    @admin.display(description="Arrangementside")
    def event_page_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("tasting:event_detail", args=[obj.public_id])
        return format_html('<a href="{}">{}</a>', url, url)

    @admin.display(description="Fasit")
    def answer_key_link(self, obj):
        if not obj.pk:
            return "-"
        try:
            ak = obj.answer_key
        except AnswerKey.DoesNotExist:
            url = reverse("admin:tasting_answerkey_add") + f"?event={obj.pk}"
            return format_html('<a href="{}">Opprett fasit</a>', url)
        url = reverse("admin:tasting_answerkey_change", args=[ak.pk])
        status = "Publisert" if ak.is_published else "Utkast"
        return format_html('<a href="{}">{}</a>', url, status)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Beregn poeng på nytt")
    def recalculate_scores(self, request, queryset):
        count = 0
        for event in queryset:
            lines = ScorecardLine.objects.filter(scorecard__event=event).select_related(
                "scorecard__event"
            )
            for line in lines:
                line.save()
                count += 1
        self.message_user(request, f"{count} poenglinjer beregnet på nytt.")


class AnswerKeyEntryFormSet(BaseInlineFormSet):
    def __init__(self, *args, event=None, **kwargs):
        self.event = event
        super().__init__(*args, **kwargs)

    def add_fields(self, form, index):
        super().add_fields(form, index)
        form.fields["beer"].queryset = Beer.objects.filter(event=self.event)


class AnswerKeyEntryInline(admin.TabularInline):
    model = AnswerKeyEntry
    formset = AnswerKeyEntryFormSet
    extra = 1
    fields = ["beer_number", "beer"]


@admin.register(AnswerKey)
class AnswerKeyAdmin(admin.ModelAdmin):
    list_display = ["event", "is_published_display", "published_at"]
    readonly_fields = ["created_by", "created_at"]
    fields = ["event", "published_at", "created_by", "created_at"]
    inlines = [AnswerKeyEntryInline]

    def get_readonly_fields(self, request, obj=None):
        readonly = super().get_readonly_fields(request, obj)
        if obj is None:
            return readonly
        # The entries point at beers belonging to this event
        return [*readonly, "event"]

    def get_inlines(self, request, obj):
        # Entries can only offer the event's beers once the event is known
        if self._get_event(request, obj) is None:
            return []
        return super().get_inlines(request, obj)

    def get_formset_kwargs(self, request, obj, inline, prefix):
        kwargs = super().get_formset_kwargs(request, obj, inline, prefix)
        kwargs["event"] = self._get_event(request, obj)
        return kwargs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "event":
            event = self._get_event_from_query(request)
            if event is not None:
                # Choosing another event would contradict the beers offered
                kwargs["queryset"] = Event.objects.filter(pk=event.pk)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description="Publisert", boolean=True)
    def is_published_display(self, obj):
        return obj.is_published

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def _get_event(self, request, obj):
        """The answer key's event, or the one the add page was opened for"""
        if obj is not None and obj.pk:
            return obj.event
        return self._get_event_from_query(request)

    def _get_event_from_query(self, request):
        event_id = self.get_changeform_initial_data(request).get("event", "")
        try:
            return Event.objects.filter(pk=int(event_id)).first()
        except ValueError:
            return None


@admin.register(Beer)
class BeerAdmin(admin.ModelAdmin):
    list_display = ["name", "event", "is_homebrew"]
    list_filter = ["event", "is_homebrew"]
    search_fields = ["name"]
    inlines = [BeerLinkInline]


@admin.register(Scorecard)
class ScorecardAdmin(admin.ModelAdmin):
    list_display = ["judge_name", "event", "public_id", "created_at"]
    list_filter = ["event"]
    readonly_fields = ["public_id", "created_at"]
