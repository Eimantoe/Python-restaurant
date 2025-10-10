from pydantic_settings import BaseSettings, SettingsConfigDict
    
class Settings(BaseSettings): # type: ignore
    debug_mode: bool = True

    inventory_service_url   : str = "https://localhost:8000"
    waitress_service_url    : str = "https://localhost:6000"
    kitchen_service_url     : str = "https://localhost:7000"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()