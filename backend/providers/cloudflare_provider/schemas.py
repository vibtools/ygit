from pydantic import BaseModel

class ProviderResponse(BaseModel):
    provider: str
    ok: bool
