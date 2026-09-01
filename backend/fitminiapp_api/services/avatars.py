from __future__ import annotations

import hashlib
import io
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.orm import Session

from fitminiapp_api.core.timezone import now_msk_naive
from fitminiapp_api.models.user import User

AVATAR_UPLOAD_MAX_BYTES = 5 * 1024 * 1024
AVATAR_MAX_SOURCE_DIMENSION = 8192
AVATAR_MAX_DECODED_PIXELS = 25_000_000
AVATAR_OUTPUT_DIMENSION = 512
AVATAR_OUTPUT_MAX_BYTES = 1024 * 1024
AVATAR_PROCESSING_TIMEOUT_SECONDS = 3.0
AVATAR_SUPPORTED_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})


class AvatarValidationError(ValueError):
    def __init__(self, message: str, *, status_code: int = 422) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True)
class ProcessedAvatar:
    image_bytes: bytes
    content_type: str
    width: int
    height: int
    sha256: str


def _ensure_within_deadline(started_at: float, clock: Callable[[], float]) -> None:
    if clock() - started_at > AVATAR_PROCESSING_TIMEOUT_SECONDS:
        raise AvatarValidationError(
            "Обработка изображения заняла слишком много времени. Выберите файл меньшего размера."
        )


def process_avatar_image(
    source: bytes,
    *,
    clock: Callable[[], float] = time.monotonic,
) -> ProcessedAvatar:
    if not source:
        raise AvatarValidationError("Файл изображения пуст")
    if len(source) > AVATAR_UPLOAD_MAX_BYTES:
        raise AvatarValidationError(
            "Файл больше 5 МБ. Выберите изображение меньшего размера.",
            status_code=413,
        )

    started_at = clock()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(source)) as opened:
                source_format = (opened.format or "").upper()
                if source_format not in AVATAR_SUPPORTED_FORMATS:
                    raise AvatarValidationError(
                        "Поддерживаются только JPEG, PNG и WebP.", status_code=415
                    )
                if getattr(opened, "is_animated", False) or getattr(opened, "n_frames", 1) != 1:
                    raise AvatarValidationError(
                        "Анимированные изображения не поддерживаются.", status_code=415
                    )
                width, height = opened.size
                if (
                    width <= 0
                    or height <= 0
                    or width > AVATAR_MAX_SOURCE_DIMENSION
                    or height > AVATAR_MAX_SOURCE_DIMENSION
                    or width * height > AVATAR_MAX_DECODED_PIXELS
                ):
                    raise AvatarValidationError(
                        "Слишком большое разрешение изображения.", status_code=413
                    )
                opened.load()
                _ensure_within_deadline(started_at, clock)
                oriented = ImageOps.exif_transpose(opened)
                normalized = ImageOps.fit(
                    oriented.convert("RGBA"),
                    (AVATAR_OUTPUT_DIMENSION, AVATAR_OUTPUT_DIMENSION),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
                _ensure_within_deadline(started_at, clock)
    except AvatarValidationError:
        raise
    except Image.DecompressionBombError, Image.DecompressionBombWarning:
        raise AvatarValidationError("Слишком большое разрешение изображения.", status_code=413)
    except UnidentifiedImageError, OSError, ValueError:
        raise AvatarValidationError("Файл повреждён или не является поддерживаемым изображением.")

    output = io.BytesIO()
    try:
        normalized.save(output, format="WEBP", quality=84, method=4, exact=True)
    except OSError:
        raise AvatarValidationError("Не удалось безопасно подготовить изображение.")
    _ensure_within_deadline(started_at, clock)
    image_bytes = output.getvalue()
    if not image_bytes or len(image_bytes) > AVATAR_OUTPUT_MAX_BYTES:
        raise AvatarValidationError("Подготовленный аватар получился слишком большим.")

    return ProcessedAvatar(
        image_bytes=image_bytes,
        content_type="image/webp",
        width=AVATAR_OUTPUT_DIMENSION,
        height=AVATAR_OUTPUT_DIMENSION,
        sha256=hashlib.sha256(image_bytes).hexdigest(),
    )


def save_user_avatar(db: Session, user_id: int, processed: ProcessedAvatar) -> User:
    user = db.query(User).filter(User.id == user_id).with_for_update().one()
    now = now_msk_naive()
    if user.custom_avatar_created_at is None:
        user.custom_avatar_created_at = now
    user.custom_avatar_content_type = processed.content_type
    user.custom_avatar_image_bytes = processed.image_bytes
    user.custom_avatar_byte_size = len(processed.image_bytes)
    user.custom_avatar_width = processed.width
    user.custom_avatar_height = processed.height
    user.custom_avatar_sha256 = processed.sha256
    user.custom_avatar_updated_at = now
    db.flush()
    return user


def delete_user_avatar(db: Session, user_id: int) -> bool:
    user = db.query(User).filter(User.id == user_id).with_for_update().one()
    if user.custom_avatar_updated_at is None:
        return False
    user.custom_avatar_content_type = None
    user.custom_avatar_image_bytes = None
    user.custom_avatar_byte_size = None
    user.custom_avatar_width = None
    user.custom_avatar_height = None
    user.custom_avatar_sha256 = None
    user.custom_avatar_created_at = None
    user.custom_avatar_updated_at = None
    db.flush()
    return True
