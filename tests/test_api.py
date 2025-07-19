from fastapi.testclient import TestClient
from app.main import app
import pytest
from unittest.mock import patch

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "providers" in data

def test_search_movies_no_params():
    response = client.get("/api/v1/movies/search")
    assert response.status_code == 400
    assert "detail" in response.json()

def test_search_movies_with_title():
    response = client.get("/api/v1/movies/search?title=Matrix")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert "total" in data
    assert "page" in data
    assert "limit" in data

def test_search_movies_invalid_type():
    response = client.get("/api/v1/movies/search?title=Matrix&type=invalid")
    assert response.status_code == 400
    assert "detail" in response.json()

def test_search_movies_with_actors():
    response = client.get("/api/v1/movies/search?actors=Tom%20Hanks")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_search_movies_with_genre():
    response = client.get("/api/v1/movies/search?genre=Action")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data

def test_pagination_limits():
    response = client.get("/api/v1/movies/search?title=Matrix&limit=51")
    assert response.status_code == 400
    assert "detail" in response.json()

    response = client.get("/api/v1/movies/search?title=Matrix&page=0")
    assert response.status_code == 400
    assert "detail" in response.json() 