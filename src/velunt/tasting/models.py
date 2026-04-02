from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from velunt.tasting.scoring import SCORING_SYSTEM_CHOICES, get_scoring_system
from velunt.tasting.utils import generate_public_id


class Event(models.Model):
    public_id = models.CharField(
        max_length=6,
        unique=True,
        default=generate_public_id,
        editable=False,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="events",
    )
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    event_date = models.DateField()
    closed_at = models.DateTimeField(null=True, blank=True)
    scoring_system = models.CharField(
        max_length=50,
        choices=SCORING_SYSTEM_CHOICES,
    )

    class Meta:
        ordering = ["-event_date"]

    def __str__(self):
        return self.description

    def get_absolute_url(self):
        return reverse("tasting:event_detail", args=[self.public_id])

    @property
    def state(self):
        if self.closed_at is not None:
            return "closed"
        today = timezone.localdate()
        if today < self.event_date:
            return "not_yet_open"
        return "open"


class Scorecard(models.Model):
    public_id = models.CharField(
        max_length=6,
        unique=True,
        default=generate_public_id,
        editable=False,
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="scorecards",
    )
    judge_name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "judge_name"],
                name="unique_judge_per_event",
            ),
        ]

    def __str__(self):
        return self.judge_name


class ScorecardLine(models.Model):
    scorecard = models.ForeignKey(
        Scorecard,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    beer_number = models.PositiveIntegerField()
    scores = models.JSONField(default=dict)
    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["scorecard", "beer_number"],
                name="unique_beer_per_scorecard",
            ),
        ]
        ordering = ["beer_number"]

    def __str__(self):
        return f"Øl #{self.beer_number}"

    def save(self, *args, **kwargs):
        self._compute_total_score()
        super().save(*args, **kwargs)

    def _compute_total_score(self):
        """Compute and store total_score from the scoring system."""
        scoring_system = get_scoring_system(self.scorecard.event.scoring_system)
        self.total_score = scoring_system.calculate_total(self.scores)
