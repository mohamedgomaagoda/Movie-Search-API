from functools import lru_cache
from pydantic import BaseSettings, validator
from typing import Optional
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    # API Keys
    OMDB_API_KEY: str
    TMDB_API_KEY: str
    
    # Cache Settings
    CACHE_TTL: int = 300  # Cache time-to-live in seconds
    CACHE_MAX_SIZE: int = 1000  # Maximum number of items in cache
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60  # Number of requests allowed per minute
    RATE_LIMIT_BURST: int = 10  # Number of requests allowed in burst
    
    # API Timeouts
    API_TIMEOUT: int = 10  # Timeout for external API calls in seconds
    
    # Pagination Defaults
    DEFAULT_PAGE_SIZE: int = 10
    MAX_PAGE_SIZE: int = 50

    @validator('CACHE_TTL')
    def validate_cache_ttl(cls, v):
        if v < 0:
            raise ValueError("Cache TTL must be non-negative")
        return v

    @validator('CACHE_MAX_SIZE')
    def validate_cache_max_size(cls, v):
        if v < 1:
            raise ValueError("Cache max size must be positive")
        return v

    @validator('RATE_LIMIT_PER_MINUTE')
    def validate_rate_limit(cls, v):
        if v < 1:
            raise ValueError("Rate limit must be positive")
        return v

    @validator('API_TIMEOUT')
    def validate_timeout(cls, v):
        if v < 1:
            raise ValueError("API timeout must be positive")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True

        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )

@lru_cache()
def get_settings() -> Settings:
    """
    Create and cache settings instance
    """
    return Settings() 