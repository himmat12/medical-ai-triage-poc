import os
from pydantic_settings import BaseSettings
from pydantic import Field

import os
from dotenv import load_dotenv


load_dotenv(override=True)


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./gp_frontdesk.db", env="DATABASE_URL")
    secret_key: str = Field(
        default="your-secret-key-change-this-in-production", env="SECRET_KEY"
    )
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=1440 * 30, env=os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
    )

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
