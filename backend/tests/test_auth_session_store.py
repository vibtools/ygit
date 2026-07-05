from backend.engines.auth_engine.internal.session_store import AuthSessionManager, MemoryJsonSessionStore


async def test_login_flow_is_one_time() -> None:
    manager = AuthSessionManager(MemoryJsonSessionStore(), session_ttl_seconds=60, auth_flow_ttl_seconds=60)
    state = await manager.create_login_flow({"nonce": "n", "code_verifier": "v", "next_path": "/"})
    first = await manager.pop_login_flow(state)
    second = await manager.pop_login_flow(state)
    assert first is not None
    assert first["nonce"] == "n"
    assert second is None


async def test_session_roundtrip_and_delete() -> None:
    manager = AuthSessionManager(MemoryJsonSessionStore(), session_ttl_seconds=60, auth_flow_ttl_seconds=60)
    session_id = await manager.create_session({"user": {"id": "user_1", "email": "a@example.com"}})
    payload = await manager.get_session(session_id)
    assert payload is not None
    assert payload["user"]["id"] == "user_1"
    await manager.delete_session(session_id)
    assert await manager.get_session(session_id) is None
