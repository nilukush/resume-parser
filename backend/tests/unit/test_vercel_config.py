"""
Unit tests for Vercel deployment configuration.

These tests validate that vercel.json exists and contains
required fields for modern Vercel serverless function deployment.

Updated 2026-02-22: Tests now validate modern Vercel configuration
without deprecated legacy builds array.
"""

import pytest
from pathlib import Path
import json


class TestVercelConfig:
    """Test Vercel deployment configuration."""

    def test_vercel_json_exists(self):
        """Test that vercel.json configuration file exists."""
        vercel_json = Path(__file__).parent.parent.parent / "vercel.json"
        assert vercel_json.exists(), "vercel.json must exist for Vercel deployment"

    def test_vercel_json_has_schema_validation(self):
        """Test that vercel.json includes schema for IDE support."""
        vercel_json = Path(__file__).parent.parent.parent / "vercel.json"

        with open(vercel_json) as f:
            config = json.load(f)

        # Modern Vercel configs should have $schema for validation
        assert "$schema" in config, "vercel.json should include $schema for validation"
        assert "openapi.vercel.sh" in config["$schema"]

    def test_vercel_json_has_build_command(self):
        """Test that Vercel config has proper build command."""
        vercel_json = Path(__file__).parent.parent.parent / "vercel.json"

        with open(vercel_json) as f:
            config = json.load(f)

        # Should have buildCommand for Python dependencies
        assert "buildCommand" in config
        assert "pip install" in config["buildCommand"]
        assert "requirements.txt" in config["buildCommand"]

    def test_vercel_json_uses_pip_user(self):
        """Test that pip install uses --user flag for PEP 668 compliance."""
        vercel_json = Path(__file__).parent.parent.parent / "vercel.json"

        with open(vercel_json) as f:
            config = json.load(f)

        # Vercel Python runtime requires --user flag
        assert "--user" in config.get("buildCommand", "")
        assert "--user" in config.get("installCommand", "")

    def test_vercel_json_no_deprecated_properties(self):
        """Test that vercel.json does NOT contain deprecated properties."""
        vercel_json = Path(__file__).parent.parent.parent / "vercel.json"

        with open(vercel_json) as f:
            config = json.load(f)

        # These properties are deprecated and should not exist
        deprecated_props = ["builds", "routes", "maxLambdaSize", "version"]
        for prop in deprecated_props:
            if prop in ["builds", "routes", "maxLambdaSize"]:
                # These should definitely NOT exist
                assert prop not in config, f"vercel.json should not contain deprecated '{prop}' property"

    def test_api_handler_exists(self):
        """Test that api/index.py handler exists for Vercel serverless."""
        api_index = Path(__file__).parent.parent.parent / "api" / "index.py"
        assert api_index.exists(), "api/index.py must exist as Vercel serverless entry point"

    def test_api_handler_uses_mangum(self):
        """Test that api/index.py uses Mangum adapter for FastAPI."""
        api_index = Path(__file__).parent.parent.parent / "api" / "index.py"

        with open(api_index) as f:
            content = f.read()

        # Should import Mangum
        assert "mangum" in content.lower()
        # Should import FastAPI app
        assert "from app.main import app" in content
        # Should export handler
        assert "handler" in content
