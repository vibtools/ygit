from __future__ import annotations

from pydantic import BaseModel, Field, SecretStr


class CloudflareOAuthResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = None
    scope: str | None = None


class CloudflareAccount(BaseModel):
    account_id: str
    account_name: str


class CloudflarePagesProject(BaseModel):
    project_id: str
    project_name: str
    production_branch: str
    subdomain: str | None = None


class CloudflarePagesArtifactFile(BaseModel):
    relative_path: str
    content_hash: str = Field(
        pattern=r"^[0-9a-f]{32}$"
    )
    size_bytes: int = Field(ge=0)


class CloudflarePagesArtifactManifest(BaseModel):
    output_directory_name: str
    file_count: int = Field(ge=1, le=20_000)
    total_bytes: int = Field(ge=0)
    files: list[CloudflarePagesArtifactFile]
    manifest: dict[str, str]


class CloudflarePagesUploadToken(BaseModel):
    upload_token: SecretStr


class CloudflarePagesAssetUploadPlan(BaseModel):
    upload_token: SecretStr
    requested_hash_count: int = Field(
        ge=1,
        le=20_000,
    )
    missing_hashes: list[str]
    cached_hash_count: int = Field(ge=0)


class CloudflarePagesAssetUploadBatchResult(BaseModel):
    uploaded_hashes: list[str]
    uploaded_file_count: int = Field(ge=1)
    uploaded_bytes: int = Field(ge=0)


class CloudflarePagesHashUpsertResult(BaseModel):
    registered_hashes: list[str]
    registered_hash_count: int = Field(
        ge=1,
        le=20_000,
    )


class CloudflareAccountValidation(BaseModel):
    provider: str = "cloudflare"
    account_id: str
    account_name: str
    scopes: list[str] = Field(default_factory=list)
