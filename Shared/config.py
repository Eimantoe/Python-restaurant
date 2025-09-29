from pydantic import BaseSettings

class Settings(BaseSettings): # type: ignore
    debug_mode: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()