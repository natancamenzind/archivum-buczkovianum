"""Images uploaded in the editor panel. They are stored as WebP (ARC-29).

`archive.models.BaseModel` validates new uploads in `clean()` and converts them in `save()`.
"""

import io
from pathlib import PurePath

from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from PIL import Image, ImageOps, UnidentifiedImageError

WEBP_QUALITY = 85


def open_image(upload: "File[bytes]") -> Image.Image:
    """The decoded image. Raise a `ValidationError` if `upload` is not one."""
    try:
        upload.seek(0)
        image = Image.open(upload)
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ValidationError(
            _("The file is not a readable image. Upload a JPG, PNG or WebP file."),
            code="invalid_image",
        ) from error
    finally:
        upload.seek(0)
    return image


def to_webp(upload: "File[bytes]") -> "File[bytes]":
    """`upload` encoded as WebP, under the same name with a .webp extension.

    A WebP file is kept as it is: encoding it again would only lose quality. Photos are turned
    upright first, since WebP drops the EXIF orientation that cameras rely on.
    """
    image = open_image(upload)
    if image.format == "WEBP":
        return upload
    output = io.BytesIO()
    ImageOps.exif_transpose(image).save(output, format="WEBP", quality=WEBP_QUALITY)
    name = PurePath(upload.name or "image").with_suffix(".webp").name
    return ContentFile(output.getvalue(), name=name)
