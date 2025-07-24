# Live E2E Testing for wish

This directory contains real environment E2E tests that validate wish against actual targets like HTB (Hack The Box) machines.

## ⚠️ Important Safety Notice

These tests perform REAL network operations against REAL targets. Only run them:
- Against authorized targets (your own lab, HTB with active subscription, etc.)
- With proper VPN connection established
- Understanding the implications of the actions

## Prerequisites

1. **HTB VPN Access**
   - Active HTB VPN subscription
   - VPN configuration file (`HTB.ovpn`)

2. **Environment Setup**
   ```bash
   # Install OpenVPN
   sudo apt-get install openvpn
   
   # Connect to HTB VPN
   sudo openvpn --config HTB.ovpn --daemon
   ```

3. **API Keys**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

## Running Live Tests

### Quick Test (Verify Setup)
```bash
# Check if environment is ready
export WISH_E2E_LIVE=true
export HTB_VPN_CONNECTED=true
pytest e2e-tests/scenarios/test_htb_lame_live.py::test_live_environment_setup -v
```

### Run Specific Test Phase
```bash
# Discovery phase only
pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_discovery_phase -v

# Enumeration phase
pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_enumeration_phase -v

# Exploitation planning
pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_exploitation_planning -v
```

### Full Attack Chain Test (Black Hat USA Demo Simulation)
```bash
# This runs the complete attack chain
pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_full_attack_chain -v -s
```

## Test Structure

### test_htb_lame_live.py
Contains four main test functions:

1. **test_htb_lame_discovery_phase**
   - Sets target (10.10.10.3)
   - Performs comprehensive port scan
   - Verifies service discovery

2. **test_htb_lame_enumeration_phase**
   - Enumerates SMB services
   - Identifies Samba version
   - Discovers CVE-2007-2447 vulnerability

3. **test_htb_lame_exploitation_planning**
   - Creates exploitation plan
   - Tests safety mechanisms
   - Verifies dangerous command blocking

4. **test_htb_lame_full_attack_chain**
   - Complete Black Hat USA demo flow
   - Discovery → Analysis → Exploitation planning
   - ~15 minute full scenario

## Safety Features

### Allowed Targets
- HTB EU VPN: 10.10.10.0/24, 10.10.11.0/24
- HTB US VPN: 10.129.0.0/16

### Blocked Commands
- System destruction: `rm -rf /`, `format`, `mkfs`
- System control: `shutdown`, `reboot`
- Fork bombs and other malicious patterns

### Allowed Tools
- Scanners: nmap, masscan, unicornscan
- Web: nikto, gobuster, dirb, wfuzz
- SMB: enum4linux, smbclient, rpcclient
- Exploitation: Limited to reconnaissance and planning

## Debugging

### Enable Detailed Logging
```bash
# Set log level
export PYTEST_LOG_LEVEL=DEBUG

# Run with output
pytest e2e-tests/scenarios/test_htb_lame_live.py -v -s --log-cli-level=INFO
```

### Common Issues

1. **VPN Not Connected**
   ```
   Error: Cannot reach target 10.10.10.3
   Solution: Verify VPN connection with: ping 10.10.10.3
   ```

2. **OpenAI API Key Missing**
   ```
   Error: OpenAI API key not found
   Solution: export OPENAI_API_KEY="your-key"
   ```

3. **Test Skipped**
   ```
   SKIPPED: Live environment test disabled
   Solution: export WISH_E2E_LIVE=true
   ```

## CI/CD Integration

For GitHub Actions:
```yaml
- name: Run Live E2E Tests
  if: github.event_name == 'workflow_dispatch'
  env:
    WISH_E2E_LIVE: true
    HTB_VPN_CONNECTED: true
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
  run: |
    # Connect VPN (secure runner only)
    # Run tests
    pytest e2e-tests/scenarios/test_htb_lame_live.py
```

## Expected Output

Successful run shows:
```
=== Starting HTB Lame Full Attack Chain ===
--- Phase 1: Initial Contact ---
--- Phase 2: Service Discovery ---
Discovered ports: {21, 22, 139, 445}
--- Phase 3: Vulnerability Analysis ---
--- Phase 4: Targeted Enumeration ---
--- Phase 5: Vulnerability Identification ---
--- Phase 6: Exploitation Planning ---

=== Attack Chain Summary ===
Target: 10.10.10.3
Services: 4 discovered
Vulnerability: Samba username map script Command Injection
Severity: critical
Next Step: Ready for controlled exploitation

✓ Full attack chain completed successfully!
This confirms wish is ready for Black Hat USA demo!
```