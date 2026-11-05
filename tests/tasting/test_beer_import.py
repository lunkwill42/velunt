import pytest

from velunt.tasting.beer_import import (
    ParsedBeer,
    ParsedBeerList,
    ParsedLink,
    import_beer_list,
    label_for_url,
    parse_beer_list,
    parse_bool,
)
from velunt.tasting.models import AnswerKey, AnswerKeyEntry, Beer


class TestParseBeerList:
    def test_when_text_is_empty_it_should_return_no_beers(self):
        assert parse_beer_list("").beers == []

    def test_when_only_titles_are_given_it_should_return_no_beers(self):
        assert parse_beer_list("Navn\tHjemmebrygg").beers == []

    def test_when_name_column_is_titled_it_should_use_that_column(self):
        text = rows(["Bryggeri", "Navn"], ["Nøgne Ø", "Underlig Jul"])
        assert names(parse_beer_list(text)) == ["Underlig Jul"]

    def test_when_name_title_is_unknown_it_should_use_first_column(self):
        text = rows(["Juleøl"], ["Underlig Jul"], ["Julebokk"])
        assert names(parse_beer_list(text)) == ["Underlig Jul", "Julebokk"]

    def test_when_name_title_differs_in_case_it_should_still_be_recognized(self):
        text = rows(["Nr", "NAVN"], ["1", "Underlig Jul"])
        assert names(parse_beer_list(text)) == ["Underlig Jul"]

    def test_when_cells_have_surrounding_whitespace_it_should_strip_them(self):
        text = rows(["Navn"], ["  Underlig Jul  "])
        assert names(parse_beer_list(text)) == ["Underlig Jul"]

    def test_when_rows_are_blank_it_should_skip_them(self):
        text = "Navn\n\nUnderlig Jul\n\t\nJulebokk\n"
        assert names(parse_beer_list(text)) == ["Underlig Jul", "Julebokk"]

    def test_when_name_is_empty_it_should_skip_the_row(self):
        text = rows(["Navn", "Hjemmebrygg"], ["", "x"], ["Julebokk", ""])
        assert names(parse_beer_list(text)) == ["Julebokk"]

    def test_when_rows_have_uneven_length_it_should_pad_missing_cells(self):
        text = rows(["Navn", "Hjemmebrygg"], ["Underlig Jul"], ["Vegards Jul", "ja"])
        beers = parse_beer_list(text).beers
        assert [beer.is_homebrew for beer in beers] == [False, True]

    def test_when_homebrew_column_exists_it_should_interpret_values(self):
        text = rows(
            ["Navn", "Hjemmebrygg"],
            ["Underlig Jul", "nei"],
            ["Vegards Jul", "x"],
        )
        beers = parse_beer_list(text).beers
        assert [beer.is_homebrew for beer in beers] == [False, True]

    def test_when_homebrew_column_is_missing_it_should_mark_no_homebrews(self):
        text = rows(["Navn"], ["Underlig Jul"])
        assert not parse_beer_list(text).beers[0].is_homebrew

    def test_when_homebrew_column_comes_first_it_should_use_next_column_for_names(
        self,
    ):  # noqa: E501
        text = rows(["Hjemmebrygg", "Juleøl"], ["x", "Vegards Jul"])
        beer = parse_beer_list(text).beers[0]
        assert (beer.name, beer.is_homebrew) == ("Vegards Jul", True)

    def test_when_column_contains_urls_it_should_label_links_with_its_title(self):
        text = rows(
            ["Navn", "Polet"],
            ["Underlig Jul", "https://www.vinmonopolet.no/p/123"],
        )
        beer = parse_beer_list(text).beers[0]
        assert beer.links == [
            ParsedLink(label="Polet", url="https://www.vinmonopolet.no/p/123")
        ]

    def test_when_link_column_has_no_title_it_should_label_links_by_domain(self):
        text = rows(["Navn", ""], ["Underlig Jul", "https://untappd.com/b/1"])
        beer = parse_beer_list(text).beers[0]
        assert [link.label for link in beer.links] == ["Untappd"]

    def test_when_several_columns_contain_urls_it_should_keep_all_links(self):
        text = rows(
            ["Navn", "Vinmonopolet", "Untappd"],
            ["Underlig Jul", "https://vinmonopolet.no/p/1", "https://untappd.com/b/1"],
        )
        beer = parse_beer_list(text).beers[0]
        assert [link.label for link in beer.links] == ["Vinmonopolet", "Untappd"]

    def test_when_link_cell_is_empty_or_not_a_url_it_should_skip_that_link(self):
        text = rows(
            ["Navn", "Untappd"],
            ["Underlig Jul", "https://untappd.com/b/1"],
            ["Julebokk", ""],
            ["Vegards Jul", "finnes ikke"],
        )
        beers = parse_beer_list(text).beers
        assert [len(beer.links) for beer in beers] == [1, 0, 0]

    def test_when_first_row_contains_a_url_it_should_treat_it_as_data(self):
        text = rows(["Underlig Jul", "https://untappd.com/b/1"], ["Julebokk", ""])
        assert names(parse_beer_list(text)) == ["Underlig Jul", "Julebokk"]

    def test_when_columns_are_not_recognized_it_should_report_them_as_ignored(self):
        text = rows(["Nr", "Navn", "", "Pris"], ["1", "Underlig Jul", "x", "89,90"])
        assert parse_beer_list(text).ignored_columns == ["Nr", "Kolonne 3", "Pris"]

    def test_when_beer_is_listed_twice_it_should_merge_into_one(self):
        text = rows(["Navn"], ["Underlig Jul"], ["Julebokk"], ["underlig jul"])
        assert names(parse_beer_list(text)) == ["Underlig Jul", "Julebokk"]

    def test_when_merging_duplicates_it_should_combine_their_links(self):
        text = rows(
            ["Navn", "Untappd"],
            ["Underlig Jul", "https://untappd.com/b/1"],
            ["Underlig Jul", "https://untappd.com/b/2"],
            ["Underlig Jul", "https://untappd.com/b/1"],
        )
        beer = parse_beer_list(text).beers[0]
        assert [link.url for link in beer.links] == [
            "https://untappd.com/b/1",
            "https://untappd.com/b/2",
        ]


class TestParseBool:
    @pytest.mark.parametrize("value", ["", "0", "-", "false", "no", "nei", "NEI", " "])
    def test_when_value_is_negative_or_blank_it_should_return_false(self, value):
        assert parse_bool(value) is False

    @pytest.mark.parametrize("value", ["x", "ja", "yes", "1", "true", "Hjemmebrygg"])
    def test_when_value_is_anything_else_it_should_return_true(self, value):
        assert parse_bool(value) is True


class TestLabelForUrl:
    @pytest.mark.parametrize(
        "url, label",
        [
            ("https://www.vinmonopolet.no/p/123", "Vinmonopolet"),
            ("https://untappd.com/b/nogne-o/1", "Untappd"),
            ("https://m.untappd.com/b/1", "Untappd"),
            ("https://www.example.org/beer", "example.org"),
        ],
    )
    def test_when_domain_is_given_it_should_return_matching_label(self, url, label):
        assert label_for_url(url) == label


class TestImportBeerList:
    def test_when_event_has_no_beers_it_should_create_all_of_them(self, event):
        result = import_beer_list(event, beer_list("Underlig Jul", "Julebokk"))

        assert result.created == 2
        assert beer_names(event) == ["Julebokk", "Underlig Jul"]

    def test_when_beer_exists_it_should_update_it_instead_of_adding_another(
        self, event
    ):  # noqa: E501
        Beer.objects.create(event=event, name="Underlig Jul")
        parsed = ParsedBeerList(beers=[ParsedBeer("underlig jul", is_homebrew=True)])

        result = import_beer_list(event, parsed)

        assert (result.created, result.existing) == (0, 1)
        assert event.beers.get().is_homebrew

    def test_when_beer_exists_it_should_add_only_missing_links(self, event):
        beer = Beer.objects.create(event=event, name="Underlig Jul")
        beer.links.create(label="Untappd", url="https://untappd.com/b/1")
        parsed = ParsedBeerList(
            beers=[
                ParsedBeer(
                    "Underlig Jul",
                    links=[
                        ParsedLink("Untappd", "https://untappd.com/b/1"),
                        ParsedLink("Vinmonopolet", "https://vinmonopolet.no/p/1"),
                    ],
                )
            ]
        )

        import_beer_list(event, parsed)

        assert sorted(beer.links.values_list("label", flat=True)) == [
            "Untappd",
            "Vinmonopolet",
        ]

    def test_when_not_replacing_it_should_keep_beers_missing_from_the_list(self, event):  # noqa: E501
        Beer.objects.create(event=event, name="Julebokk")

        import_beer_list(event, beer_list("Underlig Jul"))

        assert beer_names(event) == ["Julebokk", "Underlig Jul"]

    def test_when_replacing_it_should_remove_beers_missing_from_the_list(self, event):  # noqa: E501
        Beer.objects.create(event=event, name="Julebokk")

        result = import_beer_list(event, beer_list("Underlig Jul"), replace=True)

        assert result.removed == 1
        assert beer_names(event) == ["Underlig Jul"]

    def test_when_replacing_it_should_keep_beers_used_in_the_answer_key(
        self, event, user
    ):  # noqa: E501
        beer = Beer.objects.create(event=event, name="Julebokk")
        answer_key = AnswerKey.objects.create(event=event, created_by=user)
        AnswerKeyEntry.objects.create(answer_key=answer_key, beer_number=1, beer=beer)

        result = import_beer_list(event, beer_list("Underlig Jul"), replace=True)

        assert result.kept == ["Julebokk"]
        assert beer_names(event) == ["Julebokk", "Underlig Jul"]

    def test_when_importing_it_should_leave_other_events_alone(self, event, make_event):  # noqa: E501
        other_event = make_event()
        Beer.objects.create(event=other_event, name="Julebokk")

        import_beer_list(event, beer_list("Underlig Jul"), replace=True)

        assert beer_names(other_event) == ["Julebokk"]


@pytest.fixture()
def event(make_event):
    return make_event()


def beer_list(*names):
    return ParsedBeerList(beers=[ParsedBeer(name) for name in names])


def beer_names(event):
    return sorted(event.beers.values_list("name", flat=True))


def rows(*cells):
    return "\n".join("\t".join(row) for row in cells)


def names(parsed):
    return [beer.name for beer in parsed.beers]
