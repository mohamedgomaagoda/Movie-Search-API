# Movie Search API

A RESTful API built with FastAPI that enables users to search for movies by various criteria, integrating data from multiple external movie data providers.

## Features

- Search movies by title, actors, type, and genre
- Integration with multiple movie data providers (OMDB and TMDB)
- Comprehensive error handling
- Request validation using Pydantic
- Response caching for improved performance

## Prerequisites

- Python 3.8+
- API keys for:
  - OMDB API (Get it [here](http://www.omdbapi.com/apikey.aspx))
  - TMDB API (Get it [here](https://www.themoviedb.org/settings/api))

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd movie-search-api
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root and add your API keys:
```env
OMDB_API_KEY=your_omdb_api_key
TMDB_API_KEY=your_tmdb_api_key
```

## Running the Application

Start the server with:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation: `http://localhost:8000/docs`
- Alternative documentation: `http://localhost:8000/redoc`

### Endpoints

#### GET /api/v1/movies/search

Search for movies across multiple providers.

Query Parameters:
- `title` (optional): Movie title to search for
- `actors` (optional): Actor names (comma-separated)
- `type` (optional): Type of media (movie, series, episode)
- `genre` (optional): Movie genre
- `page` (optional): Page number for pagination (default: 1)
- `limit` (optional): Results per page (default: 10)

Example Response:
```json
{
  "results": [
    {
      "title": "The Matrix",
      "year": "1999",
      "type": "movie",
      "poster": "https://...",
      "plot": "...",
      "actors": ["Keanu Reeves", "Laurence Fishburne"],
      "genre": ["Action", "Sci-Fi"],
      "source": "omdb"
    }
  ],
  "total": 1,
  "page": 1,
  "limit": 10
}
```

## Design Decisions

1. **Multiple Provider Integration**: The API aggregates results from both OMDB and TMDB to provide comprehensive search results.
2. **Caching**: Implements response caching to reduce external API calls and improve response times.
3. **Modular Architecture**: Uses dependency injection and service layer pattern for better maintainability and testability.
4. **Error Handling**: Comprehensive error handling with proper HTTP status codes and meaningful error messages.

## Known Limitations

1. Rate limiting depends on the external API providers
2. Search results might contain duplicates from different providers
3. Limited to the data available from the integrated providers

## Possible Improvements

1. Implement more sophisticated deduplication of results
2. Add more external providers
3. Implement rate limiting
4. Add authentication and user-specific features
5. Add comprehensive test suite
6. Implement more advanced caching strategies

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 