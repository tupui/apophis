from typing import Optional

from pydantic import BaseModel


class Credentials(BaseModel):
    """Kraken credentials."""

    key: Optional[str]
    secret: Optional[str]
    future: bool = False
