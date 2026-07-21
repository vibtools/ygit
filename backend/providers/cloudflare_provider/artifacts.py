from __future__ import annotations

import hashlib
from pathlib import Path

from backend.providers.cloudflare_provider.errors import (
    CloudflarePagesArtifactError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflarePagesArtifactFile,
    CloudflarePagesArtifactManifest,
)


CLOUDFLARE_PAGES_MAX_FILE_COUNT = 20_000
CLOUDFLARE_PAGES_MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024
_HASH_READ_CHUNK_BYTES = 1024 * 1024


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
