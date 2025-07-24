# wish-models Implementation Specification

## Overview

The wish-models package provides the core data models for the wish penetration testing support system. Using type-safe model definitions with Pydantic v2, it enables state management and relationship tracking throughout the engagement.

## Implemented Models

### 1. EngagementState
The central model that manages the overall engagement state.

**Key Features:**
- Integrated management of targets, hosts, findings, and collected data
- Integration with session information
- Automatic calculation of statistics and active resources

**Helper Methods:**
- `get_active_hosts()`: Get list of hosts with "up" status
- `get_open_services()`: Get list of services on open ports
- `get_sensitive_collected_data()`: Retrieve high-sensitivity data
- `get_working_credentials()`: Get valid credentials

### 2. Target
Definition and scope management of penetration test targets.

**Validation Features:**
- Format validation for IP, CIDR, domain, and URL
- Consistency check between scope type and value
- Future datetime constraint validation

### 3. Host
Management of detailed information for discovered hosts.

**Key Features:**
- Automatic service information integration (deduplication)
- Duplicate prevention management for hostnames and tags
- Automatic update of last seen timestamp

**Validation:**
- IP address format validation
- MAC address format validation
- OS confidence score (0-1) validation

### 4. Service
Detailed information about services running on hosts.

**Key Features:**
- Management of port, protocol, and state
- Retention of banner and SSL/TLS information
- Service-specific confidence management

**Validation:**
- Port number range (1-65535) validation
- Confidence score (0-1) validation

### 5. Finding
Detailed management of vulnerabilities and discoveries.

**Key Features:**
- Classification by category and severity
- CVE ID format validation and duplicate prevention
- Bidirectional relationship management with collected data

**State Management:**
- `mark_verified()`: Mark as verified
- `mark_false_positive()`: Mark as false positive
- `is_critical()`: Critical determination

### 6. CollectedData
Management of important data such as credentials and files.

**Key Features:**
- Security management with sensitivity flags
- Validity check functionality
- Cross-reference with findings

**Relationship Management:**
- `source_finding_id`: Source of data discovery
- `derived_finding_ids`: Findings derived from data

### 7. SessionMetadata
Lightweight session information management.

**Key Features:**
- Command history (automatic retention of latest 100)
- Mode change history tracking
- Automatic calculation of statistics

## Validation Features

### validation.py Module
Provides comprehensive validation functions:

- `validate_ip_address()`: IPv4/IPv6 address validation
- `validate_cidr()`: CIDR notation validation
- `validate_port()`: Port number range validation
- `validate_mac_address()`: MAC address format validation
- `validate_cve_id()`: CVE ID format validation
- `validate_url()`: URL format validation
- `validate_domain()`: Domain name validation
- `validate_confidence_score()`: Confidence score validation
- `validate_datetime_not_future()`: Future datetime constraint validation

### ModelValidator Class
Validates relationship consistency between models:

- `validate_service_host_relationship()`: Service-host relationship validation
- `validate_finding_references()`: Finding reference validation
- `validate_collected_data_references()`: Collected data reference validation

## Technical Specifications

### Type Safety
- **Pydantic v2**: Utilization of latest validation features
- **Literal types**: Type-safe definition of limited values
- **Forward Reference**: Proper resolution of circular references
- **100% type hints**: Type annotations on all methods and fields

### Error Handling
- **Fail-Fast principle**: Immediate exceptions for programming errors
- **ValidationError**: Exception class with detailed error information
- **ValidationResult**: Integrated management of results and errors

### Performance Optimization
- **Lightweight design**: Retain only minimal necessary information
- **Lazy evaluation**: Execute calculations only when needed
- **Memory efficiency**: Elimination of duplicate data

## Testing Strategy

### Coverage Results
- **Total tests**: 113 tests
- **Success rate**: 100%
- **Code coverage**: 94%

### Test Classification
1. **Unit tests**: Individual function verification for each model
2. **Validation tests**: Comprehensive testing of all validation functions
3. **Relationship tests**: Verification of inter-model interactions
4. **Integration tests**: EngagementState composite function tests

### Test File Structure
- `test_models_core.py`: 42 tests - Individual model functions
- `test_engagement_state.py`: 11 tests - EngagementState functions
- `test_relationships.py`: 6 tests - Inter-model relationships
- `test_validation_functions.py`: 54 tests - Validation functions

## Relationship Management

### Finding ↔ CollectedData Bidirectional Relationship
- `Finding.link_collected_data()`: Data association
- `CollectedData.add_derived_finding()`: Add derived finding
- Proper handling of circular references and consistency guarantee

### Host ↔ Service Relationship
- Automatic service integration (same port/protocol)
- Automatic host ID setting and consistency maintenance

## Quality Assurance

### Static Analysis
- **ruff**: Code style and linting
- **0 warnings**: Complete resolution of all warnings
- **datetime optimization**: Resolution of deprecation warnings with `datetime.now(UTC)`

### Pydantic v2 Support
- **ConfigDict**: Migration to latest configuration method
- **json_encoders removal**: Elimination of deprecated features
- **class Config removal**: Complete migration to v2 recommended method

## Future Extensibility

### Design Principles
- **SOLID principles**: Extensible design
- **Loose coupling**: Independence between modules
- **High cohesion**: Proper grouping of related functions

### Extension Points
- Addition of new finding categories
- Additional validation functions
- Support for custom data types
- Integration with persistence layer

## Summary

The wish-models package fully implements the specifications in docs/project/06-data-model.md and provides the following additional value:

- **100% type safety**: Prevention of runtime errors
- **Comprehensive validation**: Guarantee of data consistency
- **Efficient relationship management**: Automatic handling of complex dependencies
- **High test coverage**: Ensuring reliability
- **Latest technology support**: Utilization of Pydantic v2 and latest Python features

This serves as a robust foundation for the entire wish system.