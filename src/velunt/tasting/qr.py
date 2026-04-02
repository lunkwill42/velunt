import io

import qrcode
import qrcode.image.svg


def generate_qr_svg(url):
    """Generate an inline SVG QR code for the given URL."""
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
    buffer = io.BytesIO()
    img.save(buffer)
    return buffer.getvalue().decode("utf-8")
