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
    description = models.TextField("beskrivelse")
    created_at = models.DateTimeField("opprettet", auto_now_add=True)
    event_date = models.DateField("dato")
    closed_at = models.DateTimeField("avsluttet", null=True, blank=True)
    scoring_system = models.CharField(
        "poengsystem",
        max_length=50,
        choices=SCORING_SYSTEM_CHOICES,
    )

    class Meta:
        ordering = ["-event_date"]
        verbose_name = "arrangement"
        verbose_name_plural = "arrangementer"

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
    judge_name = models.CharField("dommernavn", max_length=100)
    created_at = models.DateTimeField("opprettet", auto_now_add=True)

    class Meta:
        verbose_name = "dommerskjema"
        verbose_name_plural = "dommerskjema"
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
    beer_number = models.PositiveIntegerField("ølnummer")
    scores = models.JSONField("poeng", default=dict)
    total_score = models.DecimalField(
        "totalpoeng",
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    comment = models.TextField("kommentar", blank=True)
    created_at = models.DateTimeField("opprettet", auto_now_add=True)
    updated_at = models.DateTimeField("oppdatert", auto_now=True)

    class Meta:
        verbose_name = "poenglinje"
        verbose_name_plural = "poenglinjer"
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


class Beer(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="beers",
    )
    name = models.CharField("navn", max_length=200)
    is_homebrew = models.BooleanField("hjemmebrygg", default=False)

    class Meta:
        verbose_name = "øl"
        verbose_name_plural = "øl"
        ordering = ["name"]

    def __str__(self):
        return self.name


class BeerLink(models.Model):
    beer = models.ForeignKey(
        Beer,
        on_delete=models.CASCADE,
        related_name="links",
    )
    label = models.CharField("merkelapp", max_length=100)
    url = models.URLField("URL")

    class Meta:
        verbose_name = "øllenke"
        verbose_name_plural = "øllenker"

    def __str__(self):
        return self.label


class AnswerKey(models.Model):
    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="answer_key",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField("opprettet", auto_now_add=True)
    published_at = models.DateTimeField("publisert", null=True, blank=True)

    class Meta:
        verbose_name = "fasit"
        verbose_name_plural = "fasiter"

    def __str__(self):
        return f"Fasit: {self.event}"

    @property
    def is_published(self):
        if self.published_at is None:
            return False
        return timezone.now() >= self.published_at


class AnswerKeyEntry(models.Model):
    answer_key = models.ForeignKey(
        AnswerKey,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    beer_number = models.PositiveIntegerField("ølnummer")
    beer = models.ForeignKey(
        Beer,
        on_delete=models.CASCADE,
        related_name="answer_key_entries",
        verbose_name="øl",
    )

    class Meta:
        verbose_name = "fasitoppføring"
        verbose_name_plural = "fasitoppføringer"
        constraints = [
            models.UniqueConstraint(
                fields=["answer_key", "beer_number"],
                name="unique_beer_number_per_answer_key",
            ),
        ]
        ordering = ["beer_number"]

    def __str__(self):
        return f"#{self.beer_number}: {self.beer.name}"
