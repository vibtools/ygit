from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from backend.providers.cloudflare_provider.artifacts import (
    CLOUDFLARE_PAGES_MAX_FILE_COUNT,
    CLOUDFLARE_PAGES_MAX_FILE_SIZE_BYTES,
    CloudflarePagesArtifactBuilder,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesArtifactError,
)


def truncated_sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()[:32]


def test_artifact_manifest_is_deterministic(tmp_path: Path) -> None:
    output = tmp_path / "dist"
    assets = output / "assets"
    assets.mkdir(parents=True)

    index_value = b"<h1>YGIT</h1>"
    css_value = b"body{color:white}"

    (output / "index.html").write_bytes(index_value)
    (assets / "app.css").write_bytes(css_value)

    result = CloudflarePagesArtifactBuilder().build(output)

    assert result.output_directory_name == "dist"
    assert result.file_count == 2
    assert result.total_bytes == len(index_value) + len(css_value)
    assert [item.relative_path for item in result.files] == [
        "assets/app.css",
        "index.html",
    ]
    assert result.manifest == {
        "assets/app.css": truncated_sha256(css_value),
        "index.html": truncated_sha256(index_value),
    }


def test_artifact_manifest_includes_hidden_files(tmp_path: Path) -> None:
    output = tmp_path / "public"
    (output / ".well-known").mkdir(parents=True)
    value = b"verification"
    (output / ".well-known" / "site-verification").write_bytes(value)

    result = CloudflarePagesArtifactBuilder().build(output)

    assert result.manifest == {
        ".well-known/site-verification": truncated_sha256(value)
    }


def test_missing_output_directory_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        CloudflarePagesArtifactError,
        match="does not exist",
    ):
        CloudflarePagesArtifactBuilder().build(tmp_path / "missing")


def test_empty_output_directory_is_rejected(tmp_path: Path) -> None:
    output = tmp_path / "empty"
    output.mkdir()

    with pytest.raises(
        CloudflarePagesArtifactError,
        match="is empty",
    ):
        CloudflarePagesArtifactBuilder().build(output)


def test_symlink_entry_is_rejected_without_following(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "dist"
    output.mkdir()
    linked = output / "linked.txt"
    linked.write_text("not actually followed", encoding="utf-8")

    original = Path.is_symlink

    def fake_is_symlink(path: Path) -> bool:
        if path == linked:
            return True
        return original(path)

    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)

    with pytest.raises(
        CloudflarePagesArtifactError,
        match="cannot contain symlinks",
    ):
        CloudflarePagesArtifactBuilder().build(output)


def test_file_size_limit_is_enforced(tmp_path: Path) -> None:
    output = tmp_path / "dist"
    output.mkdir()
    (output / "large.bin").write_bytes(b"12345")

    builder = CloudflarePagesArtifactBuilder(
        max_file_size_bytes=4,
    )

    with pytest.raises(
        CloudflarePagesArtifactError,
        match="file size limit",
    ):
        builder.build(output)


def test_file_count_limit_is_enforced(tmp_path: Path) -> None:
    output = tmp_path / "dist"
    output.mkdir()

    for index in range(3):
        (output / f"{index}.txt").write_text(
            str(index),
            encoding="utf-8",
        )

    builder = CloudflarePagesArtifactBuilder(max_file_count=2)

    with pytest.raises(
        CloudflarePagesArtifactError,
        match="file count limit",
    ):
        builder.build(output)


def test_cloudflare_limits_are_locked() -> None:
    assert CLOUDFLARE_PAGES_MAX_FILE_COUNT == 20_000
    assert CLOUDFLARE_PAGES_MAX_FILE_SIZE_BYTES == 25 * 1024 * 1024
