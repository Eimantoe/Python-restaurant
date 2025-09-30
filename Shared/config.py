from pydantic_settings import BaseSettings, SettingsConfigDict
    
class Settings(BaseSettings): # type: ignore
    debug_mode: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()