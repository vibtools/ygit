from __future__ import annotations

from urllib.parse import quote, urlencode

import json
import re

import httpx

from backend.providers.cloudflare_provider.artifacts import (
    CloudflarePagesAssetUploadBatch,
)
from backend.providers.cloudflare_provider.errors import (
    CloudflareAccountValidationError,
    CloudflareOAuthConfigurationError,
    CloudflareOAuthExchangeError,
    CloudflareOAuthRefreshError,
    CloudflarePagesAssetUploadError,
    CloudflarePagesDeploymentError,
    CloudflarePagesProjectError,
    CloudflareProviderUnavailableError,
)
from backend.providers.cloudflare_provider.schemas import (
    CloudflareAccount,
    CloudflareAccountValidation,
    CloudflareOAuthResponse,
    CloudflarePagesArtifactManifest,
    CloudflarePagesAssetUploadBatchResult,
    CloudflarePagesAssetUploadPlan,
    CloudflarePagesDeployment,
    CloudflarePagesHashUpsertResult,
    CloudflarePagesProject,
    CloudflarePagesUploadToken,
)


class CloudflareProviderClient:
    def __init__(
        self,
        *,
        authorization_url: str = "https://dash.cloudflare.com/oauth2/auth",
        token_url: str = "https://dash.cloudflare.com/oauth2/token",
        api_base_url: str = "https://api.cloudflare.com/client/v4",
        timeout_seconds: float = 10.0,
    ) -> None:
        self.authorization_url = authorization_url
        self.token_url = token_url
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    @staticmethod
    def _normalize_oauth_scope_string(scopes: str) -> str:
        if not scopes:
            return ""

        normalized = str(scopes).strip()
        normalized = normalized.replace('\\"', '"').replace("\\'", "'")
        parts = [
            part.strip().strip("\\\"'")
            for part in normalized.split()
        ]
        return " ".join(part for part in parts if part)

    def build_oauth_authorization_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        scopes: str,
        state: str,
    ) -> str:
        if not client_id:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth client ID is missing.")
        if not redirect_uri:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth redirect URI is missing.")
        if not state:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth state is missing.")

        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "state": state,
        }

        normalized_scopes = self._normalize_oauth_scope_string(scopes)
        if normalized_scopes:
            params["scope"] = normalized_scopes

        return f"{self.authorization_url}?{urlencode(params)}"

    async def exchange_oauth_code(
        self,
        *,
        code_value: str,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> CloudflareOAuthResponse:
        if not code_value:
            raise CloudflareOAuthExchangeError("Cloudflare OAuth code is missing.")
        if not client_id or not client_secret:
            raise CloudflareOAuthConfigurationError("Cloudflare OAuth credentials are missing.")

        form_data = {
            "grant_type": "authorization_code",
            "code": code_value,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(self.token_url, data=form_data)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError("Cloudflare OAuth token endpoint is unavailable.") from exc

        if response.status_code >= 400:
            raise CloudflareOAuthExchangeError("Cloudflare OAuth token exchange failed.")

        return CloudflareOAuthResponse.model_validate(response.json())

    async def refresh_oauth_token(
        self,
        *,
        refresh_value: str,
        client_id: str,
        client_secret: str,
    ) -> CloudflareOAuthResponse:
        normalized_refresh = refresh_value.strip()

        if not normalized_refresh:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh value is missing."
            )

        if not client_id or not client_secret:
            raise CloudflareOAuthConfigurationError(
                "Cloudflare OAuth credentials are missing."
            )

        form_data = {
            "grant_type": "refresh_token",
            "refresh_token": normalized_refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds
            ) as client:
                response = await client.post(
                    self.token_url,
                    data=form_data,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare OAuth token endpoint is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh failed."
            )

        try:
            payload = response.json()
            return CloudflareOAuthResponse.model_validate(
                payload
            )
        except (TypeError, ValueError) as exc:
            raise CloudflareOAuthRefreshError(
                "Cloudflare OAuth refresh returned an invalid response."
            ) from exc

    @staticmethod
    def _required_pages_value(
        value: str,
        *,
        label: str,
    ) -> str:
        normalized = str(value or "").strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in ("\x00", "\r", "\n")
            )
        ):
            raise CloudflarePagesProjectError(
                f"Cloudflare Pages {label} is invalid."
            )

        return normalized

    @staticmethod
    def _pages_project_from_payload(
        payload: object,
    ) -> CloudflarePagesProject:
        if not isinstance(payload, dict):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            )

        result = payload.get("result")

        if (
            payload.get("success") is not True
            or not isinstance(result, dict)
        ):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            )

        project_data = {
            "project_id": str(result.get("id") or "").strip(),
            "project_name": str(result.get("name") or "").strip(),
            "production_branch": str(
                result.get("production_branch") or ""
            ).strip(),
            "subdomain": (
                str(result.get("subdomain")).strip()
                if result.get("subdomain")
                else None
            ),
        }

        if (
            not project_data["project_id"]
            or not project_data["project_name"]
            or not project_data["production_branch"]
        ):
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned incomplete project data."
            )

        try:
            return CloudflarePagesProject.model_validate(project_data)
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned invalid project data."
            ) from exc

    async def get_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        bearer_value: str,
    ) -> CloudflarePagesProject | None:
        account_value = self._required_pages_value(
            account_id,
            label="account identifier",
        )
        project_value = self._required_pages_value(
            project_name,
            label="project name",
        )
        access_value = self._required_pages_value(
            bearer_value,
            label="access credential",
        )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects/"
            f"{quote(project_value, safe='')}"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages project API is unavailable."
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages project lookup failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            ) from exc

        return self._pages_project_from_payload(payload)

    async def create_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        production_branch: str,
        bearer_value: str,
    ) -> CloudflarePagesProject:
        account_value = self._required_pages_value(
            account_id,
            label="account identifier",
        )
        project_value = self._required_pages_value(
            project_name,
            label="project name",
        )
        branch_value = self._required_pages_value(
            production_branch,
            label="production branch",
        )
        access_value = self._required_pages_value(
            bearer_value,
            label="access credential",
        )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }
        body = {
            "name": project_value,
            "production_branch": branch_value,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(url, json=body)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages project API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages project creation failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesProjectError(
                "Cloudflare Pages returned an invalid response."
            ) from exc

        return self._pages_project_from_payload(payload)

    async def ensure_pages_project(
        self,
        *,
        account_id: str,
        project_name: str,
        production_branch: str,
        bearer_value: str,
    ) -> CloudflarePagesProject:
        existing = await self.get_pages_project(
            account_id=account_id,
            project_name=project_name,
            bearer_value=bearer_value,
        )

        if existing is not None:
            return existing

        return await self.create_pages_project(
            account_id=account_id,
            project_name=project_name,
            production_branch=production_branch,
            bearer_value=bearer_value,
        )


    @staticmethod
    def _required_pages_asset_value(
        value: str,
        *,
        label: str,
    ) -> str:
        normalized = str(value or "").strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise CloudflarePagesAssetUploadError(
                f"Cloudflare Pages {label} is invalid."
            )

        return normalized

    @staticmethod
    def _validated_pages_asset_hashes(
        content_hashes: list[str],
    ) -> list[str]:
        normalized = sorted(
            {
                str(content_hash or "").strip()
                for content_hash in content_hashes
            }
        )

        if not normalized:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages asset hashes are missing."
            )

        if len(normalized) > 20_000:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages asset hash limit exceeded."
            )

        if any(
            re.fullmatch(r"[0-9a-f]{32}", value)
            is None
            for value in normalized
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages asset hash is invalid."
            )

        return normalized

    @staticmethod
    def _pages_upload_token_from_payload(
        payload: object,
    ) -> CloudflarePagesUploadToken:
        if not isinstance(payload, dict):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid upload-token response."
            )

        result = payload.get("result")

        if (
            payload.get("success") is not True
            or not isinstance(result, dict)
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid upload-token response."
            )

        upload_token = str(
            result.get("jwt")
            or ""
        ).strip()

        if (
            not upload_token
            or any(
                character in upload_token
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid upload token."
            )

        token_fields = {
            "upload_token": upload_token,
        }
        return CloudflarePagesUploadToken(
            **token_fields
        )

    async def get_pages_upload_token(
        self,
        *,
        account_id: str,
        project_name: str,
        bearer_value: str,
    ) -> CloudflarePagesUploadToken:
        account_value = self._required_pages_asset_value(
            account_id,
            label="account identifier",
        )
        project_value = self._required_pages_asset_value(
            project_name,
            label="project name",
        )
        access_value = self._required_pages_asset_value(
            bearer_value,
            label="access credential",
        )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects/"
            f"{quote(project_value, safe='')}/upload-token"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages upload-token API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload-token request failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid upload-token response."
            ) from exc

        return self._pages_upload_token_from_payload(
            payload
        )

    async def check_missing_pages_assets(
        self,
        *,
        upload_token: CloudflarePagesUploadToken,
        content_hashes: list[str],
    ) -> CloudflarePagesAssetUploadPlan:
        requested_hashes = (
            self._validated_pages_asset_hashes(
                content_hashes
            )
        )
        upload_value = (
            upload_token.upload_token
            .get_secret_value()
            .strip()
        )

        if (
            not upload_value
            or any(
                character in upload_value
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload token is invalid."
            )

        url = (
            f"{self.api_base_url}/pages/assets/"
            "check-missing"
        )
        headers = {
            "Authorization": f"Bearer {upload_value}",
            "Content-Type": "application/json",
        }
        body = {
            "hashes": requested_hashes,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(
                    url,
                    json=body,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages asset cache API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages missing-asset check failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid missing-asset response."
            ) from exc

        if (
            not isinstance(payload, dict)
            or payload.get("success") is not True
            or not isinstance(
                payload.get("result"),
                list,
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid missing-asset response."
            )

        raw_missing = payload["result"]

        if any(
            not isinstance(value, str)
            for value in raw_missing
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned invalid missing asset hashes."
            )

        missing_hashes = sorted(
            value.strip()
            for value in raw_missing
        )

        if (
            len(missing_hashes)
            != len(set(missing_hashes))
            or any(
                re.fullmatch(
                    r"[0-9a-f]{32}",
                    value,
                )
                is None
                for value in missing_hashes
            )
            or not set(missing_hashes).issubset(
                requested_hashes
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned invalid missing asset hashes."
            )

        plan_fields = {
            "upload_token": upload_token.upload_token,
            "requested_hash_count": len(
                requested_hashes
            ),
            "missing_hashes": missing_hashes,
            "cached_hash_count": (
                len(requested_hashes)
                - len(missing_hashes)
            ),
        }
        return CloudflarePagesAssetUploadPlan(
            **plan_fields
        )

    async def prepare_pages_asset_upload(
        self,
        *,
        account_id: str,
        project_name: str,
        bearer_value: str,
        content_hashes: list[str],
    ) -> CloudflarePagesAssetUploadPlan:
        upload_token = (
            await self.get_pages_upload_token(
                account_id=account_id,
                project_name=project_name,
                bearer_value=bearer_value,
            )
        )

        request_fields = {
            "upload_token": upload_token,
            "content_hashes": content_hashes,
        }
        return await self.check_missing_pages_assets(
            **request_fields
        )


    async def upload_pages_asset_batch(
        self,
        *,
        upload_session: CloudflarePagesUploadToken,
        batch: CloudflarePagesAssetUploadBatch,
    ) -> CloudflarePagesAssetUploadBatchResult:
        upload_value = (
            upload_session.upload_token
            .get_secret_value()
            .strip()
        )

        if (
            not upload_value
            or any(
                character in upload_value
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload token is invalid."
            )

        if not batch.items:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload batch is empty."
            )

        hashes = [
            item.content_hash
            for item in batch.items
        ]

        if (
            len(hashes) != len(set(hashes))
            or batch.total_bytes
            != sum(
                item.size_bytes
                for item in batch.items
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload batch is invalid."
            )

        url = (
            f"{self.api_base_url}/pages/assets/"
            "upload"
        )
        headers = {
            "Authorization": f"Bearer {upload_value}",
            "Content-Type": "application/json",
        }
        payload = [
            item.api_payload()
            for item in batch.items
        ]

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(
                    url,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages asset upload API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages asset upload failed."
            )

        try:
            response_payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid asset upload response."
            ) from exc

        if (
            not isinstance(response_payload, dict)
            or response_payload.get("success")
            is not True
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid asset upload response."
            )

        result_fields = {
            "uploaded_hashes": sorted(hashes),
            "uploaded_file_count": len(hashes),
            "uploaded_bytes": batch.total_bytes,
        }
        return CloudflarePagesAssetUploadBatchResult(
            **result_fields
        )


    async def upsert_pages_asset_hashes(
        self,
        *,
        upload_session: CloudflarePagesUploadToken,
        content_hashes: list[str],
    ) -> CloudflarePagesHashUpsertResult:
        registered_hashes = (
            self._validated_pages_asset_hashes(
                content_hashes
            )
        )
        upload_value = (
            upload_session.upload_token
            .get_secret_value()
            .strip()
        )

        if (
            not upload_value
            or any(
                character in upload_value
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages upload token is invalid."
            )

        url = (
            f"{self.api_base_url}/pages/assets/"
            "upsert-hashes"
        )
        headers = {
            "Authorization": f"Bearer {upload_value}",
            "Content-Type": "application/json",
        }
        body = {
            "hashes": registered_hashes,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(
                    url,
                    json=body,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages hash registration API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages hash registration failed."
            )

        try:
            response_payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid hash registration response."
            ) from exc

        if (
            not isinstance(response_payload, dict)
            or response_payload.get("success")
            is not True
        ):
            raise CloudflarePagesAssetUploadError(
                "Cloudflare Pages returned an invalid hash registration response."
            )

        result_fields = {
            "registered_hashes": registered_hashes,
            "registered_hash_count": len(
                registered_hashes
            ),
        }
        return CloudflarePagesHashUpsertResult(
            **result_fields
        )


    @staticmethod
    def _required_pages_deployment_value(
        value: str,
        *,
        label: str,
        max_length: int | None = None,
    ) -> str:
        normalized = str(value or "").strip()

        if (
            not normalized
            or any(
                character in normalized
                for character in (
                    "\x00",
                    "\r",
                    "\n",
                )
            )
            or (
                max_length is not None
                and len(normalized) > max_length
            )
        ):
            raise CloudflarePagesDeploymentError(
                f"Cloudflare Pages deployment {label} is invalid."
            )

        return normalized

    @staticmethod
    def _truncate_utf8_bytes(
        value: str,
        *,
        max_bytes: int,
    ) -> str:
        if max_bytes < 1:
            raise ValueError(
                "max_bytes must be positive."
            )

        encoded = value.encode("utf-8")

        if len(encoded) <= max_bytes:
            return value

        truncated = encoded[:max_bytes]

        while truncated:
            try:
                return truncated.decode("utf-8")
            except UnicodeDecodeError:
                truncated = truncated[:-1]

        return ""

    @staticmethod
    def _validated_pages_deployment_manifest(
        manifest: CloudflarePagesArtifactManifest,
    ) -> dict[str, str]:
        expected_manifest = {
            item.relative_path: item.content_hash
            for item in manifest.files
        }

        if (
            manifest.file_count
            != len(manifest.files)
            or manifest.file_count
            != len(expected_manifest)
            or manifest.total_bytes
            != sum(
                item.size_bytes
                for item in manifest.files
            )
            or expected_manifest
            != manifest.manifest
        ):
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages deployment manifest is inconsistent."
            )

        deployment_manifest: dict[str, str] = {}

        for relative_path, content_hash in sorted(
            expected_manifest.items()
        ):
            if (
                not relative_path
                or relative_path.startswith("/")
                or "\\" in relative_path
                or "\x00" in relative_path
                or any(
                    part in (
                        "",
                        ".",
                        "..",
                    )
                    for part in relative_path.split("/")
                )
                or re.fullmatch(
                    r"[0-9a-f]{32}",
                    content_hash,
                )
                is None
            ):
                raise CloudflarePagesDeploymentError(
                    "Cloudflare Pages deployment manifest is invalid."
                )

            deployment_manifest[
                "/" + relative_path
            ] = content_hash

        if (
            not deployment_manifest
            or len(deployment_manifest) > 20_000
        ):
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages deployment manifest is invalid."
            )

        return deployment_manifest

    @staticmethod
    def _pages_deployment_from_payload(
        payload: object,
    ) -> CloudflarePagesDeployment:
        if not isinstance(payload, dict):
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned an invalid deployment response."
            )

        result = payload.get("result")

        if (
            payload.get("success") is not True
            or not isinstance(result, dict)
        ):
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned an invalid deployment response."
            )

        aliases_value = result.get("aliases")

        if aliases_value is None:
            aliases: list[str] = []
        elif (
            isinstance(aliases_value, list)
            and all(
                isinstance(value, str)
                and value.strip()
                for value in aliases_value
            )
        ):
            aliases = sorted(
                value.strip()
                for value in aliases_value
            )
        else:
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned invalid deployment aliases."
            )

        latest_stage = result.get("latest_stage")
        stage_name: str | None = None
        stage_status: str | None = None

        if latest_stage is not None:
            if not isinstance(latest_stage, dict):
                raise CloudflarePagesDeploymentError(
                    "Cloudflare Pages returned an invalid deployment stage."
                )

            if latest_stage.get("name") is not None:
                stage_name = str(
                    latest_stage.get("name")
                ).strip() or None

            if latest_stage.get("status") is not None:
                stage_status = str(
                    latest_stage.get("status")
                ).strip() or None

        trigger = result.get("deployment_trigger")
        metadata: dict[str, object] = {}

        if trigger is not None:
            if not isinstance(trigger, dict):
                raise CloudflarePagesDeploymentError(
                    "Cloudflare Pages returned an invalid deployment trigger."
                )

            raw_metadata = trigger.get("metadata")

            if raw_metadata is not None:
                if not isinstance(
                    raw_metadata,
                    dict,
                ):
                    raise CloudflarePagesDeploymentError(
                        "Cloudflare Pages returned invalid deployment metadata."
                    )

                metadata = raw_metadata

        deployment_fields = {
            "deployment_id": str(
                result.get("id") or ""
            ).strip(),
            "project_id": str(
                result.get("project_id") or ""
            ).strip(),
            "project_name": str(
                result.get("project_name") or ""
            ).strip(),
            "environment": str(
                result.get("environment") or ""
            ).strip(),
            "url": str(
                result.get("url") or ""
            ).strip(),
            "aliases": aliases,
            "created_on": str(
                result.get("created_on") or ""
            ).strip(),
            "stage_name": stage_name,
            "stage_status": stage_status,
            "branch": (
                str(metadata.get("branch")).strip()
                if metadata.get("branch")
                else None
            ),
            "commit_hash": (
                str(
                    metadata.get(
                        "commit_hash"
                    )
                ).strip()
                if metadata.get("commit_hash")
                else None
            ),
            "commit_message": (
                str(
                    metadata.get(
                        "commit_message"
                    )
                ).strip()
                if metadata.get(
                    "commit_message"
                )
                else None
            ),
            "commit_dirty": (
                metadata.get("commit_dirty")
                if isinstance(
                    metadata.get(
                        "commit_dirty"
                    ),
                    bool,
                )
                else None
            ),
        }

        required_values = (
            deployment_fields[
                "deployment_id"
            ],
            deployment_fields["project_id"],
            deployment_fields[
                "project_name"
            ],
            deployment_fields["environment"],
            deployment_fields["url"],
            deployment_fields["created_on"],
        )

        if (
            any(
                not value
                for value in required_values
            )
            or deployment_fields["environment"]
            not in (
                "preview",
                "production",
            )
        ):
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned incomplete deployment data."
            )

        try:
            return CloudflarePagesDeployment.model_validate(
                deployment_fields
            )
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned invalid deployment data."
            ) from exc

    async def create_pages_deployment(
        self,
        *,
        account_id: str,
        project_name: str,
        bearer_value: str,
        branch: str,
        manifest: CloudflarePagesArtifactManifest,
        commit_hash: str | None = None,
        commit_message: str | None = None,
        commit_dirty: bool = False,
    ) -> CloudflarePagesDeployment:
        account_value = (
            self._required_pages_deployment_value(
                account_id,
                label="account identifier",
                max_length=32,
            )
        )
        project_value = (
            self._required_pages_deployment_value(
                project_name,
                label="project name",
            )
        )
        access_value = (
            self._required_pages_deployment_value(
                bearer_value,
                label="access credential",
            )
        )
        branch_value = (
            self._required_pages_deployment_value(
                branch,
                label="branch",
                max_length=255,
            )
        )
        deployment_manifest = (
            self._validated_pages_deployment_manifest(
                manifest
            )
        )

        commit_hash_value: str | None = None

        if commit_hash is not None:
            candidate_hash = str(
                commit_hash
            ).strip()

            if re.fullmatch(
                r"[0-9a-fA-F]{7,64}",
                candidate_hash,
            ) is None:
                raise CloudflarePagesDeploymentError(
                    "Cloudflare Pages deployment commit hash is invalid."
                )

            commit_hash_value = (
                candidate_hash.lower()
            )

        commit_message_value: str | None = None

        if commit_message is not None:
            candidate_message = str(
                commit_message
            ).strip()

            if "\x00" in candidate_message:
                raise CloudflarePagesDeploymentError(
                    "Cloudflare Pages deployment commit message is invalid."
                )

            if candidate_message:
                commit_message_value = (
                    self._truncate_utf8_bytes(
                        candidate_message,
                        max_bytes=384,
                    )
                )

        url = (
            f"{self.api_base_url}/accounts/"
            f"{quote(account_value, safe='')}/pages/projects/"
            f"{quote(project_value, safe='')}/deployments"
        )
        headers = {
            "Authorization": f"Bearer {access_value}",
        }
        form_fields: dict[
            str,
            tuple[None, str],
        ] = {
            "manifest": (
                None,
                json.dumps(
                    deployment_manifest,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
            "branch": (
                None,
                branch_value,
            ),
            "commit_dirty": (
                None,
                (
                    "true"
                    if commit_dirty
                    else "false"
                ),
            ),
            "pages_build_output_dir": (
                None,
                manifest.output_directory_name,
            ),
        }

        if commit_hash_value is not None:
            form_fields["commit_hash"] = (
                None,
                commit_hash_value,
            )

        if commit_message_value is not None:
            form_fields["commit_message"] = (
                None,
                commit_message_value,
            )

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds,
                headers=headers,
            ) as client:
                response = await client.post(
                    url,
                    files=form_fields,
                )
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError(
                "Cloudflare Pages deployment API is unavailable."
            ) from exc

        if response.status_code >= 400:
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages deployment creation failed."
            )

        try:
            payload = response.json()
        except (TypeError, ValueError) as exc:
            raise CloudflarePagesDeploymentError(
                "Cloudflare Pages returned an invalid deployment response."
            ) from exc

        return self._pages_deployment_from_payload(
            payload
        )

    async def list_accounts(self, bearer_value: str) -> list[CloudflareAccount]:
        if not bearer_value:
            raise CloudflareAccountValidationError("Cloudflare bearer value is missing.")

        headers = {"Authorization": f"Bearer {bearer_value}"}
        url = f"{self.api_base_url}/accounts"

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, headers=headers) as client:
                response = await client.get(url)
        except httpx.HTTPError as exc:
            raise CloudflareProviderUnavailableError("Cloudflare accounts API is unavailable.") from exc

        if response.status_code >= 400:
            raise CloudflareAccountValidationError("Cloudflare account validation failed.")

        payload = response.json()
        accounts = payload.get("result") or []
        return [
            CloudflareAccount(
                account_id=str(item.get("id") or ""),
                account_name=str(item.get("name") or "Cloudflare Account"),
            )
            for item in accounts
            if item.get("id")
        ]

    async def validate_oauth_access(
        self,
        *,
        bearer_value: str,
        scopes: list[str] | None = None,
    ) -> CloudflareAccountValidation:
        accounts = await self.list_accounts(bearer_value)
        if not accounts:
            raise CloudflareAccountValidationError("No Cloudflare accounts are available.")

        account = accounts[0]
        return CloudflareAccountValidation(
            account_id=account.account_id,
            account_name=account.account_name,
            scopes=scopes or [],
        )

    async def validate_account(self, token_ref: str) -> dict[str, str]:
        if not token_ref:
            raise CloudflareAccountValidationError("Cloudflare token reference is missing.")
        return {
            "provider_account_id": "cloudflare-account-placeholder",
            "provider_account_name": "Cloudflare Account",
        }
