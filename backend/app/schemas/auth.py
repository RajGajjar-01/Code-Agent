from typing import Optional

from pydantic import BaseModel


class AuthStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
