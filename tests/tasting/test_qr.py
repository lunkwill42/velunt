from velunt.tasting.qr import generate_qr_svg


class TestGenerateQrSvg:
    def test_when_given_url_it_should_return_svg_string(self):
        svg = generate_qr_svg("https://example.com/abc123")
        assert "<svg" in svg
        assert "</svg>" in svg

    def test_when_given_url_it_should_produce_valid_xml(self):
        svg = generate_qr_svg("https://example.com/abc123")
        assert svg.startswith("<?xml")
