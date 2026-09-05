"""
Tests for the FastAPI application configuration and routes.
Tests health endpoints, CORS configuration, and route registration.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test suite for health and root endpoints."""

    def test_health_check(self, client):
        """Health endpoint should return status ok."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "MedLens API"

    def test_root_endpoint(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "MedLens" in data["message"]
        assert data["docs"] == "/docs"

    def test_docs_endpoint(self, client):
        """Swagger docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint(self, client):
        """ReDoc should be accessible."""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestCORS:
    """Test suite for CORS configuration."""

    def test_cors_preflight(self, client):
        """CORS preflight requests should be handled correctly."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200

    def test_cors_vercel_origin(self, client):
        """Vercel origins should be allowed by CORS regex."""
        response = client.options(
            "/health",
            headers={
                "Origin": "https://med-lens.vercel.app",
                "Access-Control-Request-Method": "GET",
            },
        )
        assert response.status_code == 200


class TestRouteRegistration:
    """Test suite to verify all API routes are registered."""

    def test_patients_route_exists(self, client):
        """Patients routes should be registered (returns 401 without auth, not 404)."""
        response = client.get("/api/patients")
        # 401/403 means route exists but requires auth; 404 would mean missing
        assert response.status_code != 404

    def test_unknown_route_returns_404(self, client):
        """Unknown routes should return 404 or be handled."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404


class TestErrorHandling:
    """Test suite for global error handling."""

    def test_method_not_allowed(self, client):
        """Using wrong HTTP method should return 405."""
        response = client.patch("/health")
        assert response.status_code == 405

    def test_json_error_response_format(self, client):
        """Error responses should have consistent JSON format."""
        response = client.get("/api/patients")
        if response.status_code >= 400:
            data = response.json()
            assert isinstance(data, dict)
