from __future__ import annotations

import io
import json
import random
import zipfile

import pytest
from PIL import Image

from fitminiapp_api.db.session import get_session_context
from fitminiapp_api.models.user import User
from fitminiapp_api.services import account_exports
from fitminiapp_api.services.avatars import (
    AVATAR_UPLOAD_MAX_BYTES,
    AvatarValidationError,
    process_avatar_image,
)


def _login(client, telegram_user_id: int) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/dev-login",
        json={"telegram_user_id": telegram_user_id, "is_coach": False},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _image_bytes(
    image_format: str,
    *,
    color: tuple[int, int, int, int] = (105, 210, 20, 255),
    size: tuple[int, int] = (720, 480),
    exif: Image.Exif | None = None,
) -> bytes:
    image = Image.new("RGBA", size, color)
    if image_format == "JPEG":
        image = image.convert("RGB")
    output = io.BytesIO()
    save_options = {"exif": exif} if exif is not None else {}
    image.save(output, format=image_format, **save_options)
    return output.getvalue()


def _animated_webp() -> bytes:
    first = Image.new("RGB", (64, 64), "red")
    second = Image.new("RGB", (64, 64), "blue")
    output = io.BytesIO()
    first.save(output, format="WEBP", save_all=True, append_images=[second], duration=100, loop=0)
    return output.getvalue()


def _large_png() -> bytes:
    random_bytes = random.Random(110).randbytes(800 * 800 * 3)
    image = Image.frombytes("RGB", (800, 800), random_bytes)
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def _upload(client, headers: dict[str, str], content: bytes, filename: str, media_type: str):
    return client.put(
        "/api/v1/me/avatar",
        headers=headers,
        files={"file": (filename, content, media_type)},
    )


def test_avatar_is_authenticated_private_and_uses_decoded_format(client) -> None:
    jpeg = _image_bytes("JPEG")
    assert _upload(client, {}, jpeg, "avatar.jpg", "image/jpeg").status_code == 401
    assert client.get("/api/v1/me/avatar").status_code == 401

    owner_headers = _login(client, 9_810_001)
    other_headers = _login(client, 9_810_002)
    uploaded = _upload(client, owner_headers, jpeg, "looks-like.svg", "image/svg+xml")
    assert uploaded.status_code == 200
    assert uploaded.json()["custom_avatar"]["content_type"] == "image/webp"
    assert uploaded.json()["custom_avatar"]["width"] == 512
    assert uploaded.json()["custom_avatar"]["height"] == 512

    downloaded = client.get("/api/v1/me/avatar", headers=owner_headers)
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"] == "image/webp"
    assert downloaded.headers["cache-control"] == "no-store, private"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    assert downloaded.headers["etag"].startswith('"')
    with Image.open(io.BytesIO(downloaded.content)) as image:
        assert image.format == "WEBP"
        assert image.size == (512, 512)

    assert client.get("/api/v1/me/avatar", headers=other_headers).status_code == 404


def test_avatar_rejects_unsupported_malformed_animated_and_bounded_inputs(client) -> None:
    headers = _login(client, 9_810_003)

    svg = b'<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'
    unsupported = _upload(client, headers, svg, "avatar.png", "image/png")
    assert unsupported.status_code == 422
    assert "повреждён" in unsupported.json()["detail"]

    malformed = _upload(client, headers, b"not-an-image", "avatar.webp", "image/webp")
    assert malformed.status_code == 422

    animated = _upload(client, headers, _animated_webp(), "avatar.webp", "image/webp")
    assert animated.status_code == 415
    assert "Анимированные" in animated.json()["detail"]

    too_many_bytes = _upload(
        client,
        headers,
        b"x" * (AVATAR_UPLOAD_MAX_BYTES + 1),
        "avatar.png",
        "image/png",
    )
    assert too_many_bytes.status_code == 413

    too_wide = _upload(
        client,
        headers,
        _image_bytes("PNG", size=(8193, 1)),
        "avatar.png",
        "image/png",
    )
    assert too_wide.status_code == 413
    assert client.get("/api/v1/me", headers=headers).json()["custom_avatar"] is None


def test_avatar_accepts_valid_upload_larger_than_default_request_limit(client) -> None:
    headers = _login(client, 9_810_007)
    source = _large_png()
    assert 1024 * 1024 < len(source) <= AVATAR_UPLOAD_MAX_BYTES

    uploaded = _upload(client, headers, source, "large-avatar.png", "image/png")

    assert uploaded.status_code == 200
    assert uploaded.json()["custom_avatar"]["content_type"] == "image/webp"


def test_avatar_processing_deadline_fails_closed() -> None:
    ticks = iter((0.0, 4.0))
    with pytest.raises(AvatarValidationError, match="слишком много времени"):
        process_avatar_image(_image_bytes("PNG"), clock=lambda: next(ticks))


def test_avatar_strips_metadata_and_failed_replace_keeps_previous_blob(client) -> None:
    headers = _login(client, 9_810_004)
    exif = Image.Exif()
    exif[270] = "sensitive-description"
    exif[274] = 6
    first = _image_bytes("JPEG", color=(255, 0, 0, 255), size=(320, 640), exif=exif)
    assert _upload(client, headers, first, "portrait.jpg", "image/jpeg").status_code == 200
    original = client.get("/api/v1/me/avatar", headers=headers).content

    failed = _upload(client, headers, b"broken", "replacement.jpg", "image/jpeg")
    assert failed.status_code == 422
    assert client.get("/api/v1/me/avatar", headers=headers).content == original

    with Image.open(io.BytesIO(original)) as normalized:
        assert normalized.size == (512, 512)
        assert not normalized.getexif()
        assert "exif" not in normalized.info

    second = _image_bytes("PNG", color=(0, 0, 255, 255))
    replaced = _upload(client, headers, second, "replacement.png", "image/png")
    assert replaced.status_code == 200
    assert client.get("/api/v1/me/avatar", headers=headers).content != original
    with get_session_context() as db:
        user_id = client.get("/api/v1/me", headers=headers).json()["id"]
        stored = db.query(User).filter(User.id == user_id).one()
        assert stored.custom_avatar_updated_at is not None
        assert stored.custom_avatar_byte_size == len(stored.custom_avatar_image_bytes or b"")


def test_avatar_delete_restores_provider_fallback_without_changing_provider_photo(client) -> None:
    headers = _login(client, 9_810_005)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    with get_session_context() as db:
        user = db.query(User).filter(User.id == user_id).one()
        user.photo_url = "https://provider.example.test/avatar.jpg"

    assert (
        _upload(client, headers, _image_bytes("WEBP"), "avatar.webp", "image/webp").status_code
        == 200
    )
    deleted = client.delete("/api/v1/me/avatar", headers=headers)
    assert deleted.status_code == 200
    current = deleted.json()
    assert current["custom_avatar"] is None
    assert current["photo_url"] == "https://provider.example.test/avatar.jpg"
    assert client.get("/api/v1/me/avatar", headers=headers).status_code == 404
    assert client.delete("/api/v1/me/avatar", headers=headers).status_code == 200


def test_avatar_is_in_account_export_and_removed_with_account(client) -> None:
    headers = _login(client, 9_810_006)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    assert (
        _upload(client, headers, _image_bytes("PNG"), "avatar.png", "image/png").status_code == 200
    )

    export = client.post("/api/v1/me/exports", headers=headers)
    assert export.status_code == 201
    downloaded = client.get(
        f"/api/v1/me/exports/{export.json()['export_id']}/download",
        headers=headers,
    )
    with zipfile.ZipFile(io.BytesIO(downloaded.content)) as archive:
        assert "avatar/avatar.webp" in archive.namelist()
        payload = json.loads(archive.read("account.json"))
        exported_avatar = archive.read("avatar/avatar.webp")
    assert payload["custom_avatar"]["file"] == "avatar/avatar.webp"
    assert payload["custom_avatar"]["byte_size"] == len(exported_avatar)
    assert payload["custom_avatar"]["sha256"]

    deleted = client.request(
        "DELETE",
        "/api/v1/me/account",
        headers=headers,
        json={"confirmation": "DELETE"},
    )
    assert deleted.status_code == 204
    with get_session_context() as db:
        assert db.query(User).filter(User.id == user_id).first() is None


def test_account_export_uses_one_avatar_metadata_and_bytes_snapshot(
    client, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = _login(client, 9_810_008)
    user_id = client.get("/api/v1/me", headers=headers).json()["id"]
    assert (
        _upload(client, headers, _image_bytes("PNG"), "avatar.png", "image/png").status_code == 200
    )

    with get_session_context() as db:
        user = db.query(User).filter(User.id == user_id).one()
        original_bytes = bytes(user.custom_avatar_image_bytes or b"")
        original_sha256 = user.custom_avatar_sha256
        build_payload = account_exports.build_account_export

        def replace_avatar_after_snapshot(session, snapshot_user):
            payload = build_payload(session, snapshot_user)
            replacement = process_avatar_image(_image_bytes("PNG", color=(0, 0, 255, 255)))
            snapshot_user.custom_avatar_image_bytes = replacement.image_bytes
            snapshot_user.custom_avatar_byte_size = len(replacement.image_bytes)
            snapshot_user.custom_avatar_sha256 = replacement.sha256
            session.flush()
            return payload

        monkeypatch.setattr(account_exports, "build_account_export", replace_avatar_after_snapshot)
        archive_bytes, _ = account_exports.build_account_export_archive(db, user)

    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        payload = json.loads(archive.read("account.json"))
        exported_avatar = archive.read("avatar/avatar.webp")
    assert exported_avatar == original_bytes
    assert payload["custom_avatar"]["sha256"] == original_sha256
    assert payload["custom_avatar"]["byte_size"] == len(original_bytes)
