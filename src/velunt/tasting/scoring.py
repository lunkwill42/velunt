from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    min_value: Decimal
    max_value: Decimal
    increment: Decimal

    def validate(self, value) -> Decimal:
        """Validate and return a Decimal score value.

        Raises ValueError if the value is out of range or not a valid
        increment.
        """
        value = Decimal(str(value))
        if value < self.min_value or value > self.max_value:
            raise ValueError(
                f"{self.label}: {value} er utenfor tillatt område "
                f"({self.min_value}–{self.max_value})"
            )
        remainder = (value - self.min_value) % self.increment
        if remainder != 0:
            raise ValueError(
                f"{self.label}: {value} er ikke et gyldig inkrement "
                f"(må være i steg på {self.increment})"
            )
        return value


@dataclass(frozen=True)
class ScoringSystem:
    key: str
    name: str
    dimensions: list[Dimension] = field(default_factory=list)

    def calculate_total(self, scores: dict) -> Decimal | None:
        """Calculate total score from a dict of dimension scores.

        Returns None if any required dimension is missing or None.
        Subclasses override this to define their formula.
        """
        raise NotImplementedError

    def aggregate(self, totals: list[Decimal]) -> Decimal:
        """Aggregate total scores across judges (default: average)."""
        if not totals:
            return Decimal("0")
        return sum(totals) / len(totals)

    def validate_scores(self, scores: dict) -> dict[str, Decimal]:
        """Validate all dimension scores and return cleaned values."""
        validated = {}
        for dimension in self.dimensions:
            value = scores.get(dimension.key)
            if value is None:
                continue
            validated[dimension.key] = dimension.validate(value)
        return validated

    def is_complete(self, scores: dict) -> bool:
        """Check if all required dimensions have values."""
        return all(scores.get(d.key) is not None for d in self.dimensions)


class JuleolScoringSystem(ScoringSystem):
    def calculate_total(self, scores: dict) -> Decimal | None:
        if not self.is_complete(scores):
            return None
        validated = self.validate_scores(scores)
        return validated["untappd"] * validated["julete"]


class SimpleUntappdScoringSystem(ScoringSystem):
    def calculate_total(self, scores: dict) -> Decimal | None:
        if not self.is_complete(scores):
            return None
        validated = self.validate_scores(scores)
        return validated["untappd"]


JULEOL = JuleolScoringSystem(
    key="juleol",
    name="Juleøl",
    dimensions=[
        Dimension(
            key="untappd",
            label="Untappd",
            min_value=Decimal("1.0"),
            max_value=Decimal("5.0"),
            increment=Decimal("0.25"),
        ),
        Dimension(
            key="julete",
            label="Julete",
            min_value=Decimal("1.0"),
            max_value=Decimal("5.0"),
            increment=Decimal("0.25"),
        ),
    ],
)

SIMPLE_UNTAPPD = SimpleUntappdScoringSystem(
    key="simple_untappd",
    name="Enkel Untappd",
    dimensions=[
        Dimension(
            key="untappd",
            label="Untappd",
            min_value=Decimal("0.0"),
            max_value=Decimal("5.0"),
            increment=Decimal("0.1"),
        ),
    ],
)

SCORING_SYSTEMS: dict[str, ScoringSystem] = {
    system.key: system for system in [JULEOL, SIMPLE_UNTAPPD]
}

SCORING_SYSTEM_CHOICES = [
    (system.key, system.name) for system in SCORING_SYSTEMS.values()
]


def get_scoring_system(key: str) -> ScoringSystem:
    """Look up a scoring system by key.

    Raises KeyError if the key is not found.
    """
    return SCORING_SYSTEMS[key]
