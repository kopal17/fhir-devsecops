"""
Security-focused tests for the FHIR Patient API.
These tests validate security controls — not just functionality.
Run by GitHub Actions on every pull request.
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src/api"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))

from api.main import app

client = TestClient(app, raise_server_exceptions=False)

VALID_TOKEN = "Bearer demo-token-valid"
NO_TOKEN = None


class TestAuthentication:
    """Verify all PHI endpoints reject unauthenticated requests."""

    def test_get_patient_no_token_returns_401(self):
        response = client.get("/fhir/r4/Patient/patient-001")
        assert response.status_code == 401

    def test_get_patient_invalid_token_format_returns_401(self):
        response = client.get(
            "/fhir/r4/Patient/patient-001",
            headers={"Authorization": "Basic abc123"}
        )
        assert response.status_code == 401

    def test_search_no_token_returns_401(self):
        response = client.get("/fhir/r4/Patient?family=Doe")
        assert response.status_code == 401

    def test_health_check_requires_no_auth(self):
        """Health probe must never require auth — needed for load balancers."""
        response = client.get("/health")
        assert response.status_code == 200


class TestInputValidation:
    """Validate inputs are sanitised to prevent injection attacks."""

    def test_sql_injection_in_patient_id_returns_400(self):
        response = client.get(
            "/fhir/r4/Patient/'; DROP TABLE patients; --",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code == 400

    def test_path_traversal_in_patient_id_returns_400(self):
        response = client.get(
            "/fhir/r4/Patient/../../etc/passwd",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code in [400, 404]

    def test_oversized_patient_id_returns_400(self):
        long_id = "a" * 100
        response = client.get(
            f"/fhir/r4/Patient/{long_id}",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code == 400

    def test_xss_in_patient_id_returns_400(self):
        response = client.get(
            "/fhir/r4/Patient/<script>alert(1)</script>",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code in [400, 404]


class TestSearchProtection:
    """Prevent unrestricted data dumps via search endpoint."""

    def test_search_without_params_returns_400(self):
        """Searching with no parameters would expose all patients — must be blocked."""
        response = client.get(
            "/fhir/r4/Patient",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code == 400

    def test_search_with_family_param_succeeds(self):
        response = client.get(
            "/fhir/r4/Patient?family=Doe",
            headers={"Authorization": VALID_TOKEN}
        )
        assert response.status_code == 200


class TestResponseSafety:
    """Verify responses don't leak sensitive information."""

    def test_error_response_contains_no_phi(self):
        response = client.get(
            "/fhir/r4/Patient/'; DROP TABLE--",
            headers={"Authorization": VALID_TOKEN}
        )
        response_text = response.text.lower()
        # Error messages must not echo back the malicious input
        assert "drop table" not in response_text
        assert "passwd" not in response_text

    def test_health_check_contains_no_phi(self):
        response = client.get("/health")
        assert "patient" not in response.text.lower()
        assert "name" not in response.text.lower()
