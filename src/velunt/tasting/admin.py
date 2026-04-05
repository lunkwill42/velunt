from django import forms
from django.contrib import admin
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
    fields = ["name"]
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


class AnswerKeyEntryInline(admin.TabularInline):
    model = AnswerKeyEntry
    extra = 1
    fields = ["beer_number", "beer"]
    autocomplete_fields = ["beer"]


@admin.register(AnswerKey)
class AnswerKeyAdmin(admin.ModelAdmin):
    list_display = ["event", "is_published_display", "published_at"]
    readonly_fields = ["created_by", "created_at"]
    fields = ["event", "published_at", "created_by", "created_at"]
    inlines = [AnswerKeyEntryInline]

    @admin.display(description="Publisert", boolean=True)
    def is_published_display(self, obj):
        return obj.is_published

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Beer)
class BeerAdmin(admin.ModelAdmin):
    list_display = ["name", "event"]
    list_filter = ["event"]
    search_fields = ["name"]
    inlines = [BeerLinkInline]


@admin.register(Scorecard)
class ScorecardAdmin(admin.ModelAdmin):
    list_display = ["judge_name", "event", "public_id", "created_at"]
    list_filter = ["event"]
    readonly_fields = ["public_id", "created_at"]
