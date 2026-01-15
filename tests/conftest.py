"""
Pytest configuration and fixtures for Microsoft Entra ID Emulator tests.
"""
import pytest
import os
from typing import Generator
import httpx


@pytest.fixture(scope="session")
def emulator_url() -> str:
    """Get emulator URL from environment variable."""
    return os.getenv("EMULATOR_URL", "http://localhost:8029")


@pytest.fixture(scope="session")
def client(emulator_url: str) -> Generator[httpx.Client, None, None]:
    """Create HTTP client for testing."""
    with httpx.Client(base_url=emulator_url, timeout=10.0) as client:
        yield client


@pytest.fixture
def test_user() -> dict:
    """Test user credentials."""
    return {
        "username": "test@contoso.onmicrosoft.com",
        "password": "Test123!"
    }


@pytest.fixture
def test_app() -> dict:
    """Test application credentials."""
    return {
        "client_id": "test-app-123",
        "client_secret": "test-secret",
        "redirect_uri": "http://localhost:3029/callback"
    }


@pytest.fixture
def service_app() -> dict:
    """Service application credentials."""
    return {
        "client_id": "service-app-456",
        "client_secret": "service-secret"
    }
