from typing import Any

import pytest

from backend.engines.repository_engine.internal.service import RepositoryInternalService
from backend.engines.repository_engine.public import RepositoryPublicService
from backend.engines.repository_engine.schemas import RepositoryValidateInput


@pytest.mark.asyncio
async def test_public_service_validates_repository_url() -> None:
    service = RepositoryPublicService(internal=RepositoryInternalService(github_provider=object()))  # type: ignore[arg-type]
    result = await service.validate_repository_url(RepositoryValidateInput(repository_url="https://github.com/vibtools/ygit"))
    assert result.valid is True
    assert result.provider == "github"
    assert result.owner == "vibtools"
    assert result.repo == "ygit"
    assert result.normalized_url == "https://github.com/vibtools/ygit"
