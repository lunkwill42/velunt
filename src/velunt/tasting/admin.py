from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from velunt.tasting.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ["description", "event_date", "scoring_system", "state"]
    list_filter = ["scoring_system"]
    readonly_fields = ["public_id", "created_at", "event_page_link"]
    fields = [
        "public_id",
        "event_page_link",
        "description",
        "event_date",
        "scoring_system",
        "closed_at",
        "owner",
        "created_at",
    ]

    @admin.display(description="Status")
    def state(self, obj):
        return obj.state

    @admin.display(description="Arrangementside")
    def event_page_link(self, obj):
        if not obj.pk:
            return "-"
        url = reverse("tasting:event_detail", args=[obj.public_id])
        return format_html('<a href="{}">{}</a>', url, url)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(owner=request.user)

    def save_model(self, request, obj, form, change):
        if not change:
            obj.owner = request.user
        super().save_model(request, obj, form, change)
