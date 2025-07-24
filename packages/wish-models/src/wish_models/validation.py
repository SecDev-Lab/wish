"""
Validation utilities and error handling for wish-models.
"""

import ipaddress
import re
from datetime import UTC, datetime
from typing import Generic, TypeVar

T = TypeVar("T")


class ValidationError(Exception):
    """Validation error with detailed error information."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


class ValidationResult(Generic[T]):
    """Container for validation results with data and errors."""

    def __init__(self, data: T | None = None, errors: list[str] | None = None) -> None:
        self.data = data
        self.errors = errors or []
        self.is_valid = len(self.errors) == 0

    def add_error(self, error: str) -> None:
        """Add an error to the result."""
        self.errors.append(error)
        self.is_valid = False

    def raise_if_invalid(self) -> T:
        """Raise ValidationError if result is invalid, otherwise return data."""
        if not self.is_valid:
            raise ValidationError(self.errors)
        return self.data  # type: ignore

    @classmethod
    def success(cls, data: T) -> "ValidationResult[T]":
        """Create a successful validation result."""
        return cls(data=data)

    @classmethod
    def error(cls, errors: list[str]) -> "ValidationResult[T]":
        """Create a failed validation result."""
        return cls(errors=errors)


def validate_ip_address(ip_str: str) -> ValidationResult[str]:
    """Validate IP address (IPv4/IPv6)"""
    try:
        ipaddress.ip_address(ip_str)
        return ValidationResult.success(ip_str)
    except ValueError:
        return ValidationResult.error([f"Invalid IP address format: {ip_str}"])


def validate_cidr(cidr_str: str) -> ValidationResult[str]:
    """Validate CIDR notation"""
    try:
        ipaddress.ip_network(cidr_str, strict=False)
        return ValidationResult.success(cidr_str)
    except ValueError:
        return ValidationResult.error([f"Invalid CIDR format: {cidr_str}"])


def validate_port(port: int) -> ValidationResult[int]:
    """Validate port number range (1-65535)"""
    if not isinstance(port, int):  # type: ignore[unreachable]
        return ValidationResult.error(["Port must be an integer"])

    if port < 1 or port > 65535:
        return ValidationResult.error([f"Port {port} is out of valid range (1-65535)"])

    return ValidationResult.success(port)


def validate_datetime_not_future(dt: datetime) -> ValidationResult[datetime]:
    """Validate that datetime is not in the future"""
    now = datetime.now(UTC)
    if dt > now:
        return ValidationResult.error([f"DateTime {dt.isoformat()} cannot be in the future"])

    return ValidationResult.success(dt)


def validate_mac_address(mac_str: str | None) -> ValidationResult[str | None]:
    """Validate MAC address format"""
    if mac_str is None:
        return ValidationResult.success(None)

    # Common MAC address formats (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
    mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
    if re.match(mac_pattern, mac_str):
        return ValidationResult.success(mac_str)

    return ValidationResult.error([f"Invalid MAC address format: {mac_str}"])


def validate_cve_id(cve_id: str) -> ValidationResult[str]:
    """Validate CVE ID format (CVE-YYYY-NNNN)"""
    cve_pattern = r"^CVE-\d{4}-\d{4,}$"
    if re.match(cve_pattern, cve_id):
        return ValidationResult.success(cve_id)

    return ValidationResult.error([f"Invalid CVE ID format: {cve_id}. Expected format: CVE-YYYY-NNNN"])


def validate_url(url: str) -> ValidationResult[str]:
    """Basic URL format validation"""
    url_pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    if re.match(url_pattern, url, re.IGNORECASE):
        return ValidationResult.success(url)

    return ValidationResult.error([f"Invalid URL format: {url}"])


def validate_domain(domain: str) -> ValidationResult[str]:
    """Basic domain name validation"""
    # Basic domain name validation based on RFC 1035
    domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    if re.match(domain_pattern, domain):
        return ValidationResult.success(domain)

    return ValidationResult.error([f"Invalid domain format: {domain}"])


def validate_confidence_score(score: float | None) -> ValidationResult[float | None]:
    """Validate confidence score (0-1)"""
    if score is None:
        return ValidationResult.success(None)

    if not isinstance(score, int | float):  # type: ignore[unreachable]
        return ValidationResult.error(["Confidence score must be a number"])

    if score < 0.0 or score > 1.0:
        return ValidationResult.error([f"Confidence score {score} must be between 0.0 and 1.0"])

    return ValidationResult.success(float(score))


def validate_scope_type_and_value(scope_type: str, scope_value: str) -> ValidationResult[tuple[str, str]]:
    """Validate scope type and value combination"""
    errors = []

    if scope_type == "ip":
        ip_result = validate_ip_address(scope_value)
        if not ip_result.is_valid:
            errors.extend(ip_result.errors)
    elif scope_type == "cidr":
        cidr_result = validate_cidr(scope_value)
        if not cidr_result.is_valid:
            errors.extend(cidr_result.errors)
    elif scope_type == "domain":
        domain_result = validate_domain(scope_value)
        if not domain_result.is_valid:
            errors.extend(domain_result.errors)
    elif scope_type == "url":
        url_result = validate_url(scope_value)
        if not url_result.is_valid:
            errors.extend(url_result.errors)
    else:
        errors.append(f"Invalid scope_type: {scope_type}. Must be one of: ip, cidr, domain, url")

    if errors:
        return ValidationResult.error(errors)

    return ValidationResult.success((scope_type, scope_value))


class ModelValidator:
    """Class for validating relationships between models"""

    @staticmethod
    def validate_service_host_relationship(
        service_host_id: str, available_host_ids: list[str]
    ) -> ValidationResult[str]:
        """Validate that service host_id references a valid host ID"""
        if service_host_id not in available_host_ids:
            return ValidationResult.error(
                [
                    f"Service references non-existent host_id: {service_host_id}. "
                    f"Available host_ids: {available_host_ids}"
                ]
            )

        return ValidationResult.success(service_host_id)

    @staticmethod
    def validate_finding_references(
        finding_host_id: str | None,
        finding_service_id: str | None,
        available_host_ids: list[str],
        available_service_ids: list[str],
    ) -> ValidationResult[tuple[str | None, str | None]]:
        """Validate finding references"""
        errors = []

        if finding_host_id is not None and finding_host_id not in available_host_ids:
            errors.append(f"Finding references non-existent host_id: {finding_host_id}")

        if finding_service_id is not None and finding_service_id not in available_service_ids:
            errors.append(f"Finding references non-existent service_id: {finding_service_id}")

        if errors:
            return ValidationResult.error(errors)

        return ValidationResult.success((finding_host_id, finding_service_id))

    @staticmethod
    def validate_collected_data_references(
        data_source_host_id: str | None,
        data_source_service_id: str | None,
        data_source_finding_id: str | None,
        available_host_ids: list[str],
        available_service_ids: list[str],
        available_finding_ids: list[str],
    ) -> ValidationResult[tuple[str | None, str | None, str | None]]:
        """Validate collected data references"""
        errors = []

        if data_source_host_id is not None and data_source_host_id not in available_host_ids:
            errors.append(f"CollectedData references non-existent source_host_id: {data_source_host_id}")

        if data_source_service_id is not None and data_source_service_id not in available_service_ids:
            errors.append(f"CollectedData references non-existent source_service_id: {data_source_service_id}")

        if data_source_finding_id is not None and data_source_finding_id not in available_finding_ids:
            errors.append(f"CollectedData references non-existent source_finding_id: {data_source_finding_id}")

        if errors:
            return ValidationResult.error(errors)

        return ValidationResult.success((data_source_host_id, data_source_service_id, data_source_finding_id))
