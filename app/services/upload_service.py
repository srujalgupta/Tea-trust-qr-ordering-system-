import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

from .errors import ValidationError


Image.MAX_IMAGE_PIXELS = 12_000_000


def save_menu_image(file_storage, upload_folder, allowed_extensions):
    if not file_storage or not file_storage.filename:
        raise ValidationError("Image file is required.")

    original = secure_filename(file_storage.filename)
    suffix = Path(original).suffix.lower().lstrip(".")
    if suffix not in allowed_extensions:
        raise ValidationError("Allowed image formats: jpg, jpeg, png, webp.")

    try:
        file_storage.stream.seek(0)
        with Image.open(file_storage.stream) as image:
            image.verify()
    except (OSError, UnidentifiedImageError):
        raise ValidationError("Upload a valid image file.") from None
    finally:
        file_storage.stream.seek(0)

    filename = f"{uuid.uuid4().hex}.{suffix}"
    target_dir = Path(upload_folder)
    target_dir.mkdir(parents=True, exist_ok=True)
    file_storage.save(target_dir / filename)
    return filename
