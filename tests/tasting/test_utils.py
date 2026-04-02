import string

from velunt.tasting.utils import generate_public_id

VALID_CHARS = set(string.ascii_letters + string.digits)


class TestGeneratePublicId:
    def test_when_called_with_defaults_it_should_return_6_chars(self):
        assert len(generate_public_id()) == 6

    def test_when_called_with_custom_length_it_should_respect_it(self):
        assert len(generate_public_id(length=10)) == 10

    def test_when_called_it_should_only_contain_alphanumeric_chars(self):
        result = generate_public_id()
        assert all(c in VALID_CHARS for c in result)

    def test_when_called_twice_it_should_return_different_values(self):
        a = generate_public_id()
        b = generate_public_id()
        assert a != b
