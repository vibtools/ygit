SENSITIVE_LOG_KEYS = {"authorization", "cookie", "set-cookie", "github_token", "cloudflare_token", "access_token", "refresh_token", "client_secret", "database_url", "session_secret"}

def redact_sensitive_mapping(values: dict[str, object]) -> dict[str, object]:
    return {key: ("[REDACTED]" if key.lower() in SENSITIVE_LOG_KEYS else value) for key, value in values.items()}
