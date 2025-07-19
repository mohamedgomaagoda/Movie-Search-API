from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, List
from .services.movie_service import MovieService
from .models.movie import MovieResponse, ErrorResponse
from .config import get_settings
from .middleware.rate_limit import rate_limit_middleware
from .middleware.logging import logging_middleware

app = FastAPI(
    title="Movie Search API",
    description="A RESTful API for searching movies across multiple providers",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

# Add middlewares
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(logging_middleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Global exception handler for HTTPException
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.get("/api/v1/movies/search", 
         response_model=MovieResponse, 
         responses={
             400: {"model": ErrorResponse, "description": "Bad Request"},
             429: {"model": ErrorResponse, "description": "Too Many Requests"},
             500: {"model": ErrorResponse, "description": "Internal Server Error"},
         },
         tags=["Movies"])
async def search_movies(
    title: Optional[str] = Query(None, description="Movie title to search for"),
    actors: Optional[str] = Query(None, description="Comma-separated list of actor names"),
    type: Optional[str] = Query(None, description="Type of media (movie, series, episode)"),
    genre: Optional[str] = Query(None, description="Movie genre"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=50, description="Results per page"),
    movie_service: MovieService = Depends(MovieService),
):
    """
    Search for movies across multiple providers with various filters.
    
    - **title**: Optional movie title to search for
    - **actors**: Optional comma-separated list of actor names
    - **type**: Optional media type (movie, series, episode)
    - **genre**: Optional movie genre
    - **page**: Page number (starts from 1)
    - **limit**: Number of results per page (1-50)
    
    Returns paginated results combining data from all configured providers.
    At least one search parameter (title, actors, type, or genre) must be provided.
    """
    try:
        # Convert comma-separated actors string to list if provided
        actor_list = [actor.strip() for actor in actors.split(",")] if actors else None
        
        # Validate type parameter
        if type and type.lower() not in ["movie", "series", "episode"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid type parameter. Must be one of: movie, series, episode"
            )
        
        results = await movie_service.search_movies(
            title=title,
            actors=actor_list,
            type=type.lower() if type else None,
            genre=genre,
            page=page,
            limit=limit
        )
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.get("/api/v1/health",
         tags=["System"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    Returns a simple status message.
    """
    try:
        settings = get_settings()
        status = {
            "status": "healthy",
            "providers": {
                "omdb": bool(settings.OMDB_API_KEY),
                "tmdb": bool(settings.TMDB_API_KEY)
            }
        }
        return status
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Health check failed"
        ) 