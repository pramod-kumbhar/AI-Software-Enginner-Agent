from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Generated Software System"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"

settings = Settings()
