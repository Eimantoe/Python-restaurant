from pydantic_settings import BaseSettings, SettingsConfigDict
    
class Settings(BaseSettings): # type: ignore
    debug_mode: bool = True

    inventory_service_url               : str = "http://localhost:8000"
    inventory_service_menu_endpoint     : str = inventory_service_url + "/menu"
    consumeRecipeIngridients_endpoint   : str = inventory_service_url + "/consumeRecipeIngridients"


    waitress_service_url    : str = "http://localhost:6000"


    kitchen_service_url     : str = "http://localhost:7001"

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    
settings = Settings()