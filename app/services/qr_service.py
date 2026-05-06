from io import BytesIO

from .errors import ValidationError


def make_qr_png(data, size=320):
    try:
        size = int(size)
    except (TypeError, ValueError):
        raise ValidationError("QR size must be a number.") from None
    size = max(140, min(size, 900))

    try:
        import qrcode
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError("The qrcode package is required to generate QR images.") from exc

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(fill_color="#1d2328", back_color="white").convert("RGB")
    resample = getattr(Image, "Resampling", Image).NEAREST
    image = image.resize((size, size), resample)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
