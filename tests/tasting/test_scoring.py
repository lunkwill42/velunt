from decimal import Decimal

import pytest

from velunt.tasting.scoring import (
    SCORING_SYSTEMS,
    Dimension,
    get_scoring_system,
)


class TestDimension:
    @pytest.fixture()
    def untappd(self):
        return Dimension(
            key="untappd",
            label="Untappd",
            min_value=Decimal("1.0"),
            max_value=Decimal("5.0"),
            increment=Decimal("0.25"),
        )

    def test_when_value_is_valid_validate_should_return_decimal(self, untappd):
        assert untappd.validate(3.5) == Decimal("3.5")

    def test_when_value_is_at_minimum_validate_should_accept(self, untappd):
        assert untappd.validate(1.0) == Decimal("1.0")

    def test_when_value_is_at_maximum_validate_should_accept(self, untappd):
        assert untappd.validate(5.0) == Decimal("5.0")

    def test_when_value_is_below_minimum_validate_should_raise(self, untappd):
        with pytest.raises(ValueError, match="utenfor tillatt område"):
            untappd.validate(0.5)

    def test_when_value_is_above_maximum_validate_should_raise(self, untappd):
        with pytest.raises(ValueError, match="utenfor tillatt område"):
            untappd.validate(5.25)

    def test_when_value_is_invalid_increment_validate_should_raise(self, untappd):
        with pytest.raises(ValueError, match="ikke et gyldig inkrement"):
            untappd.validate(1.1)

    def test_when_value_is_string_validate_should_coerce_to_decimal(self, untappd):
        assert untappd.validate("3.25") == Decimal("3.25")


class TestJuleolScoringSystem:
    @pytest.fixture()
    def juleol(self):
        return get_scoring_system("juleol")

    def test_when_both_scores_present_calculate_total_should_multiply(self, juleol):
        scores = {"untappd": "3.5", "julete": "4.0"}
        assert juleol.calculate_total(scores) == Decimal("14.00")

    def test_when_scores_are_minimum_calculate_total_should_return_one(self, juleol):
        scores = {"untappd": "1.0", "julete": "1.0"}
        assert juleol.calculate_total(scores) == Decimal("1.00")

    def test_when_scores_are_maximum_calculate_total_should_return_25(self, juleol):
        scores = {"untappd": "5.0", "julete": "5.0"}
        assert juleol.calculate_total(scores) == Decimal("25.00")

    def test_when_untappd_missing_calculate_total_should_return_none(self, juleol):
        scores = {"julete": "4.0"}
        assert juleol.calculate_total(scores) is None

    def test_when_julete_missing_calculate_total_should_return_none(self, juleol):
        scores = {"untappd": "3.5"}
        assert juleol.calculate_total(scores) is None

    def test_when_scores_empty_calculate_total_should_return_none(self, juleol):
        assert juleol.calculate_total({}) is None

    def test_when_scores_valid_is_complete_should_return_true(self, juleol):
        scores = {"untappd": "3.5", "julete": "4.0"}
        assert juleol.is_complete(scores) is True

    def test_when_score_missing_is_complete_should_return_false(self, juleol):
        scores = {"untappd": "3.5"}
        assert juleol.is_complete(scores) is False

    def test_when_totals_provided_aggregate_should_return_average(self, juleol):
        totals = [Decimal("10"), Decimal("20"), Decimal("15")]
        assert juleol.aggregate(totals) == Decimal("15")

    def test_when_no_totals_aggregate_should_return_zero(self, juleol):
        assert juleol.aggregate([]) == Decimal("0")


class TestSimpleUntappdScoringSystem:
    @pytest.fixture()
    def simple(self):
        return get_scoring_system("simple_untappd")

    def test_when_score_present_calculate_total_should_return_value(self, simple):
        scores = {"untappd": "3.5"}
        assert simple.calculate_total(scores) == Decimal("3.5")

    def test_when_score_missing_calculate_total_should_return_none(self, simple):
        assert simple.calculate_total({}) is None

    def test_when_score_zero_calculate_total_should_return_zero(self, simple):
        scores = {"untappd": "0.0"}
        assert simple.calculate_total(scores) == Decimal("0.0")


class TestScoringRegistry:
    def test_when_looking_up_juleol_get_scoring_system_should_return_it(self):
        system = get_scoring_system("juleol")
        assert system.key == "juleol"

    def test_when_looking_up_unknown_key_get_scoring_system_should_raise(self):  # noqa: E501
        with pytest.raises(KeyError):
            get_scoring_system("nonexistent")

    def test_when_checking_registry_it_should_contain_both_systems(self):
        assert "juleol" in SCORING_SYSTEMS
        assert "simple_untappd" in SCORING_SYSTEMS
        assert len(SCORING_SYSTEMS) == 2
