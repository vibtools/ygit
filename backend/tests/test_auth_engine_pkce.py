from backend.engines.auth_engine.internal.pkce import code_challenge_s256, generate_code_verifier


def test_pkce_challenge_is_urlsafe() -> None:
    verifier = generate_code_verifier()
    challenge = code_challenge_s256(verifier)
    assert len(verifier) >= 43
    assert "=" not in challenge
    assert "+" not in challenge
    assert "/" not in challenge


def test_pkce_challenge_is_deterministic_for_verifier() -> None:
    verifier = "a" * 64
    assert code_challenge_s256(verifier) == code_challenge_s256(verifier)
