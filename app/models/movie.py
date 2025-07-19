from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Literal
from datetime import datetime

class Movie(BaseModel):
    """
    Movie data model representing a single movie
    """
    title: str
    year: str
    type: Literal["movie", "series", "episode"]
    poster: Optional[HttpUrl] = None
    plot: Optional[str] = None
    actors: List[str]
    genre: List[str]
    source: Literal["omdb", "tmdb"]  # Indicates which API provided this result

    @validator('year')
    def validate_year(cls, v):
        try:
            # Check if it's a valid year
            year = int(v)
            current_year = datetime.now().year
            if not (1888 <= year <= current_year + 1):  # 1888 is the year of the first film ever made
                raise ValueError(f"Year must be between 1888 and {current_year + 1}")
        except ValueError as e:
            raise ValueError(f"Invalid year format: {e}")
        return v

    @validator('actors')
    def validate_actors(cls, v):
        if not v:
            raise ValueError("At least one actor must be provided")
        return v

    @validator('genre')
    def validate_genre(cls, v):
        if not v:
            raise ValueError("At least one genre must be provided")
        return v

class MovieResponse(BaseModel):
    """
    Response model for movie search results
    """
    results: List[Movie]
    total: int
    page: int
    limit: int

    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError("Page number must be greater than 0")
        return v

    @validator('limit')
    def validate_limit(cls, v):
        if not 1 <= v <= 50:
            raise ValueError("Limit must be between 1 and 50")
        return v

class ErrorResponse(BaseModel):
    """
    Error response model
    """
    detail: str
    error_code: Optional[str] = None  # For more specific error identification 