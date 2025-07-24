# Live HTB Testing Infrastructure

## Overview

This document describes the infrastructure implementation for running E2E tests against live HTB (Hack The Box) environments.

## Implementation Details

### 1. pytest Marker Addition
- Added `live` marker to `pyproject.toml`
- Separates live environment tests from regular tests

### 2. Makefile Target Updates
- `make e2e`: Regular E2E tests (excludes live tests)
- `make e2e-live`: Dedicated for live environment tests (with confirmation prompt)
- `make e2e-live-check`: Environment check

### 3. HeadlessWish Extension
- Added `demo_mode` parameter (default: True)
- For live environment tests, use `demo_mode=False` to use actual APIs

### 4. Live Environment Test Files
- `e2e-tests/scenarios/test_htb_lame_live.py`
- Tests complete exploitation flow against HTB Lame (10.10.10.3)

## Usage

### Prerequisites
1. HTB VPN connection must be established
2. OpenAI API key must be configured
3. Access permissions to HTB Lame machine required

### Environment Variables
```bash
export OPENAI_API_KEY="your-api-key"
export WISH_E2E_LIVE=true
export HTB_VPN_CONNECTED=true
```

### Test Execution

#### Method 1: Using Makefile
```bash
# Run live environment tests (with confirmation prompt)
make e2e-live

# Environment check only
make e2e-live-check
```

#### Method 2: Using Demo Script
```bash
# Show confirmation screen
./e2e-tests/run_live_demo.sh

# Confirm and execute
./e2e-tests/run_live_demo.sh --confirm
```

#### Method 3: Using pytest Directly
```bash
# All live environment tests
WISH_E2E_LIVE=true HTB_VPN_CONNECTED=true uv run pytest -m live -v

# Specific test only
WISH_E2E_LIVE=true HTB_VPN_CONNECTED=true uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::test_live_environment_setup -v
```

## Test Contents

### 1. Environment Setup Test
- OpenAI API key verification
- HeadlessWish instance creation

### 2. HTB Lame Exploitation Test
- **Phase 1**: Target setup and scanning
- **Phase 2**: Service enumeration and vulnerability identification
- **Phase 3**: Exploit planning
- **Phase 4**: Complete attack chain

### 3. Output Format
- User input and system output displayed on stderr
- Progress indicators with `[▶]`, `[✔]`, `[ℹ]`, `[✗]` icons

## Security Considerations

1. **Prevent Execution in CI Environment**
   - Checks CI environment variables to prevent automatic execution
   
2. **Confirmation Prompt**
   - `make e2e-live` displays confirmation prompt
   
3. **Environment Variable Gates**
   - Both `WISH_E2E_LIVE` and `HTB_VPN_CONNECTED` required

## Troubleshooting

### When Tests are Skipped
1. Verify environment variables are set
2. Check HTB VPN connection is active
3. Confirm OpenAI API key is correct

### Connection Errors
1. Verify HTB VPN is connected: `ping 10.10.10.3`
2. Check firewall settings
3. Confirm HTB subscription is active

## Future Extensions

1. Support for other HTB machines
2. More detailed assertions
3. Performance testing
4. Simultaneous testing of multiple targets