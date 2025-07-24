"""Tests for validation functions."""

from datetime import UTC, datetime, timedelta

from wish_models.validation import (
    ModelValidator,
    validate_cidr,
    validate_confidence_score,
    validate_cve_id,
    validate_datetime_not_future,
    validate_domain,
    validate_ip_address,
    validate_mac_address,
    validate_port,
    validate_scope_type_and_value,
    validate_url,
)


class TestValidationFunctions:
    """Test individual validation functions."""

    def test_validate_ip_address_valid_ipv4(self):
        """Test valid IPv4 address validation."""
        result = validate_ip_address("192.168.1.1")
        assert result.is_valid
        assert result.data == "192.168.1.1"

    def test_validate_ip_address_valid_ipv6(self):
        """Test valid IPv6 address validation."""
        result = validate_ip_address("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert result.is_valid

    def test_validate_ip_address_invalid(self):
        """Test invalid IP address validation."""
        result = validate_ip_address("invalid-ip")
        assert not result.is_valid
        assert "Invalid IP address format" in result.errors[0]

    def test_validate_cidr_valid(self):
        """Test valid CIDR validation."""
        result = validate_cidr("192.168.1.0/24")
        assert result.is_valid
        assert result.data == "192.168.1.0/24"

    def test_validate_cidr_invalid(self):
        """Test invalid CIDR validation."""
        result = validate_cidr("invalid-cidr")
        assert not result.is_valid
        assert "Invalid CIDR format" in result.errors[0]

    def test_validate_port_valid(self):
        """Test valid port validation."""
        result = validate_port(80)
        assert result.is_valid
        assert result.data == 80

    def test_validate_port_boundary_values(self):
        """Test port boundary values."""
        # Test minimum valid port
        result_min = validate_port(1)
        assert result_min.is_valid

        # Test maximum valid port
        result_max = validate_port(65535)
        assert result_max.is_valid

    def test_validate_port_invalid_low(self):
        """Test invalid port (too low)."""
        result = validate_port(0)
        assert not result.is_valid
        assert "out of valid range" in result.errors[0]

    def test_validate_port_invalid_high(self):
        """Test invalid port (too high)."""
        result = validate_port(65536)
        assert not result.is_valid
        assert "out of valid range" in result.errors[0]

    def test_validate_port_invalid_type(self):
        """Test invalid port type."""
        result = validate_port("80")  # String instead of int
        assert not result.is_valid
        assert "must be an integer" in result.errors[0]

    def test_validate_datetime_not_future_valid(self):
        """Test valid datetime (not future)."""
        past_date = datetime.now(UTC) - timedelta(hours=1)
        result = validate_datetime_not_future(past_date)
        assert result.is_valid

    def test_validate_datetime_not_future_invalid(self):
        """Test invalid datetime (future)."""
        future_date = datetime.now(UTC) + timedelta(hours=1)
        result = validate_datetime_not_future(future_date)
        assert not result.is_valid
        assert "cannot be in the future" in result.errors[0]

    def test_validate_mac_address_valid_colon(self):
        """Test valid MAC address with colons."""
        result = validate_mac_address("00:11:22:33:44:55")
        assert result.is_valid
        assert result.data == "00:11:22:33:44:55"

    def test_validate_mac_address_valid_dash(self):
        """Test valid MAC address with dashes."""
        result = validate_mac_address("00-11-22-33-44-55")
        assert result.is_valid

    def test_validate_mac_address_none(self):
        """Test MAC address validation with None."""
        result = validate_mac_address(None)
        assert result.is_valid
        assert result.data is None

    def test_validate_mac_address_invalid(self):
        """Test invalid MAC address."""
        result = validate_mac_address("invalid-mac")
        assert not result.is_valid
        assert "Invalid MAC address format" in result.errors[0]

    def test_validate_cve_id_valid(self):
        """Test valid CVE ID."""
        result = validate_cve_id("CVE-2021-1234")
        assert result.is_valid
        assert result.data == "CVE-2021-1234"

    def test_validate_cve_id_valid_long(self):
        """Test valid CVE ID with long number."""
        result = validate_cve_id("CVE-2021-123456")
        assert result.is_valid

    def test_validate_cve_id_invalid_format(self):
        """Test invalid CVE ID format."""
        result = validate_cve_id("invalid-cve")
        assert not result.is_valid
        assert "Invalid CVE ID format" in result.errors[0]

    def test_validate_url_valid_http(self):
        """Test valid HTTP URL."""
        result = validate_url("http://example.com")
        assert result.is_valid

    def test_validate_url_valid_https(self):
        """Test valid HTTPS URL."""
        result = validate_url("https://example.com/path?param=value")
        assert result.is_valid

    def test_validate_url_invalid(self):
        """Test invalid URL."""
        result = validate_url("invalid-url")
        assert not result.is_valid
        assert "Invalid URL format" in result.errors[0]

    def test_validate_domain_valid(self):
        """Test valid domain."""
        result = validate_domain("example.com")
        assert result.is_valid
        assert result.data == "example.com"

    def test_validate_domain_valid_subdomain(self):
        """Test valid subdomain."""
        result = validate_domain("sub.example.com")
        assert result.is_valid

    def test_validate_domain_invalid(self):
        """Test invalid domain."""
        result = validate_domain("invalid..domain")
        assert not result.is_valid
        assert "Invalid domain format" in result.errors[0]

    def test_validate_confidence_score_valid(self):
        """Test valid confidence score."""
        result = validate_confidence_score(0.85)
        assert result.is_valid
        assert result.data == 0.85

    def test_validate_confidence_score_none(self):
        """Test confidence score validation with None."""
        result = validate_confidence_score(None)
        assert result.is_valid
        assert result.data is None

    def test_validate_confidence_score_boundary(self):
        """Test confidence score boundary values."""
        result_zero = validate_confidence_score(0.0)
        assert result_zero.is_valid

        result_one = validate_confidence_score(1.0)
        assert result_one.is_valid

    def test_validate_confidence_score_invalid_low(self):
        """Test invalid confidence score (too low)."""
        result = validate_confidence_score(-0.1)
        assert not result.is_valid
        assert "must be between 0.0 and 1.0" in result.errors[0]

    def test_validate_confidence_score_invalid_high(self):
        """Test invalid confidence score (too high)."""
        result = validate_confidence_score(1.1)
        assert not result.is_valid
        assert "must be between 0.0 and 1.0" in result.errors[0]

    def test_validate_confidence_score_invalid_type(self):
        """Test invalid confidence score type."""
        result = validate_confidence_score("0.85")
        assert not result.is_valid
        assert "must be a number" in result.errors[0]


class TestScopeValidation:
    """Test scope type and value validation."""

    def test_validate_scope_ip_valid(self):
        """Test valid IP scope."""
        result = validate_scope_type_and_value("ip", "192.168.1.1")
        assert result.is_valid
        assert result.data == ("ip", "192.168.1.1")

    def test_validate_scope_cidr_valid(self):
        """Test valid CIDR scope."""
        result = validate_scope_type_and_value("cidr", "10.0.0.0/8")
        assert result.is_valid

    def test_validate_scope_domain_valid(self):
        """Test valid domain scope."""
        result = validate_scope_type_and_value("domain", "example.com")
        assert result.is_valid

    def test_validate_scope_url_valid(self):
        """Test valid URL scope."""
        result = validate_scope_type_and_value("url", "https://example.com")
        assert result.is_valid

    def test_validate_scope_invalid_type(self):
        """Test invalid scope type."""
        result = validate_scope_type_and_value("invalid_type", "value")
        assert not result.is_valid
        assert "Invalid scope_type" in result.errors[0]

    def test_validate_scope_ip_invalid_value(self):
        """Test IP scope with invalid value."""
        result = validate_scope_type_and_value("ip", "invalid-ip")
        assert not result.is_valid
        assert "Invalid IP address format" in result.errors[0]

    def test_validate_scope_domain_invalid_value(self):
        """Test domain scope with invalid value."""
        result = validate_scope_type_and_value("domain", "invalid..domain")
        assert not result.is_valid
        assert "Invalid domain format" in result.errors[0]


class TestModelValidator:
    """Test ModelValidator class methods."""

    def test_validate_service_host_relationship_valid(self):
        """Test valid service-host relationship."""
        host_ids = ["host1", "host2", "host3"]
        result = ModelValidator.validate_service_host_relationship("host2", host_ids)
        assert result.is_valid
        assert result.data == "host2"

    def test_validate_service_host_relationship_invalid(self):
        """Test invalid service-host relationship."""
        host_ids = ["host1", "host2", "host3"]
        result = ModelValidator.validate_service_host_relationship("host4", host_ids)
        assert not result.is_valid
        assert "non-existent host_id" in result.errors[0]

    def test_validate_finding_references_valid(self):
        """Test valid finding references."""
        host_ids = ["host1", "host2"]
        service_ids = ["service1", "service2"]

        result = ModelValidator.validate_finding_references("host1", "service2", host_ids, service_ids)
        assert result.is_valid
        assert result.data == ("host1", "service2")

    def test_validate_finding_references_none_values(self):
        """Test finding references with None values."""
        host_ids = ["host1"]
        service_ids = ["service1"]

        result = ModelValidator.validate_finding_references(None, None, host_ids, service_ids)
        assert result.is_valid
        assert result.data == (None, None)

    def test_validate_finding_references_invalid_host(self):
        """Test finding references with invalid host."""
        host_ids = ["host1", "host2"]
        service_ids = ["service1", "service2"]

        result = ModelValidator.validate_finding_references("host3", "service1", host_ids, service_ids)
        assert not result.is_valid
        assert "non-existent host_id" in result.errors[0]

    def test_validate_finding_references_invalid_service(self):
        """Test finding references with invalid service."""
        host_ids = ["host1", "host2"]
        service_ids = ["service1", "service2"]

        result = ModelValidator.validate_finding_references("host1", "service3", host_ids, service_ids)
        assert not result.is_valid
        assert "non-existent service_id" in result.errors[0]

    def test_validate_collected_data_references_valid(self):
        """Test valid collected data references."""
        host_ids = ["host1"]
        service_ids = ["service1"]
        finding_ids = ["finding1"]

        result = ModelValidator.validate_collected_data_references(
            "host1", "service1", "finding1", host_ids, service_ids, finding_ids
        )
        assert result.is_valid
        assert result.data == ("host1", "service1", "finding1")

    def test_validate_collected_data_references_partial_none(self):
        """Test collected data references with some None values."""
        host_ids = ["host1"]
        service_ids = ["service1"]
        finding_ids = ["finding1"]

        result = ModelValidator.validate_collected_data_references(
            "host1", None, "finding1", host_ids, service_ids, finding_ids
        )
        assert result.is_valid
        assert result.data == ("host1", None, "finding1")

    def test_validate_collected_data_references_invalid_finding(self):
        """Test collected data references with invalid finding."""
        host_ids = ["host1"]
        service_ids = ["service1"]
        finding_ids = ["finding1"]

        result = ModelValidator.validate_collected_data_references(
            "host1", "service1", "finding2", host_ids, service_ids, finding_ids
        )
        assert not result.is_valid
        assert "non-existent source_finding_id" in result.errors[0]

    def test_validate_collected_data_references_multiple_errors(self):
        """Test collected data references with multiple errors."""
        host_ids = ["host1"]
        service_ids = ["service1"]
        finding_ids = ["finding1"]

        result = ModelValidator.validate_collected_data_references(
            "host2", "service2", "finding2", host_ids, service_ids, finding_ids
        )
        assert not result.is_valid
        assert len(result.errors) == 3  # All three references are invalid
