from __future__ import annotations

import base64
from collections.abc import Iterator
from dataclasses import dataclass, field
import hashlib
import mimetypes
from pathlib import Path
import re

from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesArtifactError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesArtifactFile,
    CloudflarePagesArtifactManifest,
)


CLOUDFLARE_PAGES_MAX_FILE_COUNT = 20_000
CLOUDFLARE_PAGES_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
CLOUDFLARE_PAGES_UPLOAD_BATCH_MAX_BYTES = 40 * 1024 * 1024
CLOUDFLARE_PAGES_UPLOAD_BATCH_MAX_FILES = 1_000
_HASH_READ_CHUNK_BYTES = 1024 * 1024


@dataclass(frozen=True, slots=True)
class CloudflarePagesAssetUploadItem:
    content_hash: str
    content_type: str
    encoded_value: str = field(repr=False)
    size_bytes: int

    def api_payload(self) -> dict[str, object]:
        return {
            "key": self.content_hash,
            "value": self.encoded_value,
            "metadata": {
                "contentType": self.content_type,
            },
            "base64": True,
        }


@dataclass(frozen=True, slots=True)
class CloudflarePagesAssetUploadBatch:
    items: tuple[
        CloudflarePagesAssetUploadItem,
        ...,
    ]
    total_bytes: int


class CloudflarePagesArtifactBuilder:
    def __init__(
        self,
        *,
        max_file_count: int = CLOUDFLARE_PAGES_MAX_FILE_COUNT,
        max_file_size_bytes: int = CLOUDFLARE_PAGES_MAX_FILE_SIZE_BYTES,
    ) -> None:
        if max_file_count < 1:
            raise ValueError("max_file_count must be positive.")
        if max_file_size_bytes < 1:
            raise ValueError("max_file_size_bytes must be positive.")

        self.max_file_count = max_file_count
        self.max_file_size_bytes = max_file_size_bytes

    @staticmethod
    def _content_hash(path: Path) -> str:
        digest = hashlib.sha256()

        try:
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(_HASH_READ_CHUNK_BYTES)
                    if not chunk:
                        break
                    digest.update(chunk)
        except OSError as exc:
            raise CloudflarePagesArtifactError(
                "Unable to read a build artifact."
            ) from exc

        return digest.hexdigest()[:32]

    @staticmethod
    def _relative_manifest_path(
        *,
        root: Path,
        path: Path,
    ) -> str:
        try:
            relative = path.relative_to(root)
        except ValueError as exc:
            raise CloudflarePagesArtifactError(
                "Build artifact escaped the output directory."
            ) from exc

        normalized = relative.as_posix()

        if (
            not normalized
            or normalized.startswith("/")
            or normalized == ".."
            or normalized.startswith("../")
            or "/../" in normalized
            or "\\" in normalized
            or "\x00" in normalized
        ):
            raise CloudflarePagesArtifactError(
                "Build artifact path is invalid."
            )

        return normalized

    def build(
        self,
        output_directory: str | Path,
    ) -> CloudflarePagesArtifactManifest:
        requested_root = Path(output_directory)

        if requested_root.is_symlink():
            raise CloudflarePagesArtifactError(
                "Build output directory cannot be a symlink."
            )

        try:
            root = requested_root.resolve(strict=True)
        except OSError as exc:
            raise CloudflarePagesArtifactError(
                "Build output directory does not exist."
            ) from exc

        if not root.is_dir():
            raise CloudflarePagesArtifactError(
                "Build output path is not a directory."
            )

        artifact_files: list[CloudflarePagesArtifactFile] = []
        manifest: dict[str, str] = {}
        total_bytes = 0

        try:
            candidates = sorted(
                root.rglob("*"),
                key=lambda item: item.as_posix(),
            )
        except OSError as exc:
            raise CloudflarePagesArtifactError(
                "Unable to scan the build output directory."
            ) from exc

        for candidate in candidates:
            if candidate.is_symlink():
                raise CloudflarePagesArtifactError(
                    "Build output cannot contain symlinks."
                )

            if candidate.is_dir():
                continue

            if not candidate.is_file():
                raise CloudflarePagesArtifactError(
                    "Build output contains an unsupported entry."
                )

            relative_path = self._relative_manifest_path(
                root=root,
                path=candidate,
            )

            try:
                stat_before = candidate.stat()
            except OSError as exc:
                raise CloudflarePagesArtifactError(
                    "Unable to inspect a build artifact."
                ) from exc

            if stat_before.st_size > self.max_file_size_bytes:
                raise CloudflarePagesArtifactError(
                    "Build artifact exceeds the file size limit."
                )

            if len(artifact_files) + 1 > self.max_file_count:
                raise CloudflarePagesArtifactError(
                    "Build output exceeds the file count limit."
                )

            content_hash = self._content_hash(candidate)

            try:
                stat_after = candidate.stat()
            except OSError as exc:
                raise CloudflarePagesArtifactError(
                    "Unable to verify a build artifact."
                ) from exc

            if (
                stat_before.st_size != stat_after.st_size
                or stat_before.st_mtime_ns != stat_after.st_mtime_ns
            ):
                raise CloudflarePagesArtifactError(
                    "Build artifact changed during hashing."
                )

            artifact = CloudflarePagesArtifactFile(
                relative_path=relative_path,
                content_hash=content_hash,
                size_bytes=stat_after.st_size,
            )
            artifact_files.append(artifact)
            manifest[relative_path] = content_hash
            total_bytes += stat_after.st_size

        if not artifact_files:
            raise CloudflarePagesArtifactError(
                "Build output directory is empty."
            )

        return CloudflarePagesArtifactManifest(
            output_directory_name=root.name,
            file_count=len(artifact_files),
            total_bytes=total_bytes,
            files=artifact_files,
            manifest=manifest,
        )

    @staticmethod
    def _validated_manifest_files(
        manifest: CloudflarePagesArtifactManifest,
        missing_hashes: list[str],
    ) -> list[CloudflarePagesArtifactFile]:
        expected_manifest = {
            item.relative_path: item.content_hash
            for item in manifest.files
        }

        if (
            manifest.file_count
            != len(manifest.files)
            or manifest.total_bytes
            != sum(
                item.size_bytes
                for item in manifest.files
            )
            or len(expected_manifest)
            != len(manifest.files)
            or expected_manifest
            != manifest.manifest
        ):
            raise CloudflarePagesArtifactError(
                "Build artifact manifest is inconsistent."
            )

        normalized_hashes = sorted(
            str(value or "").strip()
            for value in missing_hashes
        )

        if (
            len(normalized_hashes)
            != len(set(normalized_hashes))
            or any(
                re.fullmatch(
                    r"[0-9a-f]{32}",
                    value,
                )
                is None
                for value in normalized_hashes
            )
        ):
            raise CloudflarePagesArtifactError(
                "Missing asset hashes are invalid."
            )

        file_by_hash: dict[
            str,
            CloudflarePagesArtifactFile,
        ] = {}

        for item in sorted(
            manifest.files,
            key=lambda candidate: (
                candidate.relative_path
            ),
        ):
            file_by_hash.setdefault(
                item.content_hash,
                item,
            )

        foreign_hashes = (
            set(normalized_hashes)
            - set(file_by_hash)
        )

        if foreign_hashes:
            raise CloudflarePagesArtifactError(
                "Missing asset hash is not present in the build manifest."
            )

        return [
            file_by_hash[value]
            for value in normalized_hashes
        ]

    @staticmethod
    def _safe_manifest_file(
        *,
        root: Path,
        relative_path: str,
    ) -> Path:
        if (
            not relative_path
            or relative_path.startswith("/")
            or "\\" in relative_path
            or "\x00" in relative_path
        ):
            raise CloudflarePagesArtifactError(
                "Build artifact path is invalid."
            )

        parts = relative_path.split("/")

        if any(
            part in (
                "",
                ".",
                "..",
            )
            for part in parts
        ):
            raise CloudflarePagesArtifactError(
                "Build artifact path is invalid."
            )

        candidate = root

        for part in parts:
            candidate = candidate / part

            if candidate.is_symlink():
                raise CloudflarePagesArtifactError(
                    "Build output cannot contain symlinks."
                )

        try:
            resolved = candidate.resolve(
                strict=True
            )
            resolved.relative_to(root)
        except (OSError, ValueError) as exc:
            raise CloudflarePagesArtifactError(
                "Build artifact escaped the output directory."
            ) from exc

        if not resolved.is_file():
            raise CloudflarePagesArtifactError(
                "Build artifact is not a regular file."
            )

        return resolved

    @staticmethod
    def _load_upload_item(
        *,
        root: Path,
        artifact: CloudflarePagesArtifactFile,
    ) -> CloudflarePagesAssetUploadItem:
        path = (
            CloudflarePagesArtifactBuilder
            ._safe_manifest_file(
                root=root,
                relative_path=(
                    artifact.relative_path
                ),
            )
        )

        try:
            stat_before = path.stat()
            value = path.read_bytes()
            stat_after = path.stat()
        except OSError as exc:
            raise CloudflarePagesArtifactError(
                "Unable to read a build artifact."
            ) from exc

        if (
            stat_before.st_size
            != stat_after.st_size
            or stat_before.st_mtime_ns
            != stat_after.st_mtime_ns
            or stat_after.st_size
            != artifact.size_bytes
        ):
            raise CloudflarePagesArtifactError(
                "Build artifact changed after manifest creation."
            )

        content_hash = (
            hashlib.sha256(value)
            .hexdigest()[:32]
        )

        if content_hash != artifact.content_hash:
            raise CloudflarePagesArtifactError(
                "Build artifact hash no longer matches the manifest."
            )

        content_type = (
            mimetypes.guess_type(
                artifact.relative_path,
                strict=False,
            )[0]
            or "application/octet-stream"
        )

        item_fields = {
            "content_hash": content_hash,
            "content_type": content_type,
            "encoded_value": (
                base64.b64encode(value)
                .decode("ascii")
            ),
            "size_bytes": stat_after.st_size,
        }
        return CloudflarePagesAssetUploadItem(
            **item_fields
        )

    def iter_upload_batches(
        self,
        *,
        output_directory: str | Path,
        manifest: CloudflarePagesArtifactManifest,
        missing_hashes: list[str],
        batch_max_bytes: int = (
            CLOUDFLARE_PAGES_UPLOAD_BATCH_MAX_BYTES
        ),
        batch_max_files: int = (
            CLOUDFLARE_PAGES_UPLOAD_BATCH_MAX_FILES
        ),
    ) -> Iterator[
        CloudflarePagesAssetUploadBatch
    ]:
        if (
            batch_max_bytes < 1
            or batch_max_files < 1
        ):
            raise ValueError(
                "Upload batch limits must be positive."
            )

        requested_root = Path(
            output_directory
        )

        if requested_root.is_symlink():
            raise CloudflarePagesArtifactError(
                "Build output directory cannot be a symlink."
            )

        try:
            root = requested_root.resolve(
                strict=True
            )
        except OSError as exc:
            raise CloudflarePagesArtifactError(
                "Build output directory does not exist."
            ) from exc

        if (
            not root.is_dir()
            or root.name
            != manifest.output_directory_name
        ):
            raise CloudflarePagesArtifactError(
                "Build output directory does not match the manifest."
            )

        selected_files = (
            self._validated_manifest_files(
                manifest,
                missing_hashes,
            )
        )

        if not selected_files:
            return

        ordered_files = sorted(
            selected_files,
            key=lambda item: (
                -item.size_bytes,
                item.relative_path,
            ),
        )
        descriptor_batches: list[
            list[CloudflarePagesArtifactFile]
        ] = []
        batch_sizes: list[int] = []

        for artifact in ordered_files:
            inserted = False

            for index, descriptors in enumerate(
                descriptor_batches
            ):
                if (
                    len(descriptors)
                    < batch_max_files
                    and batch_sizes[index]
                    + artifact.size_bytes
                    <= batch_max_bytes
                ):
                    descriptors.append(artifact)
                    batch_sizes[index] += (
                        artifact.size_bytes
                    )
                    inserted = True
                    break

            if not inserted:
                if (
                    artifact.size_bytes
                    > batch_max_bytes
                ):
                    raise CloudflarePagesArtifactError(
                        "Build artifact exceeds the upload batch size limit."
                    )

                descriptor_batches.append(
                    [artifact]
                )
                batch_sizes.append(
                    artifact.size_bytes
                )

        for descriptors, total_bytes in zip(
            descriptor_batches,
            batch_sizes,
            strict=True,
        ):
            items = tuple(
                self._load_upload_item(
                    root=root,
                    artifact=artifact,
                )
                for artifact in descriptors
            )

            yield CloudflarePagesAssetUploadBatch(
                items=items,
                total_bytes=total_bytes,
            )
