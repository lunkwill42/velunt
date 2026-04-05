import io

import qrcode
import qrcode.image.svg


def generate_qr_svg(url):
    """Generate an inline SVG QR code for the given URL.

    Uses currentColor for the fill so it adapts to light/dark themes.
    """
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    buffer = io.BytesIO()
    img.save(buffer)
    svg = buffer.getvalue().decode("utf-8")
    return svg.replace("<path ", '<path fill="currentColor" ', 1)
