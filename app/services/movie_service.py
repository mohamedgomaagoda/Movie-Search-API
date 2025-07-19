from typing import List, Optional, Dict, Any
import aiohttp
from cachetools import TTLCache
from ..config import get_settings
from ..models.movie import Movie, MovieResponse
from fastapi import HTTPException

class MovieService:
    def __init__(self):
        self.settings = get_settings()
        self.cache = TTLCache(maxsize=100, ttl=self.settings.CACHE_TTL)
        self.session = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
        return self.session

    async def search_movies(
        self,
        title: Optional[str] = None,
        actors: Optional[List[str]] = None,
        type: Optional[str] = None,
        genre: Optional[str] = None,
        page: int = 1,
        limit: int = 10,
    ) -> MovieResponse:
        """
        Search for movies across multiple providers and combine results
        """
        # Validate that at least one search parameter is provided
        if not any([title, actors, type, genre]):
            raise HTTPException(
                status_code=400,
                detail="At least one search parameter (title, actors, type, or genre) must be provided"
            )

        cache_key = f"{title}:{','.join(actors or [])}:{type}:{genre}:{page}:{limit}"
        
        # Check cache first
        if cache_key in self.cache:
            return self.cache[cache_key]

        # Gather results from both providers
        results = []
        total = 0

        # Validate API keys
        if not self.settings.OMDB_API_KEY and not self.settings.TMDB_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="No movie API providers are configured"
            )

        session = await self.get_session()

        # Search OMDB
        if self.settings.OMDB_API_KEY:
            try:
                omdb_results = await self._search_omdb(session, title, actors, type, genre, page)
                results.extend(omdb_results)
                total += len(omdb_results)
            except Exception as e:
                print(f"OMDB API error: {str(e)}")
                # Continue with other providers if one fails

        # Search TMDB
        if self.settings.TMDB_API_KEY:
            try:
                tmdb_results = await self._search_tmdb(session, title, actors, type, genre, page)
                results.extend(tmdb_results)
                total += len(tmdb_results)
            except Exception as e:
                print(f"TMDB API error: {str(e)}")
                # Continue with other providers if one fails

        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = results[start_idx:end_idx]

        response = MovieResponse(
            results=paginated_results,
            total=total,
            page=page,
            limit=limit
        )

        # Cache the response
        self.cache[cache_key] = response
        return response

    async def _search_omdb(
        self,
        session: aiohttp.ClientSession,
        title: Optional[str],
        actors: Optional[List[str]],
        type: Optional[str],
        genre: Optional[str],
        page: int,
    ) -> List[Movie]:
        """
        Search movies using the OMDB API
        """
        params = {
            "apikey": self.settings.OMDB_API_KEY,
            "page": page,
        }

        # Add search parameters if provided
        if title:
            params["s"] = title
        if type:
            params["type"] = type

        try:
            async with session.get("http://www.omdbapi.com/", params=params) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("Response") == "False":
                    return []

                movies = []
                for item in data.get("Search", []):
                    try:
                        # Get detailed information for each movie
                        detail_params = {"apikey": self.settings.OMDB_API_KEY, "i": item["imdbID"]}
                        async with session.get("http://www.omdbapi.com/", params=detail_params) as detail_response:
                            detail_response.raise_for_status()
                            detail = await detail_response.json()

                            # Filter by actors and genre if specified
                            if (actors and not any(actor.lower() in detail.get("Actors", "").lower() for actor in actors)) or \
                               (genre and genre.lower() not in detail.get("Genre", "").lower()):
                                continue

                            movies.append(Movie(
                                title=detail["Title"],
                                year=detail["Year"],
                                type=detail["Type"],
                                poster=detail.get("Poster"),
                                plot=detail.get("Plot"),
                                actors=detail.get("Actors", "").split(", "),
                                genre=detail.get("Genre", "").split(", "),
                                source="omdb"
                            ))
                    except Exception as e:
                        print(f"Error fetching OMDB movie details: {str(e)}")
                        continue

                return movies
        except Exception as e:
            print(f"OMDB API error: {str(e)}")
            return []

    async def _search_tmdb(
        self,
        session: aiohttp.ClientSession,
        title: Optional[str],
        actors: Optional[List[str]],
        type: Optional[str],
        genre: Optional[str],
        page: int,
    ) -> List[Movie]:
        """
        Search movies using the TMDB API
        """
        try:
            # First, search for movies
            params = {
                "api_key": self.settings.TMDB_API_KEY,
                "page": page,
            }

            # Add search parameters
            if title:
                params["query"] = title
            
            # If no title but we have actors, search by person first
            elif actors:
                return await self._search_tmdb_by_actors(session, actors, type, genre, page)

            async with session.get("https://api.themoviedb.org/3/search/movie", params=params) as response:
                response.raise_for_status()
                data = await response.json()

                movies = []
                for item in data.get("results", []):
                    try:
                        # Get detailed information including cast
                        detail_params = {
                            "api_key": self.settings.TMDB_API_KEY,
                            "append_to_response": "credits"
                        }
                        async with session.get(f"https://api.themoviedb.org/3/movie/{item['id']}", params=detail_params) as detail_response:
                            detail_response.raise_for_status()
                            detail = await detail_response.json()

                            # Extract actors from credits
                            cast = [actor["name"] for actor in detail.get("credits", {}).get("cast", [])]
                            
                            # Filter by actors and genre if specified
                            if (actors and not any(actor.lower() in name.lower() for actor in actors for name in cast)) or \
                               (genre and not any(g["name"].lower() == genre.lower() for g in detail.get("genres", []))):
                                continue

                            movies.append(Movie(
                                title=detail["title"],
                                year=str(detail.get("release_date", ""))[:4],
                                type="movie",
                                poster=f"https://image.tmdb.org/t/p/w500{detail.get('poster_path')}" if detail.get('poster_path') else None,
                                plot=detail.get("overview"),
                                actors=cast[:5],  # Limit to top 5 actors
                                genre=[g["name"] for g in detail.get("genres", [])],
                                source="tmdb"
                            ))
                    except Exception as e:
                        print(f"Error fetching TMDB movie details: {str(e)}")
                        continue

                return movies
        except Exception as e:
            print(f"TMDB API error: {str(e)}")
            return []

    async def _search_tmdb_by_actors(
        self,
        session: aiohttp.ClientSession,
        actors: List[str],
        type: Optional[str],
        genre: Optional[str],
        page: int,
    ) -> List[Movie]:
        """
        Search movies by actor names in TMDB
        """
        movies = []
        try:
            for actor in actors:
                # Search for the actor
                params = {
                    "api_key": self.settings.TMDB_API_KEY,
                    "query": actor,
                    "page": 1
                }
                async with session.get("https://api.themoviedb.org/3/search/person", params=params) as person_response:
                    person_response.raise_for_status()
                    person_data = await person_response.json()

                    if not person_data.get("results"):
                        continue

                    # Get the first matching person's movies
                    person_id = person_data["results"][0]["id"]
                    credits_params = {"api_key": self.settings.TMDB_API_KEY}
                    async with session.get(f"https://api.themoviedb.org/3/person/{person_id}/movie_credits", params=credits_params) as credits_response:
                        credits_response.raise_for_status()
                        credits_data = await credits_response.json()

                        # Process each movie
                        for movie in credits_data.get("cast", []):
                            try:
                                detail_params = {
                                    "api_key": self.settings.TMDB_API_KEY,
                                    "append_to_response": "credits"
                                }
                                async with session.get(f"https://api.themoviedb.org/3/movie/{movie['id']}", params=detail_params) as detail_response:
                                    detail_response.raise_for_status()
                                    detail = await detail_response.json()

                                    if genre and not any(g["name"].lower() == genre.lower() for g in detail.get("genres", [])):
                                        continue

                                    cast = [actor["name"] for actor in detail.get("credits", {}).get("cast", [])]
                                    
                                    movies.append(Movie(
                                        title=detail["title"],
                                        year=str(detail.get("release_date", ""))[:4],
                                        type="movie",
                                        poster=f"https://image.tmdb.org/t/p/w500{detail.get('poster_path')}" if detail.get('poster_path') else None,
                                        plot=detail.get("overview"),
                                        actors=cast[:5],
                                        genre=[g["name"] for g in detail.get("genres", [])],
                                        source="tmdb"
                                    ))
                            except Exception as e:
                                print(f"Error fetching TMDB movie details: {str(e)}")
                                continue

            return movies
        except Exception as e:
            print(f"TMDB API error: {str(e)}")
            return []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close() 