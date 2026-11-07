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


def validate_image(upload: "File[bytes]") -> None:
    """Raise a `ValidationError` if `upload` is not a readable image. Checks the file without
    decoding its pixels: `to_webp()` decodes it once, on save."""
    try:
        upload.seek(0)
        with Image.open(upload) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError) as error:
        raise ValidationError(
            _("The file is not a readable image. Upload a JPG, PNG or WebP file."),
            code="invalid_image",
        ) from error
    finally:
        upload.seek(0)


def to_webp(upload: "File[bytes]") -> "File[bytes]":
    """`upload` encoded as WebP, under the same name with a .webp extension.

    A WebP file is kept as it is: encoding it again would only lose quality. Photos are turned
    upright first, since WebP drops the EXIF orientation that cameras rely on.
    """
    upload.seek(0)
    image = Image.open(upload)
    if image.format == "WEBP":
        upload.seek(0)
        return upload
    output = io.BytesIO()
    ImageOps.exif_transpose(image).save(output, format="WEBP", quality=WEBP_QUALITY)
    # Uploads always have a name; the fallback only satisfies the type of `File.name`.
    name = PurePath(upload.name or "image").with_suffix(".webp").name
    return ContentFile(output.getvalue(), name=name)
