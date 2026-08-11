from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

class stringBase(BaseModel):
    name: str = Field(..., description="Record name/title")
    status: str = Field(default="ACTIVE", description="Lifecycle status")

class stringCreate(stringBase):
    pass

class stringResponse(stringBase):
    id: str
    created_at: str

    class Config:
        from_attributes = True
