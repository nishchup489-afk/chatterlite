from functools import lru_cache 
from typing import Literal 

from pydantic_settings import BaseSettings , SettingsConfigDict 


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env" , 
        env_file_encoding="utf-8",
        case_sensitive=False , 
        extra="ignore"
    )


    app_name : str = "ChatterLite API"
    app_version : str = "1.0.0"

    app_env: Literal[
        "development",
        "testing",
        "production",
    ] = "development"

    
    debug : bool = True 

    api_v1_prefix : str = "/api/v1"



    database_url : str

    redis_url : str


    cors_origin : list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]



@lru_cache
def get_settings() -> Settings:
    return Settings()