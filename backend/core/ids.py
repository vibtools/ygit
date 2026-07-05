from secrets import token_urlsafe

def new_id(prefix: str) -> str:
    normalized = prefix.strip("_")
    return f"{normalized}_{token_urlsafe(18)}"
