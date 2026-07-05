import pytest

from backend.engines.project_engine.errors import ProjectNameInvalidError, ProjectSlugInvalidError
from backend.engines.project_engine.internal.validators import validate_project_name, validate_project_slug


def test_validate_project_name_normalizes_spaces() -> None:
    assert validate_project_name("  My   Portfolio  ") == "My Portfolio"


def test_validate_project_name_rejects_empty() -> None:
    with pytest.raises(ProjectNameInvalidError):
        validate_project_name("   ")


def test_validate_project_slug_accepts_valid_slug() -> None:
    assert validate_project_slug("My-Portfolio") == "my-portfolio"


@pytest.mark.parametrize("slug", ["api", "-bad", "bad-", "bad_slug", "x", "has space"])
def test_validate_project_slug_rejects_invalid(slug: str) -> None:
    with pytest.raises(ProjectSlugInvalidError):
        validate_project_slug(slug)
