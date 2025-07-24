# wish-models Design Decision Records

## Architecture Decision Records (ADR)

### ADR-001: Pydantic v2 Adoption Decision

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
Need for type safety and validation features for data models. Compared Python standard dataclasses with Pydantic v1/v2.

**Decision:**
Adopt Pydantic v2.

**Rationale:**
- **Powerful validation**: Declarative description of complex validation logic
- **Type safety**: Runtime type checking and automatic conversion
- **Serialization**: Automated JSON/dict conversion
- **v2 performance improvements**: Significant performance gains compared to v1
- **Ecosystem**: Integration with FastAPI and others

**Outcome:**
- Significant improvement in implementation efficiency
- Prevention of runtime errors
- However, warning handling was required during v2 migration (later fully resolved)

### ADR-002: Forward Reference Resolution Method

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
Circular references occur between EngagementState ↔ Host ↔ Service, etc. Need to resolve Python's forward reference constraints.

**Decision:**
Adopt lazy resolution using TYPE_CHECKING guard and model_rebuild().

**Implementation:**
```python
# Within module
if TYPE_CHECKING:
    from .other_module import OtherModel

# Resolution in __init__.py
Host.model_rebuild()
Service.model_rebuild()
```

**Rationale:**
- **Type checking**: Editors and mypy correctly recognize types
- **Runtime**: Avoid circular imports
- **Pydantic v2 compatible**: Recommended resolution method

**Outcome:**
- Properly resolved all circular references
- Implementation without compromising type safety
- Full utilization of IDE support

### ADR-003: Fail-Fast Error Handling

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
Determine error handling policy following fail-fast principle in CLAUDE.md.

**Decision:**
Immediately fail with exceptions for programming errors, handle only user environment factors with logging.

**Implementation example:**
```python
# Programming error → immediate exception
def validate_port(port: int) -> ValidationResult[int]:
    if not isinstance(port, int):
        return ValidationResult.error(["Port must be an integer"])
    # Immediate error on range check
    if port < 1 or port > 65535:
        return ValidationResult.error([f"Port {port} is out of valid range"])

# Fail-fast with ValidationError on validation failure
result.raise_if_invalid()
```

**Rationale:**
- **Early detection**: Early identification of problems
- **Debugging efficiency**: Clear failure location
- **Avoid recovery**: Prevent continued operation in uncertain states

**Outcome:**
- Early bug detection and fixes
- Prevention of unexpected behavior
- Improved development efficiency

### ADR-004: Validation Design

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
Determine unified implementation method for complex validation logic.

**Decision:**
Unified management of results and errors using ValidationResult[T] pattern.

**Implementation pattern:**
```python
class ValidationResult(Generic[T]):
    def __init__(self, data: T | None = None, errors: list[str] | None = None):
        self.data = data
        self.errors = errors or []
        self.is_valid = len(self.errors) == 0
    
    def raise_if_invalid(self) -> T:
        if not self.is_valid:
            raise ValidationError(self.errors)
        return self.data
```

**Rationale:**
- **Uniformity**: Common interface for all validation functions
- **Error information**: Provide detailed error content
- **Type safety**: Type guarantee of return values using Generic
- **Flexibility**: Support both error accumulation and batch processing

**Outcome:**
- Consistent error handling
- Provision of detailed error information
- Type-safe validation processing

### ADR-005: Relationship Management

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
Determine implementation method for bidirectional relationships between Finding ↔ CollectedData.

**Decision:**
Both models maintain ID lists referencing each other, managed by explicit association methods.

**Implementation:**
```python
# Finding side
related_collected_data_ids: list[str] = Field(default_factory=list)

def link_collected_data(self, data_id: str) -> None:
    if data_id not in self.related_collected_data_ids:
        self.related_collected_data_ids.append(data_id)

# CollectedData side  
derived_finding_ids: list[str] = Field(default_factory=list)

def add_derived_finding(self, finding_id: str) -> None:
    if finding_id not in self.derived_finding_ids:
        self.derived_finding_ids.append(finding_id)
```

**Rationale:**
- **Bidirectionality**: Relationship tracking from both directions
- **Consistency**: Duplicate prevention and data consistency
- **Flexibility**: Support for N:M relationships
- **Persistence support**: ID-based serialization support

**Outcome:**
- Efficient management of complex relationships
- Data consistency guarantee
- Future persistence layer support

### ADR-006: datetime Optimization

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
`datetime.utcnow()` deprecated in Python 3.12+, causing numerous warnings.

**Decision:**
Full migration to latest recommended method using `datetime.now(UTC)`.

**Migration:**
```python
# Old method
from datetime import datetime
created_at = Field(default_factory=datetime.utcnow)

# New method  
from datetime import datetime, UTC
created_at = Field(default_factory=lambda: datetime.now(UTC))
```

**Rationale:**
- **Future-proofing**: Support for latest Python versions
- **Warning removal**: Improved developer experience
- **Explicitness**: Clear timezone specification

**Outcome:**
- Complete removal of 395 warnings
- Compliance with latest Python recommendations
- Significant improvement in developer experience

### ADR-007: Pydantic v2 Config Optimization

**Date**: 2025-07-15  
**Status**: Adopted  

**Context:**
`class Config` and `json_encoders` deprecated in Pydantic v2, causing warnings.

**Decision:**
Migration to latest configuration method using `ConfigDict()` and removal of unnecessary `json_encoders`.

**Migration:**
```python
# Old method
class Config:
    json_encoders = {datetime: lambda v: v.isoformat()}

# New method
model_config = ConfigDict()
```

**Rationale:**
- **v2 compatibility**: Pydantic latest version recommended method
- **Auto-handling**: Automatic datetime serialization
- **Warning removal**: Improved developer experience

**Outcome:**
- Full Pydantic v2 compatibility
- Complete removal of remaining warnings
- Utilization of automatic serialization features

## Technical Trade-offs

### 1. Type Safety vs Performance
**Choice**: Prioritize type safety  
**Rationale**: Given the importance of pentest data, runtime error prevention is top priority

### 2. Flexibility vs Simplicity  
**Choice**: Maintain moderate flexibility  
**Rationale**: Support future feature expansion while avoiding excessive complexity

### 3. Memory Efficiency vs Functionality
**Choice**: Prioritize functionality  
**Rationale**: Memory constraints are limited in modern environments, focus on functionality and development efficiency

## Quality Policy

### Testing Strategy
- **100% success rate**: All tests must always pass
- **High coverage**: Maintain 90%+ code coverage
- **Boundary value testing**: Thorough testing of boundary values for each validation

### Code Quality
- **100% type hints**: Type annotations on all methods and variables
- **0 warnings**: Complete resolution of all warnings
- **Static analysis passing**: Pass all ruff checks

### Documentation
- **Implementation specifications**: Detailed documentation of implementation
- **Design decision records**: Record all important decisions
- **Usage examples**: Provide practical sample code

## Future Challenges

### Short-term Challenges
- Performance testing implementation
- Integration test expansion
- Error message internationalization

### Long-term Challenges  
- Integration design with persistence layer
- Distributed system support
- Real-time synchronization features

## Summary

The design of the wish-models package is built on accumulated decisions that balance type safety, extensibility, and maintainability. In particular, the adoption of Pydantic v2 and thorough implementation of the fail-fast principle have achieved a robust and reliable data foundation.

All design decisions are optimized toward the goal of the overall success of the wish system, contributing to efficiency in future expansion and maintenance work.