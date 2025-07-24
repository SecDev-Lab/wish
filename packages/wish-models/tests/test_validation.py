"""Tests for validation utilities."""

import pytest

from wish_models.validation import ValidationError, ValidationResult


class TestValidationResult:
    """Test ValidationResult class."""

    def test_success_result(self):
        """Test successful validation result."""
        result = ValidationResult.success("test_data")

        assert result.is_valid
        assert result.data == "test_data"
        assert result.errors == []

    def test_error_result(self):
        """Test error validation result."""
        errors = ["Error 1", "Error 2"]
        result = ValidationResult.error(errors)

        assert not result.is_valid
        assert result.data is None
        assert result.errors == errors

    def test_add_error(self):
        """Test adding error to result."""
        result = ValidationResult.success("data")
        assert result.is_valid

        result.add_error("New error")
        assert not result.is_valid
        assert "New error" in result.errors

    def test_raise_if_invalid_success(self):
        """Test raise_if_invalid with valid result."""
        result = ValidationResult.success("test_data")
        data = result.raise_if_invalid()
        assert data == "test_data"

    def test_raise_if_invalid_error(self):
        """Test raise_if_invalid with invalid result."""
        result = ValidationResult.error(["Error"])

        with pytest.raises(ValidationError) as exc_info:
            result.raise_if_invalid()

        assert "Error" in str(exc_info.value)


class TestValidationError:
    """Test ValidationError class."""

    def test_validation_error_creation(self):
        """Test ValidationError creation."""
        errors = ["Error 1", "Error 2"]
        error = ValidationError(errors)

        assert error.errors == errors
        assert "Error 1; Error 2" in str(error)
